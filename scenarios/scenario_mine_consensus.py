import time
import pytest
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from logutils.eshelper import log_scenario, consensus, assert_mining  # , assert_started, assert_connected

max_time_to_reach_consensus = 15
scenario_run_time_s = 100
impls = ['go']
boot = 'bootnode-go-0'

def log_event(event, **kwargs):
    log_scenario(name='mine', event=event, **kwargs)

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
        # don't run clients if --norun option is set
        return

    inventory = Inventory()
    clients = inventory.clients

    log_event('starting.clients.sequentially')
    for client in clients:
        start_clients(clients=[client], impls=impls, boot=boot, enable_mining=True)
        time.sleep(1)
    log_event('starting.clients.sequentially.done')

    print 'let it run for %d secs...' % scenario_run_time_s
    time.sleep(scenario_run_time_s)

    log_event('stopping_clients')
    stop_clients(clients=clients, impls=impls)
    log_event('stopping_clients.done')

    # start all clients without mining
    log_event('start_all_clients_again')
    start_clients(clients=clients, impls=impls, enable_mining=False)
    log_event('start_all_clients_again.done')

    # let them agree on a block
    log_event('wait_for_consensus')
    time.sleep(max_time_to_reach_consensus)
    log_event('wait_for_consensus.done')

    # stop all clients
    log_event('stop_all_clients')
    stop_clients(clients=clients, impls=impls)
    log_event('stop_all_clients.done')

@pytest.fixture(scope='module')
def clients():
    """py.test passes this fixture to every test function expecting an argument
    called ``clients``.
    """
    inventory = Inventory()
    return inventory.clients

# def test_startup(clients):
#     assert_started(minstarted=len(clients))

# def test_connections(clients):
#     assert_connected(minconnected=len(clients), minpeers=len(clients))

def test_mining_started(clients):
    assert_mining(minmining=len(clients), offset=scenario_run_time_s + 60)

def test_consensus(clients):
    client_count = len(clients)
    num_agreeing_clients = consensus()
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients,
                                                          client_count)
    assert num_agreeing_clients == client_count
