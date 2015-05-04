import time
import pytest
from elasticsearch_dsl import Search
from testing import nodeid_tool
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from logutils.eshelper import client, F, log_scenario, assert_started, assert_connected

# to how many peers should a connection be established
req_peer = 5
enable_mining = False
scenario_run_time_s = 45
impls = ['go']
boot = 'bootnode-go-0'
# if you want to evaluate client logs on the hosts, don't stop the clients
stop_clients_at_scenario_end = False

def log_event(event, **kwargs):
    log_scenario(name='p2p_connect', event=event, **kwargs)


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
    for client_ in clients:
        start_clients(clients=[client_], req_num_peers=req_peer, impls=impls, boot=boot, enable_mining=enable_mining)
        time.sleep(1)
    log_event('starting.clients.sequentially.done')

    print 'let it run for %d secs...' % scenario_run_time_s
    time.sleep(scenario_run_time_s)

    if stop_clients_at_scenario_end:
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


def test_started(clients):
    assert_started(len(clients))

def test_connections(clients):
    assert_connected(minconnected=len(clients), minpeers=len(clients))

    guids = [nodeid_tool.topub(ext_id.encode('utf-8')) for ext_id in clients]
    for guid in guids:
        s = Search(client)
        s = s.filter(F('term', at_message='p2p.connected'))
        s = s.filter(F('term', guid=guid))
        s = s.filter(F('term', remote_id=guid))
        response = s.execute()
        # pprint (response)
        assert response.hits.total == 0, 'a client is connected to itself'
    print 'PASS: no client is connected to itself'
