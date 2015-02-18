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

use_impls = ['go']

# this must be the same as in ../ansible/group_vars/all
g_boot_public_key = '829bb728a1b38d2e3bb8288d750502f7dce2ee329aaebf48ddc54e0cfc8003b3068fe57e20277ba50e42826c4d2bfcb172699e108d9e90b3339f8b6589449faf'

docker_run_args = {}
docker_run_args['go'] = '-port=30000 -loglevel=5 -bootnodes=enode://{bootstrap_public_key}@{bootstrap_ip}:30303 -maxpeer={req_num_peers}'
docker_run_args['python'] = '--logging :debug --log_json 1 --remote {bootstrap_ip} --port 30303 ' \
                  '--mining {mining_cpu_percentage} --peers {req_num_peers} --address {coinbase}'
teees_args = '{elarch_ip} guid,{pubkey_hex}'

mining_cpu_percentage = 50
req_num_peers = 4

ansible_args = ['-u', 'ubuntu', '--private-key=../ansible/system-testing.pem', '-vv']


def mk_inventory_executable(inventory):
    fn = tempfile.mktemp(suffix='json.sh', prefix='tmp_inventory', dir=None)
    fh = open(fn, 'w')
    fh.write("#!/bin/sh\necho '%s'" % json.dumps(inventory))
    fh.close()
    os.chmod(fn, stat.S_IRWXU)
    return fn


def exec_playbook(inventory, playbook):
    fn = mk_inventory_executable(inventory)
    # replace for go with --tags=go or delete to address both
    impls = ','.join(use_impls)
    args = ['ansible-playbook', '../ansible/%s' % playbook, '-i', fn, '--tags=%s' % impls] + ansible_args
    print 'executing', ' '.join(args)
    result = subprocess.call(args)
    if result:
        print 'failed'
    else:
        print 'success'


def start_clients(clients=[]):
    """
    start all clients with a custom config (nodeid)
    """
    inventory = Inventory()
    clients = clients or list(inventory.clients)
    inventory.inventory['client_start_group'] = dict(children=clients, hosts=[])
    # print clients
    # quit()
    assert inventory.es
    assert inventory.boot
    for client in clients:
        assert client
        ext_id = str(client)
        pubkey = nodeid_tool.topub(ext_id)
        coinbase = nodeid_tool.coinbase(ext_id)
        d = dict(hosts=inventory.inventory[client], vars=dict())
        dra_go = docker_run_args['go'].format(bootstrap_public_key=g_boot_public_key, bootstrap_ip=inventory.boot,
                                     req_num_peers=req_num_peers)
        dra_python = docker_run_args['python'].format(bootstrap_ip=inventory.boot,
                                     mining_cpu_percentage=mining_cpu_percentage,
                                     req_num_peers=req_num_peers,
                                     coinbase=coinbase)
        d['vars']['docker_run_args'] = {} 
        d['vars']['docker_run_args']['go'] = dra_go
        d['vars']['docker_run_args']['python'] = dra_python
        d['vars']['docker_container_id'] = {}
        d['vars']['docker_container_id']['go'] = 'docker_go'
        d['vars']['docker_container_id']['python'] = 'docker_python'
        d['vars']['docker_tee_args'] = {}
        d['vars']['docker_tee_args']['go'] = teees_args.format(elarch_ip=inventory.es, pubkey_hex=pubkey)
        d['vars']['docker_tee_args']['python'] = teees_args.format(elarch_ip=inventory.es, pubkey_hex=pubkey)
        inventory.inventory[client] = d
    print json.dumps(inventory.inventory, indent=2)
    exec_playbook(inventory.inventory, playbook='client-start.yml')


def stop_clients(clients=[]):
    # create group in inventory
    inventory = Inventory()
    clients = clients or list(inventory.clients)
    inventory.inventory['client_stop_group'] = dict(children=clients, hosts=[])
    assert inventory.es
    assert inventory.boot
    for client in clients:
        assert client
        d = dict(hosts=inventory.inventory[client], vars=dict())
        d['vars']['docker_container_id'] = {}
        d['vars']['docker_container_id']['go'] = 'docker_go' 
        d['vars']['docker_container_id']['python'] = 'docker_python'
        inventory.inventory[client] = d
#    print json.dumps(inventory.inventory, indent=2)
    exec_playbook(inventory.inventory, playbook='client-stop.yml')


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    sys.argv = sys.argv[:1]  # ec2.py peeks into args, so delete passing-variables-on-the-command-line
    if 'start' in args:
          start_clients()
    #     start_clients([u'tag_Name_client-01'])
    elif 'stop' in args:
        stop_clients()
    else:
        print 'usage:%s start|stop' % sys.argv[0]
