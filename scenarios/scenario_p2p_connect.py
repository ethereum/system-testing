from base import Inventory
from clients import start_clients, stop_clients
import time
import sys
import nodeid_tool
from elasticsearch_dsl import Search
from eshelper import client, pprint, F, log_scenario

min_peer_count = 4
maxpeer= 5
scenario_run_time_s = 1 * 60
impls = ['cpp']
# 0 is go bootstrap, 1 is cpp bootstrap
boot = 1

def execute(clients):
    log_scenario('p2p_connect', 'starting.clients')
    start_clients(clients=clients, maxnumpeer=min_peer_count, impls=impls, boot=boot)

    log_scenario('p2p_connect', 'starting.clients.done')
    print 'let it run for %d secs...' % scenario_run_time_s
    time.sleep(scenario_run_time_s)

    log_scenario('p2p_connect', 'stopping.clients')
    stop_clients(clients=clients, impls=impls)

    log_scenario('p2p_connect', 'stopping.clients.done')


def scenario():
    """
    starts all clients

    check: all clients logged 'starting' event

    @return: bool(consensous of all)
    """
    log_scenario(name='p2p_connect', event='started')

    inventory = Inventory()
    clients = inventory.clients

    execute(clients)

    # check all started
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
    num_started_expected = len(clients)

    if not num_started == num_started_expected:
        print 'FAIL: only %d (of %d) clients started' % (num_started, num_started_expected)
        return False
    print 'PASS: all clients started logging'
    for tag in response.aggregations.by_guid.buckets:
        # print(tag.key, tag.doc_count)
        if not tag.doc_count == 1:
            print 'FAIL: some clients started more than once'
            return False
    print 'PASS: all clients started just once'

    # check all connected
    s = Search(client)
    s = s.filter(F('term', at_message='p2p.connected'))
    s.aggs.bucket('by_guid', 'terms', field='guid', size=0)
    response = s.execute()

    num_connected = len(response.aggregations.by_guid.buckets)
    num_connected_expected = len(clients)

    if not num_connected == num_connected_expected:
        print 'FAIL: only %d (of %d) clients connected to other nodes' % \
            (num_connected, num_connected_expected)
        return False
    print 'PASS: all clients have at least one connection to another node'

    for tag in response.aggregations.by_guid.buckets:
        # print(tag.key, tag.doc_count)
        num_connected = tag.doc_count
        if not num_connected >= min_peer_count:
            print 'FAIL: one client only connected to %d (of %d) other nodes"' % \
                (num_connected, min_peer_count)
            return False
    print 'PASS: all clients are connected at least to %d other nodes' % min_peer_count

    guids = [nodeid_tool.topub(ext_id.encode('utf-8')) for ext_id in clients]
    for guid in guids:
        s = Search(client)
        s = s.filter(F('term', at_message='p2p.connected'))
        s = s.filter(F('term', guid=guid))
        s = s.filter(F('term', remote_id=guid))
        response = s.execute()
        # pprint (response)
        if not response.hits.total == 0:
            print 'FAIL: a client is connected to itself'
            return False
    print 'PASS: no client is connected to itself'
    return True

if __name__ == '__main__':
    success = scenario()
    if not success:
        sys.exit(1)
