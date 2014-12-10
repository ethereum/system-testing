#!/usr/bin/env python
"""
teees | tee like tool to log to elasticsearch

# -u     : unbuffered binary stdout and stderr (also PYTHONUNBUFFERED=x)

operation:
    read lines from pipes stdin, stderr
        if not valid json format:
            make fallback json format
        add timestamp
        add key/values parsed from sys.args
        send to an elasticsearch instance
        write to stdout/stderr



Kibana / Logstash:
indices should be formatted like logstash-YYYY.MM.DD.
You can change the pattern Kibana is looking for, but we won't do that here
logs must have a timestamp, stored in the @timestamp field.
It's also nice to put the message part in the message field
cause Kibana shows it by default


timestamp
    2009-11-15T14:12:12


ToDo:
    cmd line args:
        remote endpoint
        mining percentage

    Define messages+key/values

    initial log should contain
        nodeid
        version
        protocol

    prefix with timestamp
    prefix with initial data
"""
import sys
import json
import elasticsearch
from logstash_formatter import LogstashFormatter

if len(sys.argv) < 2:
    print "usage: loggging_app | teees.py <elasticsearch_host:port> <extra_key,value_pairs> ..."
    sys.exit(1)

es_endpoint = sys.argv[1]
extra = dict(x.split(',') for x in sys.argv[2:])

### ES
es = elasticsearch.Elasticsearch(es_endpoint)
es_index_name = 'logstash-2014.12.10' # logstash-YYYY.MM.DD
es_doc_type = 'ethlog'

def es_log(doc):
    es.create(index=es_index_name, doc_type=es_doc_type, body=doc)

lsformatter = LogstashFormatter(defaults=extra)

while True:
    l = sys.stdin.readline().strip()
    try:
        d = json.loads(l)
    except ValueError:
        d = dict(msg='raw', raw=l)
    # send to elasticsearch
    es_log(lsformatter.format(d))
    # tee like echo
    print l
