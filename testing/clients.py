"""
Ethereum clients support
"""

from testing import Inventory
from tasks import set_logging, run_containers, stop_containers
from fabric.api import task
import nodeid_tool

set_logging(debug=False)

# Docker run options (daemonize, ports, volumes, entrypoint)
opts = {}
opts['cpp'] = ('-d '
               '-p 30303:30303 '
               '-p 30303:30303/udp '
               '-p 8080:8080 '
               '-v /opt/data:/opt/data '
               '-v /opt/dag:/root/.ethash '
               '--log-driver syslog '
               '--entrypoint eth')

opts['go'] = ('-d '
              '-p 30303:30303 '
              '-p 30303:30303/udp '
              '-p 8545:8545 '
              '-v /opt/data:/opt/data '
              '-v /opt/dag:/tmp/dag '
              '--log-driver syslog '
              '--entrypoint geth')

opts['python'] = ('-d '
                  '-p 30303:30303 '
                  '-p 30303:30303/udp '
                  '-p 4000:4000 '
                  '-v /opt/data:/opt/data '
                  '--log-driver syslog '
                  '--entrypoint pyethapp')

# Clients command line parameters
cmds = {}
cmds['cpp'] = (
    '--db-path /opt/data '
    '--verbosity 9 '
    '--structured-logging '
    '--json-rpc '
    '--upnp off '
    '--public-ip {client_ip} '
    '--remote {bootstrap_ip} '
    '--peers {req_num_peers} {mining_state} '
    '--session-secret {privkey}'
)
cmds['go'] = (
    '--datadir /opt/data '
    '--rpc '
    '--rpcaddr=0.0.0.0 '
    '--logjson "-" '
    '--loglevel "5" '
    '--bootnodes=enode://{bootstrap_public_key}@{bootstrap_ip}:30303 '
    '--maxpeers={req_num_peers} '
    '--nodekeyhex={privkey} '
    '--mine={mining_state} '
    '--etherbase primary '
    '--unlock primary '
    '--password /opt/data/password'
)
cmds['python'] = (
    '--bootstrap_node=enode://{bootstrap_public_key}@{bootstrap_ip}:30303 '
    '--log-json '
    '-c data_dir=/opt/data '
    '-c accounts.privkeys_hex=[{privkey}] '
    '-c p2p.min_peers={req_num_peers} '
    'run'
)

mining_percentage = 50

def create_clients_config(inventory):
    clients_config = dict()

    for nodename, ip in inventory.clients.items():
        clients_config[nodename] = dict()
        impl = nodename.split("-")[1]
        # for impl in ['go', 'cpp', 'python']:
        clients_config[nodename]['ip'] = ip
        clients_config[nodename]['impl'] = impl
        clients_config[nodename]['nodename'] = nodename
        clients_config[nodename]['pubkey'] = nodeid_tool.topub(nodename)
        clients_config[nodename]['privkey'] = nodeid_tool.topriv(nodename)
        clients_config[nodename]['coinbase'] = nodeid_tool.coinbase(nodename)
    return clients_config

def create_guid_lookup_table(inventory, client_config):
    guid_lookup_table = dict()
    for nodename in client_config:
        ip = client_config[nodename]['ip']
        impl = client_config[nodename]['impl']
        guid = client_config[nodename]['pubkey']
        host = client_config[nodename]['nodename']
        guid_lookup_table[guid] = {'guid_short': guid[0:7] + '...', 'host': host, 'ip': ip, 'impl': impl}
    return guid_lookup_table

inventory = Inventory()
clients_config = create_clients_config(inventory)
guid_lookup_table = create_guid_lookup_table(inventory, clients_config)

def get_boot_ip_pk(inventory, boot='bootnode-go-0'):
    d = dict(ip=inventory.bootnodes[boot],
             pk=nodeid_tool.topub(boot))
    return d

@task
def start_clients(clients=[], impls=[], images=None, req_num_peers=7, boot='bootnode-go-0', enable_mining=True):
    """
    Start all clients by IP with a custom config
    """
    inventory = Inventory()

    assert inventory.es
    assert inventory.bootnodes

    bootnode = get_boot_ip_pk(inventory, boot)

    if not clients:
        for nodename, ip in inventory.clients.items():
            clients.append(ip)

    options = {}
    commands = {}
    nodes = {'cpp': [], 'go': [], 'python': []}

    # Generate per nodename options and commands
    for nodename in clients:
        assert nodename

        impl = clients_config[nodename]['impl']

        if impl == 'go':
            commands[nodename] = cmds['go'].format(bootstrap_public_key=bootnode['pk'],
                                                   bootstrap_ip=bootnode['ip'],
                                                   req_num_peers=req_num_peers,
                                                   privkey=clients_config[nodename]['privkey'],
                                                   mining_state=enable_mining)
            options[nodename] = opts['go']
        elif impl == 'cpp':
            commands[nodename] = cmds['cpp'].format(bootstrap_ip=bootnode['ip'],
                                                    client_ip=clients_config[nodename]['ip'],
                                                    req_num_peers=req_num_peers,
                                                    privkey=clients_config[nodename]['privkey'],
                                                    mining_state='--force-mining '
                                                                 '--mining on' if enable_mining else '')
            options[nodename] = opts['cpp']
        elif impl == 'python':
            commands[nodename] = cmds['python'].format(bootstrap_public_key=bootnode['pk'],
                                                       bootstrap_ip=bootnode['ip'],
                                                       req_num_peers=req_num_peers,
                                                       privkey=clients_config[nodename]['privkey'],
                                                       # mining_state=mining_percentage if enable_mining else '0'
                                                       )
            options[nodename] = opts['python']
        else:
            raise ValueError("No implementation: %s" % impl)

        # Add nodename per implementation
        nodes[impl].append(nodename)

    # All nodes per implementation, with optional images, and all options and commands per nodename
    run_containers(nodes, images, options, commands)

@task
def stop_clients(clients=[], impls=[], boot=None):
    inventory = Inventory()
    nodenames = []
    if not clients:
        for nodename, ip in inventory.clients.items():
            nodenames.append(nodename)
    else:
        for nodename in clients:
            nodenames.append(nodename)

    if nodenames:
        stop_containers(nodenames)

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
