"""
Ethereum clients support
"""

from testing import Inventory
from tasks import run_containers, stop_containers
from fabric.api import task
import nodeid_tool
# from logutils.eshelper import log_scenario  # dumbass circular import...

# Set options (daemonize and entrypoint)
options = {
    'cpp': '-d --entrypoint eth',
    'go': '-d --entrypoint geth',
    'python': '-d --entrypoint pyethapp',
}

client_cmds = {}
client_cmds['go'] = (
    '--port=30000 '
    '--rpcaddr=0.0.0.0 '
    '--rpcport=20000 '
    '--logjson "-" --loglevel "5" '
    '--bootnodes=enode://{bootstrap_public_key}@{bootstrap_ip}:30303 '
    '--maxpeers={req_num_peers} '
    '--nodekeyhex={privkey} '
    '--mine={mining_state} '
    '--etherbase primary '
    '--unlock primary '
    '--password /tmp/geth-password '
)
client_cmds['cpp'] = (
    '--verbosity 9 '
    '--structured-logging '
    '--json-rpc-port 21000 '
    '--listen 31000 '
    '--upnp off '
    '--public-ip {client_ip} '
    '--remote {bootstrap_ip} '
    '--peers {req_num_peers} {mining_state} '
)
client_cmds['python'] = (
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

def create_clients_config(inventory):
    clients_config = dict()

    for i, ip in enumerate(inventory.clients):
        clients_config[ip] = dict()
        for impl in ['go', 'cpp', 'python']:
            clients_config[ip][impl] = dict()
            ext_id = "testnode-%s-%s" % (impl, i)
            clients_config[ip][impl]['ext_id'] = ext_id
            clients_config[ip][impl]['pubkey'] = nodeid_tool.topub(ext_id)
            clients_config[ip][impl]['privkey'] = nodeid_tool.topriv(ext_id)
            clients_config[ip][impl]['coinbase'] = nodeid_tool.coinbase(ext_id)
    return clients_config

def create_guid_lookup_table(inventory, client_config):
    guid_lookup_table = dict()
    for ip in client_config:
        for impl in client_config[ip]:
            guid = client_config[ip][impl]['pubkey']
            host = client_config[ip][impl]['ext_id']
            guid_lookup_table[guid] = {'guid_short': guid[0:7] + '...', 'host': host, 'ip': ip, 'impl': impl}
    return guid_lookup_table

inventory = Inventory()
clients_config = create_clients_config(inventory)
guid_lookup_table = create_guid_lookup_table(inventory, clients_config)

def get_boot_ip_pk(inventory, boot=0):
    d = dict(ip=inventory.bootnodes[boot],
             pk=nodeid_tool.topub("bootnode-%s" % boot))
    return d

@task
def start_clients(clients=[], impls=[], images=None, req_num_peers=7, boot=0, enable_mining=True):
    """
    Start all clients with a custom config (nodeid)
    """
    inventory = Inventory()
    if not clients:
        for nodename, ip in inventory.instances:
            if nodename.startswith('testnode'):
                clients.append(nodename)

    bootnode = get_boot_ip_pk(inventory, boot)
    assert inventory.es
    assert inventory.bootnodes

    for client in clients:
        assert client

        commands = {}
        commands['go'] = client_cmds['go'].format(bootstrap_public_key=bootnode['pk'],
                                                  bootstrap_ip=bootnode['ip'],
                                                  req_num_peers=req_num_peers,
                                                  privkey=clients_config[client]['go']['privkey'],
                                                  mining_state=enable_mining)

        commands['cpp'] = client_cmds['cpp'].format(bootstrap_ip=bootnode['ip'],
                                                    client_ip=client,
                                                    req_num_peers=req_num_peers,
                                                    mining_state='--force-mining --mining on' if enable_mining else '')

        commands['python'] = client_cmds['python'].format(bootstrap_ip=bootnode['ip'],
                                                          req_num_peers=req_num_peers,
                                                          coinbase=clients_config[client]['python']['coinbase'],
                                                          mining_state=mining_cpu_percentage if enable_mining else '0')

        # TODO teees or logstash-forwarder
        # for impl in ['go', 'cpp', 'python']:
        #     d['vars']['docker_run_args'][impl] = cmds[impl]
        #     d['vars']['docker_tee_args'][impl] = teees_args.format(
        #         elarch_ip=inventory.es,
        #         pubkey_hex=clients_config[client][impl]['pubkey'])

    # Set options (daemonize and entrypoint)
    options = {
        'cpp': '-d --entrypoint eth',
        'go': '-d --entrypoint geth',
        'python': '-d --entrypoint pyethapp',
    }

    run_containers(clients, images, options, commands)

def stop_clients(clients=[], impls=[], boot=0):
    inventory = Inventory()
    if not clients:
        for nodename, ip in inventory.instances:
            if nodename.startswith('testnode'):
                clients.append(nodename)

    stop_containers(clients)

#
# # Circular import with log_scenario...
#
# if __name__ == '__main__':
#     import sys
#     args = sys.argv[1:]
#     # ec2.py peeks into args, so delete passing-variables-on-the-command-line
#     sys.argv = sys.argv[:1]

#     if 'start' in args:
#         log_scenario(name='cmd_line', event='start_clients')
#         start_clients()
#         log_scenario(name='cmd_line', event='start_clients.done')
#     elif 'starttest' in args:
#         print clients_config[u'testnode-go-0']['go']
#         start_clients([u'testnode-go-0'], boot=0, enable_mining=True)
#     elif 'stop' in args:
#         log_scenario(name='cmd_line', event='stop_clients')
#         stop_clients()
#         log_scenario(name='cmd_line', event='stop_clients')
#     elif 'stoptest' in args:
#         stop_clients([u'testnode-go-0'])
#     else:
#         print 'usage:%s start|stop' % sys.argv[0]
