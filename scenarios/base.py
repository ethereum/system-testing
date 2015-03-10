#!/usr/bin/env python
"""
1. start playbooks to setup environment
    nodes
    elasticsearch
2. check prerequisites
3. load cluster config with ips
4. use rpc api / ansible to issue commands

ansible --private-key=../ansible/system-testing.pem -u ubuntu -i ec2.py tag_Name_client-01  -a ls
"""
import elasticsearch
import ec2
from addict import Dict
from collections import OrderedDict
import ansible.runner
import ansible.inventory
import sys


def ansible_run(pattern, module_name='command', module_args=''):
    # http://docs.ansible.com/docker_module.html
    inventory = ansible.inventory.Inventory('ec2.py')
    # construct the ansible runner and execute on all hosts
    results = ansible.runner.Runner(
        inventory=inventory,
        remote_user='ubuntu',
        private_key_file='../ansible/system-testing.pem',
        pattern=pattern,
        forks=10,
        module_name=module_name,
        module_args=module_args,
    ).run()

    # results = dict(contacted=[(hostname, res), ...], dark=[(hostname, res), ...])
    # res['stdout']
    return results


import subprocess
import sys


def rrun(host, cmd):
    args = ['-i', '../ansible/system-testing.pem', '-l', 'ubuntu']
    args += ["%s" % host, cmd]
    ssh = subprocess.Popen(["ssh"] + args,
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if not result:
        error = ssh.stderr.readlines()
    else:
        error = []
    return result, error


class Inventory(object):

    def __init__(self):
        inventory = self.inventory = ec2.inventory()
        self.instances = dict((k, v[0]) for k, v in inventory.items() if k.startswith('tag_Name_'))
        self.boot0 = self.instances['tag_Name_ST-boot-00000']
        self.boot1 = self.instances['tag_Name_ST-boot-00001']
        self.es = self.instances['tag_Name_ST-elarch']
        self.clients = OrderedDict(sorted((k, v) for k, v in self.instances.items()
                                          if k.startswith('tag_Name_ST-host-')))
        self.roles = dict((k, v) for k, v in inventory.items() if k.startswith('tag_Role_'))


class Scenario(object):

    docker_pyeth_image_name = 'sveneh/pyethereum-develop'

    def __init__(self):
        self.inventory = Inventory()

    def client_num_to_name(num):
        return 'host-%0.5d' % (num)  

    def client_num_to_host(num):
        return self.inventory.clients[self.client_num_to_name(num)]

    def start_client(num):
        name = self.client_num_to_name(num)
        host = self.client_num_to_host(num)
        cmd = 'docker run '
        """

        docker run --name=client-01 --name eth_client -d sveneh/pyethereum-develop -d data2
        docker logs --follow=true eth_client
        docker stop eth_client
        docker ps
        docker images

        Q: werden die daten im container gespeichert?
        """

    def run(self):
        self.start_client(0)
        time.sleep(100)
        self.stop_client(0)


if __name__ == '__main__':
    inventory = Inventory()
    # print rrun(inventory.clients['client-03'], 'docker ps')
    # print ansible_run('tag_Name_client-02', 'command', 'docker ps')
    print 'bootstrapping', inventory.boot0, inventory.boot1
    print 'elasticsearch', inventory.es
    print 'clients', inventory.clients
    print 'roles', inventory.roles
