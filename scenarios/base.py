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
    args += [ "%s" % host, cmd]
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

    docker_pyeth_image_name = 'sveneh/pyethereum-develop'

    def __init__(self):
        self.cluster = Cluster()

    def client_num_to_name(num):
        return 'client-%0.2d' % (num+1)  # FIXME 100 limit and start at zero

    def client_num_to_host(num):
        return self.cluster.clients[self.client_num_to_name(num)]

    def start_client(num):
        name = self.client_num_to_name(num)
        host = self.client_num_to_host(num)
        cmd = 'docker run '
        """

        docker run --name=client-01 -d sveneh/pyethereum-develop -d data2
        docker logs --follow=true cf7eddc9656b982d82145e809d5152555a21cccb3aeaa599cfe97cb911bb8ddd
        docker stop cf7eddc9656b982d82145e809d5152555a21cccb3aeaa599cfe97cb911bb8ddd
        docker ps
        docker images

        Q: werden die daten im container gespeichert?
        """



    def run(self):
        self.start_client(0)
        time.sleep(100)
        self.stop_client(0)




if __name__ == '__main__':
    cluster = Cluster()
    print 1
    print rrun(cluster.clients['client-03'], 'docker ps')
    print 2
    #print ansible_run('tag_Name_client-02', 'command', 'docker ps')
    print 'bootstrapping', cluster.boot
    print 'elasticsearch', cluster.es
    print 'clients', cluster.clients
    print 'roles', cluster.roles



"""
---
- name: Start ethereum python client
  docker:
      image:    sveneh/pyethereum-develop
      expose:   30303
      ports:    30303:30303

      # parameters given to client
      command: --logging :debug --log_json 1 --remote {{ bootstrap_ip }} --port 30303 --mining {{ mining_cpu_percentage }} --peers {{ req_num_peers }}

- name: Get the docker container id
  # ansible docker module does not support this, therefore shell
  shell:    docker ps --latest=true --quiet=true
  register: docker_id

- name: Log docker output to elarch
  # fire and forget, don't wait to finish, run for one day
  async: 86400
  poll: 0
  # again, ansible docker module does not support logs
  # pyethereum wrongly logs to stderr
  shell: docker logs --follow=true {{ docker_id.stdout }} 2>&1 | {{ repo_path }}/logging/teees.py {{ elarch_ip }}
roles/clients/tasks/startup-client.yml (END)


ansible 54.67.82.196  -a 'docker stop ef97db676533'

ansible tag_Role_client -a 'docker ps'


 ansible tag_Role_client -m setup
"""
