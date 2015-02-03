from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q as _Q
from elasticsearch_dsl import F as _F
import time
import datetime
from base import Inventory


def at_kargs(kargs):
    return dict([(k.replace('at_', '@'), v) for k, v in kargs.items()])
Q = lambda *args, **kargs: _Q(*args, **at_kargs(kargs))
F = lambda *args, **kargs: _F(*args, **at_kargs(kargs))

# from base import Inventory
es_endpoint = '%s:9200' % Inventory().es
# es_endpoint = '54.153.13.89:9200'  # FIXME speedup hack
client = Elasticsearch(es_endpoint)


def time_range_filter(offset=60):
    start_time = datetime.datetime.utcfromtimestamp(
        time.time() - offset).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return F('range', at_timestamp=dict(gte=start_time, lte=end_time))


def consensus(offset=10):
    """
    check for 'eth.chain.new_head' messages
    and return the max number of clients, that had the same head
    during the last `offset` seconds.

    """
    s = Search(client)
    s = s.query(Q("match", at_message='eth.chain.new_head'))
    s = s.filter(time_range_filter(offset=offset))
    # By default, the buckets are ordered by their doc_count descending
    s.aggs.bucket('by_block_hash', 'terms', field='@fields.block_hash', size=10)
    #s = s[10:10]
    response = s.execute()
    print response
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


def messages():
    s = Search(client)
    s = s.filter(time_range_filter(offset=6000))
    s.aggs.bucket('by_message', 'terms', field='@message', size=100)
    #s = s[0:1000]
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
    q_status = Q("match", at_message='chain.api.received_status')
    q_send_disconnect = Q("match", at_message='p2p.sending_disconnect')
#    q_recv_disconnect = Q("match", at_message='p2p.sending_disconnect')
    s = s.query(q_status | q_send_disconnect)
    #s = s[0:1000]
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
    s = s.query(Q("match", at_message='eth.tx.tx_new'))
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
    s = s.query(Q("match", at_message='eth.tx.tx_new'))
    s = s.filter(time_range_filter(offset=offset))
    # By default, the buckets are ordered by their doc_count descending
    s.aggs.bucket('by_tx', 'terms', field='@fields.tx', size=10)
    #s = s[0:1000]
    response = s.execute()
    if response:
        return max(tag.doc_count for tag in response.aggregations.by_tx.buckets)
    else:
        return 0


# response = tx_list(200)
# print tx_propagation(200)
"""

todo:

delete data from clients and bootstrapping client

how to seperate logs for scenarios?
clean nodes after senarios?

plan:
    one index per scenario
    scenario_name-yyyy-mm-dd
    change alias to this index

"""
