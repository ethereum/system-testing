system-testing
==============

planning is done in the [wiki](https://github.com/ethereum/system-testing/wiki)


#Installing necessary software

tests are deployed via Ansible on Amazon EC2 instances. Installing Ansible via virtualenv yields conflicts with the boto library.

 
Current install on Ubuntu:
```
sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ansible python-boto

git clone https://github.com/ethereum/system-testing.git
```
AWS credentials are stored in ~/.boto
