#!/usr/bin/env python
"""
1. start playbooks to setup environment
    nodes
    elasticsearch
2. check prerequisites
3. load cluster config with ips
4. use rpc api / ansible to issue commands


"""
import elasticsearch
import ec2
from addict import Dict
from collections import OrderedDict



class Cluster(object):
    def __init__(self):
        inventory = ec2.inventory()
        self.instances = dict((k[len('tag_Name_'):],v[0])
                          for k,v in inventory.items()
                           if k.startswith('tag_Name_'))
        self.boot = self.instances.get('boot')
        self.es = self.instances.get('elarch')
        self.clients = OrderedDict(sorted((k, v) for k, v in
                                   self.instances.items() if k.startswith('client-')))
        self.roles = dict((k[len('tag_Role_'):],v)
                          for k,v in inventory.items()
                           if k.startswith('tag_Role_'))

class Scenario(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    cluster = Cluster()
    print cluster.boot
    print cluster.es
    print cluster.clients
    print cluster.roles


