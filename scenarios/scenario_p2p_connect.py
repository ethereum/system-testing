from base import Inventory
from clients import start_clients
import random
import time
import sys
import nodeid_tool

max_time_to_reach_consensus = 10
random.seed(42)
from elasticsearch_dsl import Search
from eshelper import client, pprint


def scenario():
    """
    starts all clients

    check: all clients logged 'starting' event

    @return: bool(consensous of all)
    """
    inventory = Inventory()
    clients = inventory.clients

    # start-up all clients
    start_clients(clients=clients)

    # let them agree on a block
    time.sleep(max_time_to_reach_consensus)

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
    s = s.filter('term', at_message='starting')
    s.aggs.bucket('by_guid', 'terms', field='guid', size=0)
    response = s.execute()
    pprint(response)

    num_started = len(response.aggregations.by_guid.buckets)
    num_started_expected = len(clients)

    # assert response.hits.total = num_started_expected

    if not num_started == num_started_expected:
        print 'FAIL: only %d (of %d) clients logged "starting"' % (num_started, num_started_expected)
        return False
    print 'PASS: correct clients started log events'
    for tag in response.aggregations.by_guid.buckets:
        # print(tag.key, tag.doc_count)
        if not tag.doc_count == 1:
            return False
    print 'PASS: all clients started just once'

    # check all connected
    """
        "p2p.connected": {
            "remote_version_string": "Impl/OS/version, e.g. Go/Linux/0.8.2",
            "comment": "as soon as a successful connetion to another node is established",
            "remote_addr": "ipv4:port, e.g. 10.46.56.35:30303",
            "remote_id": "hex128, e.g. 0123456789abcdef... exactly 128 digits",
            "num_connections": "int, e.g. 4 - number of other nodes this client is currently connected to",
            "ts": "YYYY-MM-DDTHH:MM:SS.SSSSSSZ"
        }
    """
    s = Search(client)
    s = s.filter('term', at_message='p2p.connected')
    s.aggs.bucket('by_guid', 'terms', field='guid', size=0)
    response = s.execute()
    if not len(response.aggregations.by_guid.buckets) == len(clients):
        return False
    for tag in response.aggregations.by_guid.buckets:
        # print(tag.key, tag.doc_count)
        if not tag.doc_count == len(clients) - 1:  # connect all but self
            return False

    guids = [nodeid_tool.topub(ext_id) for ext_id in clients]
    for guid in guids:
        s = Search(client)
        s = s.filter('term', at_message='p2p.connected')
        s = s.filter('term', guid=guid)
    s.aggs.bucket('by_remote_id', 'terms', field='remote_id', size=0)
    response = s.execute()

    if not len(response.aggregations.by_remote_id.buckets) == len(clients) - 1:
        return False

    return True

if __name__ == '__main__':
    success = scenario()
    if not success:
        sys.exit(1)
