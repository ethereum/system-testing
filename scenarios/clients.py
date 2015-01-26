"""
random notes:
ansible --overwrite
http://docs.ansible.com/developing_inventory.html
http://docs.ansible.com/playbooks_variables.html#passing-variables-on-the-command-line
"""
from base import Inventory
import nodeid_tool
import json
import subprocess
import tempfile
import stat
import os

key_file = '../ansible/system-testing.pem'

docker_run_args = '--logging :debug --log_json 1 --remote {bootstrap_ip} --port 30303 ' \
                  '--mining {mining_cpu_percentage} --peers {req_num_peers}'
teees_args = '{elarch_ip} guid,{pubkey_hex}'

mining_cpu_percentage = 50
req_num_peers = 4

ansible_args = ['-u', 'ubuntu', '--private-key=../ansible/system-testing.pem']


def inventory_executable(inventory):
    fn = tempfile.mktemp(suffix='json.sh', prefix='tmp_inventory', dir=None)
    fh = open(fn, 'w')
    fh.write("#!/bin/sh\necho '%s'" % json.dumps(inventory))
    fh.close()
    os.chmod(fn, stat.S_IRWXU)
    return fn


def exec_start_clients(inventory):
    fn = inventory_executable(inventory)
    print 'inventory executable:', fn
    args = ['ansible-playbook', '../ansible/client-start.yml', '-i', fn] + ansible_args
    
    # this will not work
    #args += ['--extra-vars="host_pattern=tag_Role_client"']
    # this will
    args += ['--extra-vars=host_pattern=tag_Role_client']

    # the following is just to verify that the command is working. Comment it out when you actually want to start clients
    args += ['--list-hosts']

    print 'executing', ' '.join(args)
    result = subprocess.call(args)
    if result:
        print 'failed'
    else:
        print 'success'


def start_clients():
    """
    start all clients with a custom config (nodeid)
    """
    inventory = Inventory()
    #inventory.inventory['_meta']['host_pattern'] = 'tag_Role_client'
    #inventory.inventory['host_pattern'] = 'tag_Role_client'
    for client in list(inventory.clients):
        assert client
        assert inventory.es
        assert inventory.boot
        ext_id = str(client)
        pubkey = nodeid_tool.topub(ext_id)
        d = dict(hosts=inventory.inventory[client], vars=dict())
        dra = docker_run_args.format(bootstrap_ip=inventory.boot,
                                     mining_cpu_percentage=mining_cpu_percentage,
                                     req_num_peers=req_num_peers)
        d['vars']['docker_run_args'] = dra
        d['vars']['docker_tee_args'] = teees_args.format(elarch_ip=inventory.es, pubkey_hex=pubkey)
        #d['host_pattern'] = client
        inventory.inventory[client] = d
    print json.dumps(inventory.inventory, indent=2)
    exec_start_clients(inventory.inventory)


def stop_clients(host_pattern):
    """
    # host_pattern to be defined on cmd_line like --extra-vars "host_pattern=tag_Role_client"
    """
    args = ['ansible-playbook', '../ansible/client-stop.yml', '-i', 'ec2.py',
            '--extra-vars',  '"host_pattern=%s"' % host_pattern] + ansible_args
    print 'executing', ' '.join(args)
    result = subprocess.call(args)
    if result:
        print 'failed'
    else:
        print 'success'


if __name__ == '__main__':
    # stop_clients(host_pattern='tag_Role_client')
    start_clients()


# print json.dumps(inventory.inventory, indent=4)

"""
1) inventory schreiben
2) ansible-pb -i invent client-run (clients starten)

loop:
  random wait
  docker stop random client (ansible-playbook --extra-args pattern=tag_name
  random wait
  random start stoped client
until tired

start analytics





"""
