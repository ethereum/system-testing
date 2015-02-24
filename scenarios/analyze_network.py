import json
from elasticsearch_dsl import Search
from eshelper import F
from elasticsearch import Elasticsearch
import elasticsearch_dsl
from base import Inventory
#es_endpoint = '%s:9200' % Inventory().es
es_endpoint = '54.152.117.76:9200'  # FIXME speedup hack
client = Elasticsearch(es_endpoint)


def pprint(x):
    print json.dumps(x, indent=2)


def scenario_time():
    # {"@fields": {}, "@timestamp": "2015-02-23T17:03:41.738412Z", "@source_host": "newair.brainbot.com", "@message": "scenario.p2p_connect.started"}

    s = Search(client)
    s = s.filter('bool',
                 should=[F('term', at_message='scenario.p2p_connect.started'),
                         F('term', at_message='scenario.p2p_connect.starting.clients'),
                         F('term', at_message='scenario.p2p_connect.stopping.clients')])
    s = s.fields(['@message', '@timestamp'])
    s = s[0:10]
    s = s.sort('-@timestamp')  # desc,  we want the latest events
    response = s.execute()
    return response


def fetch():
    s = Search(client)
    s = s.filter('bool',
                 should=[F('term', at_message='p2p.disconnected'),
                         F('term', at_message='p2p.connected')])
    s = s.fields(['@fields.remote_id', 'guid', '@message', '@timestamp'])
    # FIXME add filter for time range
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
    # HACK, look for last connect
    for i, (event, n, r) in enumerate(reversed(events)):
        if event == 'connected':
            break
    events = events[:-i]
    print 'num events', len(events)
    # END HACK

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

    # G = nx.balanced_tree(3, 5)
    G = nx.Graph()
    for node, remotes in g.items():
        #print node[:8]
        for r in set(remotes):
            #print '\t', r[:8]
            G.add_edge(node, r)
#    print 'estrada_index', nx.estrada_index(G)
#    print 'eigenvector_centrality', nx.eigenvector_centrality(G)
#    print 'degree_centrality', nx.degree_centrality(G)
#    print 'communicability', nx.communicability(G)
    print 'diameter', nx.diameter(G)
    print 'avg shortest path', nx.average_shortest_path_length(G)
    #pos = nx.graphviz_layout(G, prog='twopi', args='')
    pos = nx.spring_layout(G)
    plt.figure(figsize=(8, 8))
    nx.draw(G, pos, node_size=20, alpha=0.5, node_color="blue", with_labels=False)
    plt.axis('equal')
    plt.savefig('circular_tree.png')
    plt.show()


if __name__ == '__main__':
    st = scenario_time()
    print st.hits
    r = fetch()
    g = analyze(r)
    visualize(g)
    # pprint(g)
    # for node, remotes in g.items():
    #     print node[:8]
    #     assert len(remotes) == set(remotes)
    #     for r in remotes:
    #         print '\t', r[:8]
