system-testing
==============

testing ethereum clients in dedicated networks

[more info in the wiki](https://github.com/ethereum/system-testing/wiki)


#Installing necessary software

tests are deployed via Ansible on Amazon EC2 instances.


Current install on Ubuntu:
```
sudo apt-get install libfreetype6-dev python-graphviz python python-pip python-virtualenv
git clone https://github.com/ethereum/system-testing.git
cd system-testing
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

```
AWS credentials are stored in ~/.boto

Usage: [wiki](https://github.com/ethereum/system-testing/wiki/How-to-run-a-test)
