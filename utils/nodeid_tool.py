#!/usr/bin/env python
import sys
from docopt import docopt
from sha3 import sha3_256
from bitcoin import privtopub, encode_pubkey

"""
external_id:  e.g. 'honest1, honest2, ...'
private_key:  hex(sha3(external_id))

private_key: is used to derive pubkey, address, etc.
"""

def sha3(seed):
    return sha3_256(seed).digest()

# all results are hex encoded

def sha3_hex(seed):
    return sha3(seed).encode('hex')

topriv = sha3_hex

def _privtopub(privkey):
    r = encode_pubkey(privtopub(privkey), 'bin_electrum')
    assert len(r) == 64
    return r

def topub(extid):
    r = _privtopub(topriv(extid)).encode('hex')
    assert len(r) == 128
    return r

tonodeid = topub

def toaddr(extid):
    r = sha3(_privtopub(topriv(extid)))[-20:].encode('hex')
    assert len(r) == 40
    return r

coinbase = toaddr

doc = \
    """nodeid_tool.py

Helper to deterministically generate
privkey, nodeid, address, coinbase
based on an external identifier.

privkey == sha3(extid)
nodeid == pubkey
address == coinbase == sha3(pubkey)[-20:]

all hex encoded

can be used with other command line tools, e.g.:
echo 'node-31' | ./nodeid_tool.py -s nodeid
06f8495ea9d5f23abd6f4bb4b3c5719945ee0d6b71c3dc7c398e7b7dc5cf354f

Usage:
  pyethclient sha3 <data>
  pyethclient privkey <extid>
  pyethclient pubkey  <extid>
  pyethclient nodeid  <extid>
  pyethclient address <extid>
  pyethclient coinbase <extid>

Options:
  -h --help                 Show this screen
  -s --stdin                take arguments from stdin
"""


def main():
    # Take arguments from stdin with -s
    if len(sys.argv) > 1 and sys.argv[1] == '-s':
        sys.argv = [sys.argv[0], sys.argv[2]] + \
            sys.stdin.read().strip().split(' ')
    # Get command line arguments
    arguments = docopt(doc, version='nodeid_tool 0.0.1')

    cmd_map = dict(sha3=(sha3_hex, arguments['<data>']),
                   privkey=(topriv, arguments['<extid>']),
                   pubkey=(topub, arguments['<extid>']),
                   nodeid=(tonodeid, arguments['<extid>']),
                   address=(toaddr, arguments['<extid>']),
                   coinbase=(toaddr, arguments['<extid>']),

                   )
    for k in cmd_map:
        if arguments.get(k):
            cmd_args = cmd_map.get(k)
            out = cmd_args[0](*cmd_args[1:])
            print out
            break

if __name__ == '__main__':
    main()
