system-testing
==============

Testing ethereum clients in dedicated networks. More info in the [wiki](https://github.com/ethereum/system-testing/wiki).

Tests are deployed via `docker-machine` on Amazon EC2 instances.

### Installing necessary software

#### Using Docker

Add your AWS credentials in your local `~/.boto`, it will get mounted as a single-file volume inside the container.

##### Running with `docker`:
```
docker run -v ~/.boto:/root/.boto -it ethereum/system-testing
```

##### Running with `docker-compose` (`brew install docker-compose` or [official install docs](https://docs.docker.com/compose/install/)):
```
docker-compose run testing
```

#### Directly
```
apt-get install libfreetype6-dev python-pygraphviz python python-dev python-pip python-virtualenv
git clone https://github.com/ethereum/system-testing.git
cd system-testing
virtualenv venv  # optional
source venv/bin/activate  # optional
pip install -e .
```

### Usage

Launch `testing` to run tests.

```
usage: testing [-h] [-v] [-c CPP_NODES] [--cpp-image CPP_IMAGE]
               [--cpp-boot CPP_BOOT] [-g GO_NODES] [--go-image GO_IMAGE]
               [--go-boot GO_BOOT] [-p PYTHON_NODES]
               [--python-image PYTHON_IMAGE] [--python-boot PYTHON_BOOT]
               [-e ELASTICSEARCH] [-i VPC] [-r REGION] [-z ZONE] [-d DEBUG]
               [-s [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} ...]]]
               [{ls,stop,rm,cleanup}] [parameters [parameters ...]]

positional arguments:
  {ls,stop,rm,cleanup}  Optional commands for maintenance
  parameters            Optional parameters

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -c CPP_NODES, --cpp CPP_NODES
                        Number of C++ nodes to launch (default: 1)
  --cpp-image CPP_IMAGE
                        Base C++ image to use (default: ethereum/client-cpp)
  --cpp-boot CPP_BOOT   Number of C++ bootnodes to launch (default: 0)
  -g GO_NODES, --go GO_NODES
                        Number of Go nodes to launch (default: 1)
  --go-image GO_IMAGE   Base Go image to use (default: ethereum/client-go)
  --go-boot GO_BOOT     Number of Go bootnodes to launch (default: 1)
  -p PYTHON_NODES, --python PYTHON_NODES
                        Number of Python nodes to launch (default: 1)
  --python-image PYTHON_IMAGE
                        Base PyEthApp image to use (default: ethereum/client-
                        python)
  --python-boot PYTHON_BOOT
                        Number of Python bootnodes to launch (default: 0)
  -e ELASTICSEARCH, --es ELASTICSEARCH
                        IP of the ElasticSearch node (default: None)
  -i VPC, --vpc-id VPC  AWS VPC ID (default: vpc-3fe30e5a)
  -r REGION, --region REGION
                        AWS Region (default: us-east-1)
  -z ZONE, --zone ZONE  AWS Zone (default: b)
  -d DEBUG, --debug DEBUG
                        Debug (default: False)
  -s [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} ...]], --scenarios [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} [{tx_propagation,chain_consensus,p2p_connect,mine_consensus} ...]]
                        Scenarios to test (default: all)
```

### Cleanup
```
testing cleanup
```

See related [wiki article](https://github.com/ethereum/system-testing/wiki/How-to-run-a-test)
