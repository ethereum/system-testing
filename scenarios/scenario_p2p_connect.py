import time
from elasticsearch_dsl import Search
import pytest
from base import Inventory
from clients import start_clients, stop_clients
import nodeid_tool
from elasticsearch_dsl import Search
from eshelper import client, pprint, F, log_scenario, check_connection

min_peer_count = 2
max_peer = 5
scenario_run_time_s = 1 * 60
impls = ['cpp']
# 0 is go bootstrap, 1 is cpp bootstrap
boot = 1

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

    log_event('starting.clients')
    start_clients(clients=clients, maxnumpeer=min_peer_count, impls=impls, boot=boot)
    log_event('starting.clients.done')

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


def test_started(clients):
    """Check that all clients logged 'starting' event."""
    """
        "starting": {
            "comment": "one of the first log events, before any operation is started",
            "client_impl": "Impl/OS/version, e.g. Go/Linux/0.8.2",
            "eth_version": "int, e.g. 52",
            "ts": "YYYY-MM-DDTHH:MM:SS.SSSSSSZ"
        }
    """
    s = Search(client)
    s = s.filter(F('term', at_message='starting'))
    s.aggs.bucket('by_guid', 'terms', field='guid', size=0)
    response = s.execute()
    # pprint(response)

    num_started = len(response.aggregations.by_guid.buckets)
    client_count = len(clients)

    assert num_started == client_count, 'only %d (of %d) clients '  \
           'started' % (num_started, client_count)
    print 'PASS: all clients started logging'
    for tag in response.aggregations.by_guid.buckets:
        # print(tag.key, tag.doc_count)
        assert tag.doc_count == 1, 'some clients started more than once'
    print 'PASS: all clients started just once'


def test_connections(clients):
    assert check_connection(minconnected=len(clients), minpeers=len(clients)-1)
    
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
