system-testing
==============

planning is done in the [wiki](https://github.com/ethereum/system-testing/wiki)


#Installing necessary software

tests are deployed via Ansible on Amazon EC2 instances. 

 
Current install on Ubuntu:
```
sudo apt-get install python python-pip python-virtualenv
git clone https://github.com/ethereum/system-testing.git
cd system-testing
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

```
AWS credentials are stored in ~/.boto
