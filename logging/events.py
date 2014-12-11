"""
Describes the events we aim to log

Scope:
Nodes as black boxes (we don't care about their conclusions)
The system of interacting nodes as a white box (we know/log what should and is going on)

But developers might find the tool useful to get insight into their clients.
So log whatever you want (to add interesting bits or lower the development burden).

Event names maps:
You might want to user dfferent event names, that align better with your modules/metaphors/whatever.
Please add the translation to event_names_map.py

Events:
The expected event logs are defined below. You are free to emit more event logs.

Attributes:
Each event has expected attributes. You can add more attributes but not less.

Understand:
The log database can not efficiently do joins.
Therefore logs need to provide as much context as is needed to make sense.
i.e. log data is denormalized

Log Format:

Expected log records are json dicts which map
message_name : dict(of key value pairs)
Example: {'message_name': {eth_version=0, version='py', coinbase='address'}}

ToDo:
Testing mode which reads logs of a client and checks
    * if all required events where used
    * if all key/values are within the specicfication

"""

address = 'hex40'
hexid = 'hex128'
endpoint = 'host:port'
hexhash = 'hex64'
hexrlp = 'hexN'

class Event(object):
    """
    Base Event class which describes events, their names and expected information
        keeps track of all instances
        adds defaults to the description of logs
        inherit to set repeating key/value information requirements
    """
    events = []
    defaults = {'node_id': hexid}

    def __init__(self, name, **kargs):
        self.name = name
        kargs.update(self.defaults)
        self.kargs = kargs
        self.events.append(self)

    def dict(self):
        return {self.name:self.kargs}

# used for bad none json logs
Event('notjson', logging_error='', log_line='')

# Startup
Event('starting', eth_version=0, version='', coinbase=address)

# P2P
class P2PEvent(Event):
    defaults = dict(remote_nodeid=address, num_connections=0)
    defaults.update(Event.defaults)

P2PEvent('p2p.connecting', endpoint=endpoint)
P2PEvent('p2p.connected')
P2PEvent('p2p.handshaked', remote_capabilities=[])
P2PEvent('p2p.disconnected')
P2PEvent('p2p.disconnecting', reason='')
P2PEvent('p2p.disconnecting.bad_handshake', reason='')
P2PEvent('p2p.disconnecting.bad_block', reason='')
P2PEvent('p2p.disconnecting.bad_tx', reason='')
P2PEvent('p2p.disconnecting.bad_protocol', reason='')
P2PEvent('p2p.disconnecting.reputation', reason='')
P2PEvent('p2p.disconnecting.dht', reason='')

# Blocks
class BlockEvent(Event):
    defaults = dict(head=hexhash, block_hash=hexhash, prev_hash=hexhash, number=0, difficulty=0)
    defaults.update(Event.defaults)

BlockEvent('newblock.received')
BlockEvent('newblock.mined', hexrlp=hexrlp)
BlockEvent('newblock.broadcasted')
BlockEvent('newblock.is_known')
BlockEvent('newblock.is_new')
BlockEvent('newblock.missing_parent')
BlockEvent('newblock.is_invalid', reason='')
BlockEvent('newblock.chain.is_older')
BlockEvent('newblock.chain.is_current')
BlockEvent('newblock.chain.switched', old_head=hexhash)

# Transactions
class TXEvent(Event):
    defaults = dict(tx_hash=hexhash, sender=address, address=address, nonce=0)
    defaults.update(Event.defaults)

TXEvent('tx.created', hexrlp=hexrlp)
TXEvent('tx.received')
TXEvent('tx.broadcasted')
TXEvent('tx.validated')
TXEvent('tx.is_invalid', reason='')


import json
from collections import OrderedDict

def events():
    r = []
    for e in Event.events:
        r.append(e.dict())
    return r

def event_name_map():
    r = OrderedDict()
    for e in Event.events:
        r[e.name] = ''
    return r

if __name__ == '__main__':
    print json.dumps(events(), indent=4)
    #print json.dumps(event_name_map(), indent=4)

