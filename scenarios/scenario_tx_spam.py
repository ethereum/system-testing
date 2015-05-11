import time
import pytest
import random
import concurrent.futures as futures
from testing import nodeid_tool
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from testing.rpc import coinbase, balance, transact
from logutils.eshelper import tx_propagation, log_scenario

impls = ['go']  # enabled implementations, currently not being used
min_consensus_ratio = 0.90
txs_per_client = 100
max_time_to_reach_consensus = 15
stop_clients_at_scenario_end = True
offset = 30  # buffer value, consensus runtime gets added to this

def Ox(x):
    return '0x' + x

def log_event(event, **kwargs):
    log_scenario(name='tx_propagation', event=event, **kwargs)

def send_tx(endpoint, sending_address, receiving_address, value):
    log_event('sending_transaction', sender=sending_address,
              to=receiving_address, value=value)
    tx = transact(endpoint, sender=sending_address,
                  to=receiving_address, value=value)
    log_event('sending_transaction.done', result=tx)

    return tx


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
    len_clients = len(clients)

    log_event('starting.clients')
    start_clients(clients=clients, impls=impls)
    log_event('starting.clients.done')

    blocktime = 12
    # Initial difficulty is very high, takes around 2 minutes for a first block
    # to be mined on a single client. In this case we assume we're launching a
    # lot of them so we just try to let as many of them as possible mine a few
    # blocks
    delay = blocktime * len_clients * 3
    print 'mining for %ss' % delay
    log_event('waiting', delay=delay)
    time.sleep(delay)

    start = time.time()

    # create txs
    for i, client in enumerate(clients):
        sender = client
        recipient_delta = random.randint(0, len_clients - 1)
        if recipient_delta == i:  # choose neighbor if randint chose itself
            recipient_delta += 1
        recipient = clients[recipient_delta]

        rpc_host = inventory.clients[sender]
        rpc_port = 8545  # hard coded FIXME if we get multiple clients per ec
        endpoint = 'http://%s:%d' % (rpc_host, rpc_port)

        sending_address = coinbase(endpoint)
        receiving_address = Ox(nodeid_tool.coinbase(str(recipient)))

        # print 'sending addr %s, receiving addr %s' % (sending_address, receiving_address)

        value = 100
        # print balance(endpoint, sending_address)
        # this fails randomly, why ?
        balance_ = balance(endpoint, sending_address)

        txs = []
        for tx in xrange(1, txs_per_client):
            if value < balance_:
                balance_ -= value
                txs.append(tx)

        with futures.ThreadPoolExecutor(max_workers=txs_per_client) as executor:
            future_to_tx = dict((executor.submit(send_tx,
                                                 endpoint,
                                                 sending_address,
                                                 receiving_address,
                                                 value), tx)
                                for tx in txs)

        for future in futures.as_completed(future_to_tx, 300):
            tx = future_to_tx[future]
            if future.exception() is not None:
                print '%s generated an exception for tx #%s: %r' % (sender, tx, future.exception())
            # else:
            #     tx_result = future.result()
            #     print '%s #%s result: %s' % (sender, tx, tx_result['result'])

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
    num_agreeing_clients = tx_propagation(offset=offset)
    assert num_agreeing_clients >= int(client_count * min_consensus_ratio), (
        'only %d (of %d) clients received a transaction' % (num_agreeing_clients, client_count))
    print 'PASS: %d (of %d) clients received a transaction' % (num_agreeing_clients, client_count)
