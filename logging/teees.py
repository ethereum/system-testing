#!/usr/bin/env python
"""
teees | tee like tool to log to elasticsearch

# -u     : unbuffered binary stdout and stderr (also PYTHONUNBUFFERED=x)

operation:
    read lines from pipes stdin (redirect stderr)
        if not valid json format:
            make fallback json format
        add timestamp
        add key/values parsed from sys.args
        send to an elasticsearch instance
        echo original to stdout (necessary?)

Kibana / Logstash:
indices should be formatted like logstash-YYYY.MM.DD.
You can change the pattern Kibana is looking for, but we won't do that here
logs must have a timestamp, stored in the @timestamp field.
It's also nice to put the message part in the message field
cause Kibana shows it by default

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
import datetime
import elasticsearch
from logstash_formatter import LogstashFormatter
from event_names_map import substitutions

if len(sys.argv) < 2:
    print "usage: loggging_app | teees.py <elasticsearch_host:port> <extra_key,value_pairs> ..."
    sys.exit(1)

es_endpoint = sys.argv[1]
extra = dict(x.split(',') for x in sys.argv[2:])

# ES
es = elasticsearch.Elasticsearch(es_endpoint)
# logstash-YYYY.MM.DD
es_index_name = 'logstash-%s' % datetime.datetime.utcnow().strftime('%Y.%m.%d')
es_doc_type = 'ethlog'


def es_log(doc):
    es.create(index=es_index_name, doc_type=es_doc_type, body=doc)

lsformatter = LogstashFormatter(defaults=extra)

while True:
    l = sys.stdin.readline().strip()
    if not l:
        continue
    try:
        d = json.loads(l)
    except ValueError:
        d = dict(event='notjson', log_line=l, logging_error='raw input')

    # FIX for wrongly specified events
    d = d if len(d) > 1 else dict(list(d.values()[0].items()) + [('event', d.keys()[0])])

    # check that there is an event
    if 'event' not in d:
        d['event'] = 'notset'
        d['logging_error'] = 'event_not_set'

    # substitute event name
    d['event'] = substitutions.get(d['event'], d['event'])

    # format for kibana
    kd = lsformatter.format(d)

    # send to elasticsearch
    es_log(kd)

    # tee like echo
#    print l
