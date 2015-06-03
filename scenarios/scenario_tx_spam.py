import time
import pytest
import random
import concurrent.futures as futures
from testing import nodeid_tool
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from testing.rpc import coinbase, balance, transact
from logutils.eshelper import tx_propagation, log_scenario

min_consensus_ratio = 0.90
mined_blocks_target = 5
txs_per_client = 20
max_time_to_reach_consensus = 30
stop_clients_at_scenario_end = True
time_to_sync_on_testnet = 3600
offset = 30  # buffer value, consensus runtime gets added to this

# globals
successful = 0
total_txs_tried = 0

def log_event(event, show=True, **kwargs):
    log_scenario(name='tx_spam', event=event, show=show, **kwargs)

def client_tx(client, clients, inventory):
    len_clients = len(clients)

    sender = client
    recipient_delta = random.randint(0, len_clients - 1)

    # Find our own key
    key = 0
    for i, client_ in enumerate(clients):
        if client_ == client:
            key = i

    if recipient_delta == key:  # choose neighbor if randint chose itself
        recipient_delta += 1
    recipient = clients[recipient_delta]

    rpc_host = inventory.clients[sender]
    rpc_port = 8545  # hard coded FIXME if we get multiple clients per ec
    endpoint = 'http://%s:%d' % (rpc_host, rpc_port)

    sending_address = coinbase(endpoint)
    receiving_address = "0x%s" % nodeid_tool.coinbase(str(recipient))

    # print 'sending addr %s, receiving addr %s' % (sending_address, receiving_address)

    value = 100
    balance_ = balance(endpoint, sending_address)

    data = ""
    for i in xrange(0, 10000):
        data += "01"
    gas = 1000000

    total_value = value + gas * 10000000000000

    global successful
    global total_txs_tried
    for tx in xrange(1, txs_per_client):
        if total_value < balance_:
            total_txs_tried += 1
            balance_ -= value
            result = send_tx(endpoint, sending_address, receiving_address, value, gas, data)
            if result:
                successful += 1
            time.sleep(3)

def send_tx(endpoint, sending_address, receiving_address, value, gas, data):
    log_event('sending_transaction', show=False, sender=sending_address,
              to=receiving_address, value=value)
    tx = transact(endpoint, sender=sending_address, to=receiving_address, value=value, gas=gas, data=data)
    log_event('sending_transaction.done', show=False, result=tx)

    return tx


@pytest.fixture(scope='module', autouse=True)
def run(run_clients, on_testnet):
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

    fillnode = clients.pop()

    len_clients = len(clients)
    total_txs = txs_per_client * len_clients

    log_event('starting.clients')
    start_clients(clients=clients, enable_mining=not on_testnet, testnet=on_testnet)
    log_event('starting.clients.done')

    # Fill testnodes with ether
    log_event('filling.clients')
    filler_privkey = "c85ef7d79691fe79573b1a7064c19c1a9819ebdbd1faaab1a8ec92344438aaf4"
    start_clients(clients=[fillnode], enable_mining=False, privkey=filler_privkey, testnet=on_testnet)
    if on_testnet:
        time.sleep(time_to_sync_on_testnet)
    else:
        time.sleep(15)
    rpc_host = inventory.clients[fillnode]
    rpc_port = 8545  # hard coded FIXME if we get multiple clients per ec
    endpoint = 'http://%s:%d' % (rpc_host, rpc_port)
    sender = "0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826"
    fill_successful = 0
    for client in clients:
        to = "0x%s" % nodeid_tool.coinbase(str(client))
        tx = transact(endpoint, sender=sender, to=to, value=100000000000000000000)
        if tx:
            fill_successful += 1
        time.sleep(3)
    log_event('filling.result', successful=fill_successful, total_txs_tried=len_clients)
    time.sleep(max_time_to_reach_consensus)

    start = time.time()

    # Client futures with tx loop
    with futures.ThreadPoolExecutor(max_workers=len_clients) as executor:
        future_to_client = dict((executor.submit(client_tx,
                                                 client,
                                                 clients,
                                                 inventory), client)
                                for client in clients)

    for future in futures.as_completed(future_to_client, 300):
        client = future_to_client[future]
        if future.exception() is not None:
            print '%s generated an exception: %r' % (client, future.exception())

    log_event('txs_result', successful=successful, total_txs_tried=total_txs_tried, max_total_txs=total_txs)

    log_event('waiting', delay=max_time_to_reach_consensus)
    time.sleep(max_time_to_reach_consensus)
    log_event('waiting.done')

    if stop_clients_at_scenario_end:
        log_event('stopping_clients')
        stop_clients(clients=clients)
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
    """Check that all clients have received transactions."""
    num_agreeing_clients = tx_propagation(client_count, offset=offset)
    assert num_agreeing_clients >= int(client_count * min_consensus_ratio), (
        'only %d (of %d) clients received a transaction' % (num_agreeing_clients, client_count))
    print 'PASS: %d (of %d) clients received a transaction' % (num_agreeing_clients, client_count)
