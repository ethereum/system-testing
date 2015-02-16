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

Recommended Reading - Logging Best Practices:
https://docs.google.com/a/ethdev.com/document/d/1oeW_l_YgQbR-C_7R2cKl6eYBT5N4WSMbvz0AT6hYDvA/edit?pli=1


Log Format:

Expected log records are json dicts which map
message_name : dict(of key value pairs)
Example: {'message_name': {eth_version=0, version_string='py', coinbase='address'}}


Questions:
* namespaces?
* should we log the chain syncing?


ToDo:
Testing mode which reads logs of a client and checks
    * if all required events where used
    * if all key/values are within the specicfication

"""

address = 'hex40, e.g. 0x0123456789abcdef0123456789abcdef01234567'
protocol_version = 'int, e.g. 52'
guid = 'hex128, e.g. 0x0123456789abcdef... 128 digits'
client_addr = 'host:port, e.g. 10.46.56.35:30303 or poc-8.ethdev.com:30303'
client_impl = 'Impl/OS/version, e.g. Go/Linux/0.8.2'
hexhash = 'hex64, e.g. 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
hexrlp = 'hexN'
timestamp = 'YYYY-MM-DDTHH:MM:SS.SSSSSSZ'
num_connections = 'int, e.g. 4 - number of other nodes this client is currently connected to'

class Event(object):
    """
    Base Event class which describes events, their names and expected information
        keeps track of all instances
        adds defaults to the description of logs
        inherit to set repeating key/value information requirements
    """
    events = []
    defaults = dict(ts=timestamp)

    def __init__(self, name, **kargs):
        self.name = name
        kargs.update(self.defaults)
        self.kargs = kargs
        self.events.append(self)

    def dict(self):
        return {self.name:self.kargs}


##########################################################
# Events that clients should log
##########################################################

# Startup
Event('starting', comment='one of the first log events, before any operation is started', level='info', eth_version=protocol_version, client_impl=client_impl)

# P2P
class P2PEvent(Event):
    defaults = dict(remote_id=guid, num_connections=num_connections)
    defaults.update(Event.defaults)

# P2PEvent('p2p.connecting', remote_addr=client_addr)
P2PEvent('p2p.connected', comment='as soon as a successful connetion to another node is established', level='info', remote_addr=client_addr, remote_impl=client_impl)
#P2PEvent('p2p.handshaked', remote_capabilities=[])
#P2PEvent('p2p.disconnected')
#P2PEvent('p2p.disconnecting', reason='')
# more precise reasons
# P2PEvent('p2p.disconnecting.bad_handshake', reason='')
# P2PEvent('p2p.disconnecting.bad_protocol', reason='')
# e.g. if a peer doesn't deliver (txs, blks, ...) as expected
# P2PEvent('p2p.disconnecting.reputation', reason='')
# e.g. if there where better connection options found
# P2PEvent('p2p.disconnecting.dht', reason='')
# if a peer sends rough info
# P2PEvent('p2p.eth.disconnecting.bad_block', reason='')
#P2PEvent('p2p.eth.disconnecting.bad_tx', reason='')


# Blocks
class BlockEvent(Event):
    defaults = dict(head_hash=hexhash, block_hash=hexhash, block_prev_hash=hexhash, block_number=0, block_difficulty=0)
    defaults.update(Event.defaults)

# created blocks
# BlockEvent('eth.newblock.mined', block_hexrlp=hexrlp)
# BlockEvent('eth.newblock.broadcasted')

class ReceivedBlockEvent(BlockEvent):
    defaults = dict(remote_id=guid)
    defaults.update(BlockEvent.defaults)

# received blocks
#ReceivedBlockEvent('eth.newblock.received')
#ReceivedBlockEvent('eth.newblock.is_known')
#ReceivedBlockEvent('eth.newblock.is_new')
#ReceivedBlockEvent('eth.newblock.missing_parent')
#ReceivedBlockEvent('eth.newblock.is_invalid', reason='')
## previously unknown block w/ block.number < head.number
#ReceivedBlockEvent('eth.newblock.chain.is_older')
## block which appends to the chain w/ highest difficulty (after appending)
#ReceivedBlockEvent('eth.newblock.chain.is_canonical')
## block which appends to a chain which has not the highest difficulty
#ReceivedBlockEvent('eth.newblock.chain.not_canonical')
## if the block makes adds to a differnt chain which then has the highest total difficult.
## i.e. block.prev != head.prev != head
#ReceivedBlockEvent('eth.newblock.chain.switched', old_head_hash=hexhash)


# Transactions
class TXEvent(Event):
    defaults = dict(tx_hash=hexhash, tx_sender=address, tx_address=address, tx_nonce=0)
    defaults.update(Event.defaults)


# scope of tx events is only for those received over the wire
# not those included in blocks (discuss!)
#TXEvent('eth.tx.created', tx_hexrlp=hexrlp)
#TXEvent('eth.tx.received', remote_id=guid)
#TXEvent('eth.tx.broadcasted')
#TXEvent('eth.tx.validated')
#TXEvent('eth.tx.is_invalid', reason='')


# used by teees.py to wrap and annotate bad none json logs
Event('notjson', logging_error='', log_line='', comment='not to be implemented by clients')

#########################################

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

