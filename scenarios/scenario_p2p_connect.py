import time
import pytest
from elasticsearch_dsl import Search, F
from testing import nodeid_tool
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from logutils.eshelper import client, log_scenario, assert_started, assert_connected

impls = ['go']  # enabled implementations, currently not being used
req_peer = 5  # to how many peers should a connection be established
enable_mining = False
scenario_run_time = 60
stop_clients_at_scenario_end = True
offset = 30  # buffer value, total runtime gets added to this

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

    start = time.time()

    log_event('starting.clients')
    start_clients(clients=clients, req_num_peers=req_peer, impls=impls, enable_mining=enable_mining)
    log_event('starting.clients.done')

    print 'let it run for %d secs...' % scenario_run_time
    time.sleep(scenario_run_time)

    if stop_clients_at_scenario_end:
        log_event('stopping_clients')
        stop_clients(clients=clients, impls=impls)
        log_event('stopping_clients.done')

    global offset
    offset += time.time() - start
    print "Total offset: %ss" % offset

@pytest.fixture(scope='module')
def clients():
    """py.test passes this fixture to every test function expecting an argument
    called ``clients``.
    """
    inventory = Inventory()
    return inventory.clients


def test_started(clients):
    assert_started(len(clients), offset=offset)

def test_connections(clients):
    len_clients = len(clients)
    min_peers = len_clients if len_clients <= 3 else 3
    assert_connected(minconnected=len_clients, minpeers=min_peers, offset=offset)

    guids = [nodeid_tool.topub(ext_id.encode('utf-8')) for ext_id in clients]
    for guid in guids:
        s = Search(client)
        s = s.filter('exists', field='json_message.p2p.connected.ts')
        s = s.filter(F('term', guid=guid))
        s = s.filter(F('term', remote_id=guid))
        response = s.execute()
        # pprint (response)
        assert response.hits.total == 0, 'a client is connected to itself'
    print 'PASS: no client is connected to itself'
