Blockchain project
=====


###### This repository contains a (personal) project I worked on in October 2019, in order to better understand blockchains. The original structure is inspired by [Daniel van Flymen](https://github.com/dvf) in his article [Learn blockchains by Building one](https://medium.com/@vanflymen/learn-blockchains-by-building-one-117428612f46)


Installation and running
------

###### To process the blockchain, you will need Python 3.6 or any higher version, which should include the pip virtual library; as well as a Shell interpreter.

###### First, need to install the virtual environment pipenv, and the flask module:

###### `$ python -m pip install pipenv`
###### `$ python -m pip install flask`
###### `$ python -m pipenv install requests`

###### You can then proceed to run the blockchain (with as many nodes as they want):

###### `$python -m pipenv run python blockchain.py -p xxxx` (where `xxxx` is the port of the node you are instancing).

