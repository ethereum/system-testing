"""
Describes the events we aim to log

Recommended Reading - Logging Best Practices:
https://docs.google.com/a/ethdev.com/document/d/1oeW_l_YgQbR-C_7R2cKl6eYBT5N4WSMbvz0AT6hYDvA/edit?pli=1

ToDo:
Testing mode which reads logs of a client and checks
    * if all required events where used
    * if all key/values are within the specicfication
    * uncomment necessary log event when needed

"""

address = 'hex40, e.g. 0123456789abcdef0123456789abcdef01234567'
protocol_version = 'int, e.g. 52'
guid = 'hex128, e.g. 0123456789abcdef... exactly 128 digits'
client_addr = 'ipv4:port, e.g. 10.46.56.35:30303'
client_impl = 'Impl/OS/version, e.g. Go/Linux/0.8.2'
hexhash = 'hex64, e.g. 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
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
        return {self.name: self.kargs}


##########################################################
# Events that clients should log
##########################################################

# Startup
Event('starting', comment='one of the first log events, before any operation is started',
      eth_version=protocol_version, client_impl=client_impl)

# P2P


class P2PEvent(Event):
    defaults = dict(remote_id=guid, num_connections=num_connections)
    defaults.update(Event.defaults)

# P2PEvent('p2p.connecting', remote_addr=client_addr)
P2PEvent('p2p.connected',
         comment='as soon as a successful connection to another node is established',
         remote_addr=client_addr, remote_version_string=client_impl)
P2PEvent('p2p.disconnected',
         comment='as soon as a disconnection from another node happened',
         remote_addr=client_addr)
# P2PEvent('p2p.handshaked', remote_capabilities=[])
# P2PEvent('p2p.disconnected')
# P2PEvent('p2p.disconnecting', reason='')
# more precise reasons
# P2PEvent('p2p.disconnecting.bad_handshake', reason='')
# P2PEvent('p2p.disconnecting.bad_protocol', reason='')
# e.g. if a peer doesn't deliver (txs, blks, ...) as expected
# P2PEvent('p2p.disconnecting.reputation', reason='')
# e.g. if there where better connection options found
# P2PEvent('p2p.disconnecting.dht', reason='')
# if a peer sends rough info
# P2PEvent('p2p.eth.disconnecting.bad_block', reason='')
# P2PEvent('p2p.eth.disconnecting.bad_tx', reason='')


# Blocks
class BlockEvent(Event):
    defaults = dict(chain_head_hash=hexhash, block_hash=hexhash,
                    block_prev_hash=hexhash, block_number=0)
    defaults.update(Event.defaults)

# created blocks
BlockEvent('eth.miner.new_block',
           comment='as soon as the block was mined, before adding as new head')
BlockEvent('eth.chain.received.new_block', remote_id=guid,
           comment='whenever a _new_ block is received, before adding')
BlockEvent('eth.chain.new_head', comment='whenever head changes')


# Transactions
class TXEvent(Event):
    defaults = dict(tx_hash=hexhash)
    defaults.update(Event.defaults)


# scope of tx events is only for those received over the wire
# not those included in blocks (discuss!)
TXEvent('eth.tx.received', remote_id=guid)


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
    # print json.dumps(event_name_map(), indent=4)
