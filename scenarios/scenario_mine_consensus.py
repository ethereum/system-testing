import time
from elasticsearch_dsl import Search
import pytest
from base import Inventory
from clients import start_clients, stop_clients
import nodeid_tool
from elasticsearch_dsl import Search
from eshelper import client, pprint, F, log_scenario, check_connection, consensus, assert_mining


scenario_run_time_s = 100
impls = ['go']
# 0 is go bootstrap, 1 is cpp bootstrap
boot = 0

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


@pytest.fixture(scope='module')
def clients():
    """py.test passes this fixture to every test function expecting an argument
    called ``clients``.
    """
    inventory = Inventory()
    return inventory.clients




def test_connections(clients):
    assert check_connection(minconnected=len(clients), minpeers=len(clients)-2)

def test_mining_started(clients):
    assert_mining(minmining=len(clients))

def test_consensus(clients):
    client_count = len(clients)
    assert check_connection(minconnected=client_count, minpeers=client_count-2)
    num_agreeing_clients = consensus()
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients,
                                                          client_count)
    assert num_agreeing_clients == client_count
