"""
random notes:
ansible --overwrite
http://docs.ansible.com/developing_inventory.html
http://docs.ansible.com/playbooks_variables.html#passing-variables-on-the-command-line

docker_run_args = []

p2p_port = 30000 + N
rpc_port = 8000 + N
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
                  '--mining {mining_cpu_percentage} --peers {req_num_peers} --address {coinbase}'
teees_args = '{elarch_ip} guid,{pubkey_hex}'

mining_cpu_percentage = 50
req_num_peers = 4

ansible_args = ['-u', 'ubuntu', '--private-key=../ansible/system-testing.pem']


def mk_inventory_executable(inventory):
    fn = tempfile.mktemp(suffix='json.sh', prefix='tmp_inventory', dir=None)
    fh = open(fn, 'w')
    fh.write("#!/bin/sh\necho '%s'" % json.dumps(inventory))
    fh.close()
    os.chmod(fn, stat.S_IRWXU)
    return fn


def exec_playbook(inventory, playbook):
    fn = mk_inventory_executable(inventory)
    args = ['ansible-playbook', '../ansible/%s' % playbook, '-i', fn] + ansible_args
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
    assert inventory.es
    assert inventory.boot
    for client in clients:
        assert client
        ext_id = str(client)
        pubkey = nodeid_tool.topub(ext_id)
        coinbase = nodeid_tool.coinbase(ext_id)
        d = dict(hosts=inventory.inventory[client], vars=dict())
        dra = docker_run_args.format(bootstrap_ip=inventory.boot,
                                     mining_cpu_percentage=mining_cpu_percentage,
                                     req_num_peers=req_num_peers,
                                     coinbase=coinbase)
        d['vars']['docker_run_args'] = dra
        d['vars']['container_id'] = client
        d['vars']['docker_tee_args'] = teees_args.format(elarch_ip=inventory.es, pubkey_hex=pubkey)
        inventory.inventory[client] = d
#    print json.dumps(inventory.inventory, indent=2)
    exec_playbook(inventory.inventory, playbook='client-start.yml')


def stop_clients(clients=[]):
    # create group in inventory
    inventory = Inventory()
    clients = clients or list(inventory.clients)
    inventory.inventory['client_stop_group'] = dict(children=clients, hosts=[])
    exec_playbook(inventory.inventory, playbook='client-stop.yml')


if __name__ == '__main__':
    import sys
    if 'start' in sys.argv:
        start_clients()
    elif 'stop' in sys.argv:
        stop_clients()
    else:
        print 'usage:%s start|stop' % sys.argv[0]
