#!/usr/bin/env python
"""
Kibana:
http://54.164.87.19/index.html#/dashboard/file/default.json
"""
from datetime.datetime import utcnow
import json
import elasticsearch
from addict import Dict


es_index_prefix = 'logstash-'
es_index_name = 'logstash-%s' % utcnow().strftime('%Y.%m.%d')  # logstash-YYYY.MM.DD
es_doc_type = 'ethlog'

# different config.json can be specified at the command line
config = default_config = {
    "index_prefix": es_index_prefix,       # logstash-YYYY.MM.DD
    "doctype": es_doc_type,    # doctype of a classifed doc
    "es_host": "localhost",
    "es_port": 9200,
}


def pprint(data):
    print json.dumps(data, indent=2)

def search(es, index_name):
    body = Dict()
    body.query.has_parent.query.match_all
    body.query.has_parent.type = config['eval_doctype']
    # body.post_filter.term.evaluated = 'no'
    # body._source = True
    # body.fields = ['_parent']
    # body.sort._parent.order = 'asc'

    classifications = Dict(es.search(index_name, es_doc_type, body=body))

    return classifications

def main(config):
    es = elasticsearch.Elasticsearch(host=config['es_host'], port=config['es_port'])
    indices = [i for i in es.indices.status()['indices'].keys()
                    if i.startswith(config['index_prefix'])]








if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        config = json.loads(sys.argv[1])
    main(config)
