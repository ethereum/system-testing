system-testing
==============

Testing ethereum clients in dedicated networks. More info in the [wiki](https://github.com/ethereum/system-testing/wiki).

Tests are deployed via Ansible on Amazon EC2 instances.

### Installing necessary software

#### Using Docker

Add your AWS credentials in your local `~/.boto`, it will get mounted as a single-file volume inside the container.

##### Running with `docker-compose` (`brew install docker-compose` or [official install docs](https://docs.docker.com/compose/install/)):
```
docker-compose run testing
```

##### Running with `docker`:
```
docker run -v ~/.boto:/root/.boto -it ethereum/system-testing
```


#### Directly on Ubuntu
```
sudo apt-get install libfreetype6-dev python-pygraphviz python python-dev python-pip python-virtualenv
git clone https://github.com/ethereum/system-testing.git
cd system-testing
virtualenv venv
source venv/bin/activate
pip install -e .
```

### Usage

Launch `testing` to run tests.

```
usage: testing [-h] [-v] [-c CPP_NODES] [--cpp-image CPP_IMAGE] [-g GO_NODES]
               [--go-image GO_IMAGE] [-p PYTHON_NODES]
               [--python-image PYTHON_IMAGE] [-e ELASTICSEARCH] [-i VPC]
               [-r REGION] [-z ZONE] [-d DEBUG]
               [-s [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} ...]]]

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -c CPP_NODES, --cpp CPP_NODES
                        Number of C++ nodes to launch (default: 1)
  --cpp-image CPP_IMAGE
                        Base C++ image to use (default: ethereum/client-cpp)
  -g GO_NODES, --go GO_NODES
                        Number of Go nodes to launch (default: 1)
  --go-image GO_IMAGE   Base Go image to use (default: ethereum/client-go)
  -p PYTHON_NODES, --python PYTHON_NODES
                        Number of Python nodes to launch (default: 1)
  --python-image PYTHON_IMAGE
                        Base PyEthApp image to use (default: ethereum/client-
                        python)
  -e ELASTICSEARCH, --es ELASTICSEARCH
                        IP of the ElasticSearch node (default: 52.4.55.33)
  -i VPC, --vpc-id VPC  AWS VPC ID (default: vpc-3fe30e5a)
  -r REGION, --region REGION
                        AWS Region (default: us-east-1)
  -z ZONE, --zone ZONE  AWS Zone (default: b)
  -d DEBUG, --debug DEBUG
                        Debug (default: False)
  -s [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} ...]], --scenarios [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} ...]]
                        Scenarios to test (default: all)
```

See related [wiki article](https://github.com/ethereum/system-testing/wiki/How-to-run-a-test)
