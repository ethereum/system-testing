import time
import pytest
from base import Inventory
import nodeid_tool
from clients import start_clients, stop_clients
from eshelper import tx_propagation, log_scenario
from rpc import coinbase, balance, transact

max_time_to_reach_consensus = 10
impl=['go']

def Ox(x):
    return '0x' + x

def log_event(event, **kwargs):
    log_scenario(name='tx_propagation', event=event, **kwargs)



@pytest.fixture(scope='module', autouse=True)
def run(run_clients):
    """Run the clients.

    Because of ``autouse=True`` this method is executed before everything else
    in this module.

    The `run_clients` fixture is defined in ``conftest.py``. It is true by
    default but false if the --norun command line flag is set.
    """
    log_event('started')
    if not run_clients:
        return

    inventory = Inventory()
    clients = list(inventory.clients)

    # stop all clients
    # log_event('stopping_clients')
    # stop_clients(clients=clients,impl=impl)
    # log_event('stopping_clients.done')

    log_event('starting_one_client')
    start_clients(clients=clients[:1], impl=impl)
    log_event('starting_one_client.done')
    print 'mine a bit'
    blocktime = 12
    # intitial difficulty is very high, takes around 2 minutes for initial mined block
    delay = blocktime * 14
    log_event('waiting', delay=delay)
    time.sleep(delay)

    # start other clients
    log_event('starting_other_clients')
    start_clients(clients=clients[1:],impl=impl)
    log_event('starting_other_clients.done')

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
    log_event('sending_transaction', sender=sending_address,
              to=receiving_address, value=value)
    tx = transact(endpoint, sender=sending_address, to=receiving_address, value=value)
    log_event('sending_transaction.done', result=tx)

    log_event('waiting', delay=max_time_to_reach_consensus)
    time.sleep(max_time_to_reach_consensus)
    log_event('waiting.done')


@pytest.fixture(scope='module')
def client_count():
    """py.test passes this fixture to every test function expecting an argument
    called ``client_count``.
    """
    inventory = Inventory()
    return len(inventory.clients)


def test_propagation(client_count):
    """Check that all clients have received the transaction."""
    num_agreeing_clients = tx_propagation(offset=max_time_to_reach_consensus * 2)
    # stop_clients(clients=clients, impl=impl)
    assert num_agreeing_clients == client_count, 'only %d (of %d) clients '  \
           'received a transaction' % (num_agreeing_clients, client_count)
    print 'PASS: all %d clients received a transaction' % client_count
