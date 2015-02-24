import json
from elasticsearch_dsl import Search
from elasticsearch_dsl import F as _F
from elasticsearch import Elasticsearch
from collections import OrderedDict

def at_kargs(kargs):
    return dict([(k.replace('at_', '@'), v) for k, v in kargs.items()])
F = lambda *args, **kargs: _F(*args, **at_kargs(kargs))

#  es_endpoint = '%s:9200' % Inventory().es
es_endpoint = '54.152.117.76:9200'  # FIXME speedup hack
client = Elasticsearch(es_endpoint)


def pprint(x):
    print json.dumps(x, indent=2)


def session_times():
    # {"@fields": {}, "@timestamp": "2015-02-23T17:03:41.738412Z", "@source_host": "newair.brainbot.com", "@message": "scenario.p2p_connect.started"}

    start_message = 'scenario.p2p_connect.starting.clients'
    stop_message = 'scenario.p2p_connect.stopping.clients'
    s = Search(client)
    s = s.filter('bool',
                 should=[F('term', at_message=start_message),
                         F('term', at_message=stop_message)])
    s = s.fields(['@message', '@timestamp'])
    s = s[0:100000]
    s = s.sort('-@timestamp')  # desc,  we want the latest events
    response = s.execute()

    events = [] # joungest to oldest, last should be a stop message
    for h in response:
        msg = 'start' if h['@message'][0] == start_message else 'stop'
        ts = h['@timestamp'][0]
        events.append((msg, ts))
    assert not events or events[0][0] == 'stop'
    sessions = []
    while len(events) >= 2:
        stop = events.pop()
        start = events.pop()
        sessions.append(dict([start, stop]))
    return sessions


def fetch(session):
    s = Search(client)
    s = s.filter('bool',
                 should=[F('term', at_message='p2p.disconnected'),
                         F('term', at_message='p2p.connected')])
    s = s.filter('range', **{'@timestamp': dict(gte=session['start'], lte=session['stop'])})
    s = s.fields(['@fields.remote_id', 'guid', '@message', '@timestamp'])
    s = s[0:100000]
    #s = s[0:10]
    s = s.sort('@timestamp')
    response = s.execute()
    return response


def analyze(r):
    graph = dict()  # from > list(remote)
    events = []
    for h in r.hits:
        node = h.guid[0]
        remote = h['@fields.remote_id'][0]
        message = h['@message'][0]
        # ts = h['@timestamp'][0]
        # print ts

        event = message.split('.')[1]
        events.append((event, node, remote))
    print 'num events', len(events)

    for event, node, remote in events:
        if event == 'connected':
            graph.setdefault(node, list()).append(remote)
        else:
            assert event == 'disconnected', event
            # print 'remove'
            graph[node].remove(remote)

    return graph


def visualize(graph):
    import networkx as nx
    import matplotlib.pyplot as plt
    from networkx import graphviz_layout

    G = nx.Graph()
    for node, remotes in graph.items():
        #print node[:8]
        for r in set(remotes):
            #print '\t', r[:8]
            G.add_edge(node, r)

#    print 'estrada_index', nx.estrada_index(G)
#    print 'eigenvector_centrality', nx.eigenvector_centrality(G)
#    print 'degree_centrality', nx.degree_centrality(G)
#    print 'communicability', nx.communicability(G)
    num_peers = [len(v) for v in graph.values()]

    metrics = OrderedDict(num_nodes=len(graph))
    metrics['max_peers'] = max(num_peers)
    metrics['min_peers'] = min(num_peers)
    metrics['avg_peers'] = sum(num_peers) / len(num_peers)
    metrics['diameter '] = nx.diameter(G)
    metrics['avg_shortest_path'] = nx.average_shortest_path_length(G)

    text = ''
    for k, v in metrics.items():
        text += '%s:\t%.2f\n' % (k, v)

    # pos = nx.graphviz_layout(G, prog='twopi', args='')
    pos = nx.spring_layout(G)
    plt.figure(figsize=(8, 8))
    nx.draw(G, pos, node_size=20, alpha=0.5, node_color="blue", with_labels=False)
    plt.text(0.02, 0.02, text, transform=plt.gca().transAxes)
    plt.axis('equal')
    plt.savefig('circular_tree.png')
    plt.show()


if __name__ == '__main__':
    sessions = session_times()
    print 'sessions', sessions
    SESSION = 0  # 0 == latest session
    if sessions:
        r = fetch(sessions[SESSION])
        g = analyze(r)
        visualize(g)
    # # pprint(g)
    # for node, remotes in g.items():
    #     print node[:8]
    #     assert len(remotes) == set(remotes)
    #     for r in remotes:
    #         print '\t', r[:8]
