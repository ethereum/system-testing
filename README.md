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
(you might have to press <kbd>enter</kbd> once more to see the shell prompt)

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
pip install -r requirements.txt
```
AWS credentials are stored in ~/.boto

### Usage

See related [wiki article](https://github.com/ethereum/system-testing/wiki/How-to-run-a-test)
