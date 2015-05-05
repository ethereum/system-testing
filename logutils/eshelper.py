from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl import F, Q
import time
import json
import datetime
from testing.clients import guid_lookup_table
from testing.testing import Inventory
from logstash_formatter import LogstashFormatter


# from base import Inventory
es_endpoint = '%s:9200' % Inventory().es
# es_endpoint = '54.152.5.133:9200'  # FIXME speedup hack
client = Elasticsearch(es_endpoint)

lsformatter = LogstashFormatter(defaults=dict())
es_index_name = 'logstash-%s' % datetime.datetime.utcnow().strftime('%Y.%m.%d')
es_doc_type = 'ethlog'


def pprint(x):
    print json.dumps(x.to_dict(), indent=2)

def ip_from_guid(guid):
    return guid_lookup_table[guid]['guid_short'] + ' @ ' + guid_lookup_table[guid]['ip'] + '/' + guid_lookup_table[guid]['impl']

def time_range_filter(field="timestamp", offset=60):
    start_time = datetime.datetime.utcfromtimestamp(
        time.time() - offset).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return F('range', **{field: {"gte": start_time, "lte": end_time}})

def log_scenario(name, event, **kargs):
    doc = dict(event='scenario.%s.%s' % (name, event))
    doc.update(kargs)
    print doc['event'], repr(kargs) if kargs else ''
    doc = lsformatter.format(doc)
    client.create(index=es_index_name, doc_type=es_doc_type, body=doc)


def assert_started(minstarted, offset=90):
    """Asserts that at least `minstarted` clients logged 'starting' event."""
    """
        "starting": {
            "comment": "one of the first log events, before any operation is started",
            "client_impl": "Impl/OS/version, e.g. Go/Linux/0.8.2",
            "eth_version": "int, e.g. 52",
            "ts": "YYYY-MM-DDTHH:MM:SS.SSSSSSZ"
        }
    """
    s = Search(client)
    s = s.filter(time_range_filter(field="json_message.starting.ts", offset=offset))
    s.aggs.bucket('by_host', 'terms', field='syslog_hostname.raw', size=0)
    response = s.execute()
    # pprint(response)

    print "passed for:"
    for tag in response.aggregations.by_host.buckets:
        print '  %s' % tag.key  # ip_from_guid(tag.key)

    num_started = len(response.aggregations.by_host.buckets)

    assert num_started >= minstarted, 'only %d (of %d) clients started' % (num_started, minstarted)
    for tag in response.aggregations.by_host.buckets:
        assert tag.doc_count == 1, 'client %s started more than once' % tag.key  # ip_from_guid(tag.key)


def assert_connected(minconnected=2, minpeers=2, offset=90):
    """
    assert that at least `minconnected` clients are connected to at least `minpeers` other clients
    """
    s = Search(client)
    s = s.filter(time_range_filter(field="json_message.p2p.connected.ts", offset=offset))
    s.aggs.bucket('by_host', 'terms', field='syslog_hostname.raw', size=0)
    response = s.execute()
    # pprint(response)

    print "passed for: "
    for tag in response.aggregations.by_host.buckets:
        print '  %s, connections: %d' % (tag.key, tag.doc_count)  # ip_from_guid(tag.key)

    num_connected = len(response.aggregations.by_host.buckets)

    assert num_connected >= minconnected, 'only %d (of %d) clients connected to other nodes' % (num_connected,
                                                                                                minconnected)

    for tag in response.aggregations.by_host.buckets:
        num_connected = tag.doc_count
        assert num_connected >= minpeers, ('at least one client only connected to %d '
                                           '(of %d expected) other nodes"' % (num_connected, minpeers))

def consensus(offset=60):
    """
    check for 'eth.chain.new_head' messages
    and return the max number of clients, that had the same head
    during the last `offset` seconds.
    """
    s = Search(client)
    # s = s.query(Q('match', message='eth.chain.new_head'))
    s = s.filter('exists', field='json_message.eth.chain.new_head.block_number')
    s = s.sort({'json_message.eth.chain.new_head.ts': {'order': 'desc', 'ignore_unmapped': 'true'}})
    response = s.execute()

    # Get latest block number
    x = max(hit['_source']['json_message']['eth.chain.new_head']['block_number'] for hit in response.hits.hits)

    # By default, the buckets are ordered by their doc_count descending
    # s.aggs.bucket('by_block_hash', 'terms', field='json_message.eth.chain.new_head.block_hash', size=3)

    # Reach consensus around latest block number
    s = Search(client)
    s = s.filter(time_range_filter(field="json_message.eth.chain.new_head.ts", offset=offset))
    s.aggs.bucket('latest', 'range',
                  field='json_message.eth.chain.new_head.block_number',
                  ranges=[{"from": x - 1, "to": x + 1}]).bucket(
                      'by_block_hash', 'terms',
                      field='json_message.eth.chain.new_head.block_hash',
                      size=3)
    # s = s[10:10]
    response = s.execute()
    # pprint(response)

    if response:
        return max(tag.doc_count for tag in response.aggregations.latest.buckets[0].by_block_hash.buckets)
    else:
        return 0


def assert_consensus(offset=10):
    """
    check for 'eth.chain.new_head' messages
    and return the max number of clients, that had the same head
    during the last `offset` seconds.
    """
    s = Search(client)
    s = s.query(Q("match", message='eth.chain.new_head'))
    # s = s.filter(time_range_filter(offset=offset))
    # By default, the buckets are ordered by their doc_count descending
    s.aggs.bucket('by_block_hash', 'terms', field='@fields.block_hash', size=0)
    # s = s[10:10]
    response = s.execute()
    pprint(response)
    if response:
        return max(tag.doc_count for tag in response.aggregations.by_block_hash.buckets)
    else:
        return 0

def consensus2():
    """
    measure block propagation time (including adding to the chain)
        median
        max
    """


def assert_mining(minmining):
    """
    assert that at least `minmining` clients have started mining and mined a block
    """
    s = Search(client)
    s = s.filter(F('term', message='eth.miner.new_block'))
    s.aggs.bucket('by_host', 'terms', field='syslog_hostname.raw', size=0)
    response = s.execute()
    # pprint(response)

    print "passed for: "
    for tag in response.aggregations.by_host.buckets:
        print '  %s, blocks mined: %d' % (tag.key, tag.doc_count)  # ip_from_guid(tag.key)

    num_mining = len(response.aggregations.by_host.buckets)
    assert num_mining >= minmining, 'only %d clients mining, expexted at least %d' % (num_mining, minmining)


def messages():
    s = Search(client)
    s = s.filter(time_range_filter(offset=6000))
    s.aggs.bucket('by_message', 'terms', field='message', size=100)
    # s = s[0:1000]
    response = s.execute()
    for tag in response.aggregations.by_message.buckets:
        print(tag.key, tag.doc_count)
    return response


def network():
    """
    get all handhakes and disconnects

    map network

    'chain.api.received status', remote_id=peer, genesis_hash=genesis_hash.encode('hex'))
    'p2p.sending disconnect', remote_id=self, readon=reason)
    'p2p.received disconnect', remote_id=self, reason=None)
    """
    s = Search(client)
    q_status = Q("match", message='chain.api.received_status')
    q_send_disconnect = Q("match", message='p2p.sending_disconnect')
#    q_recv_disconnect = Q("match", at_message='p2p.sending_disconnect')
    s = s.query(q_status | q_send_disconnect)
    # s = s[0:1000]
    response = s.execute()
    for hit in response:
        print hit
    return response


def tx_list(offset=10):
    """
    check for 'eth.tx.tx_new' messages
    and return the max number of clients, that had the same tx
    during the last `offset` seconds.

    """
    s = Search(client)
    s = s.query(Q("match", message='eth.tx.received'))
    s = s.filter(time_range_filter(offset=offset))
    s = s[0:100]
    response = s.execute()
    for hit in response.hits:
        print hit.to_dict()
    return response


def tx_propagation(offset=10):
    """
    check for 'eth.tx.tx_new' messages
    and return the max number of clients, that had the same tx
    during the last `offset` seconds.

    """
    s = Search(client)
    s = s.query(Q("match", message='eth.tx.received'))
    s = s.filter(time_range_filter(offset=offset))
    # By default, the buckets are ordered by their doc_count descending
    s.aggs.bucket('by_tx', 'terms', field='@fields.tx_hash', size=10)
    # s = s[0:1000]
    response = s.execute()
    if response:
        return max(tag.doc_count for tag in response.aggregations.by_tx.buckets)
    else:
        return 0

# response = tx_list(200)
# print tx_propagation(200)
