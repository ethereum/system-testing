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



# this must be the same as in ../ansible/group_vars/all
# fixme use node_id tool cli
g_boot0_public_key = '829bb728a1b38d2e3bb8288d750502f7dce2ee329aaebf48ddc54e0cfc8003b3068fe57e20277ba50e42826c4d2bfcb172699e108d9e90b3339f8b6589449faf'
g_boot1_public_key = 'tbd'

docker_run_args = {}
docker_run_args['go'] = (
    '--port=30000 '
    '--rpcaddr=0.0.0.0 '
    '--rpcport=20000 '
    '--logjson "-" --loglevel "5" '
    #    '--bootnodes=enode://{bootstrap_public_key}@{bootstrap_ip}:30303 '
    '--bootnodes=enode://6cdd090303f394a1cac34ecc9f7cda18127eafa2a3a06de39f6d920b0e583e062a7362097c7c65ee490a758b442acd5c80c6fce4b148c6a391e946b45131365b@54.169.166.226:30303 '
    '--maxpeers={req_num_peers} '
    '--nodekeyhex={privkey} '
    '--mine={mining_state} '
    '--etherbase primary '
    '--unlock primary '
    '--password /tmp/geth-password '
)
docker_run_args['cpp'] = (
    '--verbosity 9 '
    '--structured-logging '
    '--json-rpc-port 21000 '
    '--listen 31000 '
    '--upnp off '
    '--public-ip {client_ip} '
    '--remote 54.169.166.226 '
    '--peers {req_num_peers} {mining_state} '
)
docker_run_args['python'] = (
    '--logging :debug '
    '--log_json 1 '
    '--remote {bootstrap_ip} '
    '--port 30303 '
    '--mining {mining_state} '
    '--peers {req_num_peers} '
    '--address {coinbase} '
)
teees_args = '{elarch_ip} guid,{pubkey_hex}'

mining_cpu_percentage = 50




# add -vv for debug output
ansible_args = ['-u', 'ubuntu', '--private-key=../ansible/system-testing.pem']

def create_clients_config(inventory):
    clients_config = dict()
    
    for c, ip in inventory.clients.iteritems():
        clients_config[c] = dict() 
        for impl in ['go', 'cpp', 'python']:
            clients_config[c][impl] = dict()
            ext_id = str(c) + impl
            clients_config[c][impl]['pubkey'] = nodeid_tool.topub(ext_id)
            clients_config[c][impl]['privkey'] = nodeid_tool.topriv(ext_id)
            clients_config[c][impl]['coinbase'] = nodeid_tool.coinbase(ext_id)
    return clients_config

def create_guid_lookup_table(inventory, client_config):
    guid_lookup_table = dict()
    for c in client_config:
        for i in client_config[c]:
            guid = (client_config[c][i]['pubkey'])
            guid_lookup_table[guid] = { 'guid_short': guid[0:7] + '...', 'host': c, 'ip': inventory.clients[c], 'impl': i }
    return guid_lookup_table


clients_config = create_clients_config(Inventory())
guid_lookup_table = create_guid_lookup_table(Inventory(), clients_config)

def mk_inventory_executable(inventory):
    fn = tempfile.mktemp(suffix='json.sh', prefix='tmp_inventory', dir=None)
    fh = open(fn, 'w')
    fh.write("#!/bin/sh\necho '%s'" % json.dumps(inventory))
    fh.close()
    os.chmod(fn, stat.S_IRWXU)
    return fn


def exec_playbook(inventory, playbook, impls):
    fn = mk_inventory_executable(inventory)
    impls = ','.join(impls)
    args = ['ansible-playbook', '../ansible/%s' %
            playbook, '-i', fn, '--tags=%s' % impls] + ansible_args
    print 'executing', ' '.join(args)
    result = subprocess.call(args)
    if result:
        print 'failed'
    else:
        print 'success'

def get_boot_ip_pk(inventory, boot=0):
    d = dict(ip=inventory.boot0 if boot==0 else inventory.boot1, pk=g_boot0_public_key if boot==0 else g_boot1_public_key)
    return d

def start_clients(clients=[], req_num_peers=7, impls=['go'], boot=0, enable_mining=True):
    """
    start all clients with a custom config (nodeid)
    """
    inventory = Inventory()
    clients = clients or list(inventory.clients)
    inventory.inventory['client_start_group'] = dict(children=clients, hosts=[])
    # print clients
    # quit()
    bt = get_boot_ip_pk(inventory, boot)
    assert inventory.es
    assert inventory.boot0
    for client in clients:
        assert client

        d = dict(hosts=inventory.inventory[client], vars=dict())

        dra = {}
        dra['go'] = docker_run_args['go'].format(bootstrap_public_key=bt['pk'],
                                              bootstrap_ip=bt['ip'],
                                              req_num_peers=req_num_peers,
                                              privkey=clients_config[client]['go']['privkey'],
                                              mining_state=enable_mining
                                              )

        dra['cpp'] = docker_run_args['cpp'].format(bootstrap_ip=bt['ip'],
                                                      client_ip=inventory.instances[client],
                                                      req_num_peers=req_num_peers,
                                                      mining_state='--force-mining --mining on' if enable_mining else '')

        dra['python'] = docker_run_args['python'].format(bootstrap_ip=bt['ip'],
                                                      req_num_peers=req_num_peers,
                                                      coinbase=clients_config[client]['python']['coinbase'],
                                                      mining_state=mining_cpu_percentage if enable_mining else '0')
        
        d['vars']['target_client_impl'] = impls
        d['vars']['docker_run_args'] = {}
        d['vars']['docker_tee_args'] = {}

        for impl in ['go', 'cpp', 'python']:
            d['vars']['docker_run_args'][impl] = dra[impl]
            d['vars']['docker_tee_args'][impl] = teees_args.format(
            elarch_ip=inventory.es, pubkey_hex=clients_config[client][impl]['pubkey'])

        inventory.inventory[client] = d
        # print json.dumps(inventory.inventory, indent=2)
    exec_playbook(inventory.inventory, playbook='client-start.yml', impls=impls)


def stop_clients(clients=[], impls=['go'], boot=0):
    # create group in inventory
    inventory = Inventory()
    clients = clients or list(inventory.clients)
    inventory.inventory['client_stop_group'] = dict(children=clients, hosts=[])
    assert inventory.es
    assert inventory.boot0
    for client in clients:
        assert client
        d = dict(hosts=inventory.inventory[client], vars=dict())
        inventory.inventory[client] = d
        d['vars']['target_client_impl'] = impls
#    print json.dumps(inventory.inventory, indent=2)
    exec_playbook(inventory.inventory, playbook='client-stop.yml', impls=impls)



if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    # ec2.py peeks into args, so delete passing-variables-on-the-command-line
    sys.argv = sys.argv[:1]
   
    if 'start' in args:
        log_scenario(name='cmd_line', event='start_clients')
        start_clients()
        log_scenario(name='cmd_line', event='start_clients.done')
    elif 'starttest' in args:
        print clients_config[u'tag_Name_ST-host-00000']['go']
        start_clients([u'tag_Name_ST-host-00000'], impls=['go'], boot=0, enable_mining=True)
    elif 'stop' in args:
        log_scenario(name='cmd_line', event='stop_clients')
        stop_clients()
        log_scenario(name='cmd_line', event='stop_clients')
    elif 'stoptest' in args:
        stop_clients([u'tag_Name_ST-host-00000'], impls=['go'])
    else:
        print 'usage:%s start|stop' % sys.argv[0]
