import subprocess
from base import Inventory
import nodeid_tool
from clients import start_clients, stop_clients
from eshelper import tx_propagation, log_scenario
from rpc import coinbase, balance, transact
import time
import sys

max_time_to_reach_consensus = 10
impl=['go']

def Ox(x):
    return '0x' + x


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

    no_of_clients = len(clients)

    # FIXME reset everything
    log_scenario('tx_propagation', event='started')

    if True:
        # stop all clients
        #log_scenario('tx_propagation', event='stopping_clients')
        # stop_clients(clients=clients,impl=impl)
        # log_scenario('tx_propagation', event='stopping_clients.done')
        log_scenario('tx_propagation', event='starting_one_client')
        start_clients(clients=clients[:1],impl=impl)
        log_scenario('tx_propagation', event='starting_one_client.done')
        print 'mine a bit'
        blocktime = 12
        # intitial difficulty is very high, takes around 2 minutes for initial mined block
        delay = blocktime * 14
        log_scenario('tx_propagation', event='waiting', delay=delay)
        time.sleep(delay)

        # start other clients
        log_scenario('tx_propagation', event='starting_other_clients')
        start_clients(clients=clients[1:],impl=impl)
        log_scenario('tx_propagation', event='starting_other_clients.done')

        # create tx
        sender = clients[0]
        recipient = clients[1]

        rpc_host = inventory.inventory[sender][0]
        rpc_port = 20000  # hard coded FIXME if we get multiple clients per ec
        endpoint = 'http://%s:%d' % (rpc_host, rpc_port)

        sending_address = coinbase(endpoint)
        receiving_address = Ox(nodeid_tool.coinbase(str(recipient)))

        print 'sending addr %s, receiving addr %s' % (sending_address, receiving_address)
        
        value = 100
        # print balance(endpoint, sending_address)
        # this fails randomly, why ?
        assert value < balance(endpoint, sending_address)
        log_scenario('tx_propagation', event='sending_transaction',
                sender=sending_address, to=receiving_address, value=value)
        tx = transact(endpoint, sender=sending_address, to=receiving_address, value=value)
        log_scenario('tx_propagation', event='sending_transaction.done', result=tx)

        log_scenario('tx_propagation', event='waiting', delay=max_time_to_reach_consensus)
        time.sleep(max_time_to_reach_consensus)
        log_scenario('tx_propagation', event='waiting.done')

     
    num_agreeing_clients = tx_propagation(offset=max_time_to_reach_consensus * 2)
    print '%d out of %d clients received a tx' % (num_agreeing_clients, no_of_clients)
    
    # stop_clients(clients=clients, impl=impl)
    
    return num_agreeing_clients == no_of_clients 


if __name__ == '__main__':
    success = scenario()
    if not success:
        sys.exit(1)
