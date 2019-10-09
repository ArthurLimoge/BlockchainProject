import hashlib
import json
from time import time
from flask import Flask, jsonify, request, session
# from flask_session import Session
from uuid import uuid4
from urllib.parse import urlparse


class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(100, 1)  # manually set the genesis block
        self.nodes = set()  # creates a public tuple of all the nodes' ids in the network
        self.p_nodes = set()  # creates a semi-private list of all the nodes in the network

    def create_block(self, new_proof, previous_hash=None):
        block = {
            'timestamp': time(),
            'index': len(self.chain) + 1,
            'transactions': self.transactions,
            'proof': new_proof,
            'previous_hash': previous_hash or self.hash(self.last_block)
        }

        self.transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1  # returns the index of the block it'll be added to

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        pre_hash = json.dumps(block, sort_keys=True).encode()  # orders the block string to make the hash consistent
        return hashlib.sha256(pre_hash).hexdigest()

    def proof_of_work(self, last_proof):
        new_proof = 0
        while self.valid_proof(new_proof, last_proof) is False:
            new_proof += 1
        return new_proof

    """"
    This static method to generate a new valid proof of work relies on a simplified version of the hashcash algorithm.
    For a new proof of work to be considered valid, we need its combined hash with the previous proof to start with
    a certain pre-determined number of zeros (in our case, say 4).
    """
    @staticmethod
    def valid_proof(new_proof, last_proof):
        combined_hash = hashlib.sha256(f'{new_proof}{last_proof}'.encode()).hexdigest()
        return combined_hash[:5] == "00000"

    def valid_chain(self, chain):
        length = len(chain)
        index = 1
        last_block = chain[0]

        """
        This function checks that the chain input is valid, via checking the proof-of-works and hashes are valid.
        """

        while index < length:
            block = chain.index

            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(block['proof'], last_block['proof']):
                return False

            last_block = block
            index += 1

            return True

    def resolve_chain(self):
        """
        Consensus algorithm: checks for longer (valid) chains in the network.
        """

        neighbours = self.nodes
        new_chain = None

        local_length = len(self.chain)

        for neighbour in neighbours:
            response = request.get(f'http://{neighbour}/chain')

            if response.status_code == 200:
                neighbour_chain = response.json()['chain']
                length = len(neighbour_chain)

                if length > local_length and self.valid_chain(chain):
                    local_length = length
                    new_chain = neighbour_chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def register_node(self, id_):
        new_node = Node(id_)
        node_netloc = new_node.return_id
        self.p_nodes.add(new_node)  # private tuple to be used in the program
        self.nodes.add(node_netloc)  # public tuple listing all the nodes' IDs
        return self.nodes


class Node:

    def __init__(self, id_):
        self.id_ = urlparse(id_).netloc
        self.wallet = 0

    @property
    def return_id(self):
        return self.id_

    @property
    def return_wallet(self):
        return self.wallet


node = Flask(__name__)  # create a node as a Flask instance
local_id = str(uuid4()).replace('-', '')  # generates an address for the node
local_netloc = urlparse(local_id).netloc

blockchain = Blockchain()


@node.route('/mine', methods=['GET'])  # mining endpoint
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    new_proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",  # transaction sent by the mint
        recipient=local_id,
        amount=1
    )

    response = blockchain.create_block(new_proof)
    response['Message'] = 'New block forged'
    return jsonify(response), 200


@node.route('/chain', methods=['GET'])  # returns the chain in json
def chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@node.route('/id', methods=['GET'])
def return_id():
    response = {'message': f'The local id is {local_id}'}
    return jsonify(response), 202


@node.route('/nodes/register', methods=['POST'])  # input has to be of the form {'nodes': list_of_nodes}
def register():
    values = request.get_json()
    addresses = values.get('addresses')

    if addresses is None:
        response = {'message': 'Please input address(es)'}

    else:

        for address in addresses:
            blockchain.register_node(address)

        response = {
            'message': 'New nodes have been added.',
            'node_list': list(blockchain.nodes)
        }

    return jsonify(response), 201


@node.route('/nodes/list', methods=['GET'])
def nodes_list():
    response = {'message': f'Registered nodes are {list(blockchain.nodes)}'}
    return jsonify(response), 202


@node.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    else:
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

        response = {'message': f'Transaction will be added to block {index}'}
        return jsonify(response), 201


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=4200, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    node.run(host='0.0.0.0', port=port)
