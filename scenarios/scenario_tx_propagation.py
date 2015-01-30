import subprocess
from base import Inventory
import nodeid_tool
from clients import start_clients, stop_clients
from eshelper import consensus
import random
import time
import sys


max_time_to_reach_consensus = 10


def scenario():
    """
    starts one client
        let it mine some ether
    start all clients
    create tx client_0 > client_1
    send tx to one client

    check tx propagation time < X
    check consensus

    @return: bool(consensus of all nodes)
    """
    inventory = Inventory()
    clients = list(inventory.clients)

    # FIXME reset everything

    if True:
        # stop all clients
        stop_clients(clients=clients[1:])
        start_clients(clients=clients[:1])

        # mine a bit
        blocktime = 12
        time.sleep(blocktime * len(clients) * 1.5)

        # start other clients
        start_clients(clients=clients[1:])

    # create tx
    sender = clients[0]

    ext_id = str(sender)
#    pubkey = nodeid_tool.topub(ext_id)
    privkey = nodeid_tool.topriv(ext_id)
    sending_address = nodeid_tool.coinbase(ext_id)

    recipient = clients[1]
    receiving_address = nodeid_tool.coinbase(str(recipient))

    rpc_host = inventory.inventory[sender][0]
    rpc_port = str(30203)
    value = str(100)

    # dump account
    sending_address = '6c386a4b26f73c802f34673f7248bb118f97424a'
    print 'sending address', sending_address

    args = ['pyethclient', '-H', rpc_host, '-p', rpc_port, 'getstate', sending_address]
    print 'executing', ' '.join(args)
    result = subprocess.call(args)
    if result:
        print 'failed'

    # pyethclient quicktx <to> <value> <data_hex> <pkey_hex>

    args = ['pyethclient', '-H', rpc_host, '-p', rpc_port]
    args += ['quicktx', receiving_address, value, '', privkey]
    print 'executing', ' '.join(args)
    result = subprocess.call(args)
    if result:
        print 'failed'

    time.sleep(max_time_to_reach_consensus)
    num_agreeing_clients = consensus(offset=max_time_to_reach_consensus)
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients, len(clients))
    return num_agreeing_clients == len(clients)


if __name__ == '__main__':
    success = scenario()
    if not success:
        sys.exit(1)
