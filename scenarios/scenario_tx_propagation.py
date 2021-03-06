import time
import pytest
from testing import nodeid_tool
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from testing.rpc import coinbase, balance, transact
from logutils.eshelper import tx_propagation, log_scenario

impls = ['go']  # enabled implementations, currently not being used
min_consensus_ratio = 0.90
max_time_to_reach_consensus = 15
stop_clients_at_scenario_end = True
offset = 30  # buffer value, consensus runtime gets added to this

def log_event(event, show=True, **kwargs):
    log_scenario(name='tx_propagation', event=event, show=show, **kwargs)

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

    log_event('starting_one_client')
    start_clients(clients=clients[:1], impls=impls)
    log_event('starting_one_client.done')
    print 'mine a bit'
    blocktime = 12
    # intitial difficulty is very high, takes around 2 minutes for initial mined block
    delay = blocktime * 14
    log_event('waiting', delay=delay)
    time.sleep(delay)

    # start other clients
    log_event('starting_other_clients')
    start_clients(clients=clients[1:], impls=impls)
    log_event('starting_other_clients.done')

    # create tx
    sender = clients[0]
    recipient = clients[1]

    rpc_host = inventory.clients[sender]
    rpc_port = 8545  # hard coded FIXME if we get multiple clients per ec
    endpoint = 'http://%s:%d' % (rpc_host, rpc_port)

    sending_address = coinbase(endpoint)
    receiving_address = "0x%s" % nodeid_tool.coinbase(str(recipient))

    print 'sending addr %s, receiving addr %s' % (sending_address, receiving_address)

    value = 100
    # print balance(endpoint, sending_address)
    # this fails randomly, why ?
    assert value < balance(endpoint, sending_address)

    start = time.time()

    log_event('sending_transaction', show=False, sender=sending_address,
              to=receiving_address, value=value)
    tx = transact(endpoint, sender=sending_address, to=receiving_address, value=value)
    log_event('sending_transaction.done', show=False, result=tx)

    log_event('waiting', delay=max_time_to_reach_consensus)
    time.sleep(max_time_to_reach_consensus)
    log_event('waiting.done')

    if stop_clients_at_scenario_end:
        log_event('stopping_clients')
        stop_clients(clients=clients, impls=impls)
        log_event('stopping_clients.done')

    global offset
    offset += time.time() - start
    print "Total offset: %s" % offset

@pytest.fixture(scope='module')
def client_count():
    """py.test passes this fixture to every test function expecting an argument
    called ``client_count``.
    """
    inventory = Inventory()
    return len(inventory.clients)

def test_propagation(client_count):
    """Check that all clients have received the transaction."""
    num_agreeing_clients = tx_propagation(client_count, offset=offset)
    assert num_agreeing_clients >= int(client_count * min_consensus_ratio), (
        'only %d (of %d) clients received a transaction' % (num_agreeing_clients, client_count))
    print 'PASS: %d (of %d) clients received a transaction' % (num_agreeing_clients, client_count)
