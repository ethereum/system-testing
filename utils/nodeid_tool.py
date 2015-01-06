#!/usr/bin/env python
import sys
from docopt import docopt
from pyethereum import utils

def sha3(x):
    return utils.sha3(x).encode('hex')

topriv = sha3

def privtoaddr(x):
    x = topriv(x)
    if len(x) == 64:
        x = x.decode('hex')
    return utils.privtoaddr(x)

def privtonodeid(x):
    return topriv(x)


doc = \
    """nodeid_tool.py

Helper to deterministically generate
privkey, nodeid, address, coinbase
based on an external identifier.

nodeid == privkey == sha3(external_id) (hex encoded)
address == coinbase

can be used with other command line tools, e.g.:
echo 'node-31' | ./nodeid_tool.py -s nodeid
06f8495ea9d5f23abd6f4bb4b3c5719945ee0d6b71c3dc7c398e7b7dc5cf354f

Usage:
  pyethclient sha3 <data>
  pyethclient privkey <extid>
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

    cmd_map = dict(sha3=(sha3, arguments['<data>']),
                   privkey=(topriv, arguments['<extid>']),
                   nodeid=(privtonodeid, arguments['<extid>']),
                   address=(privtoaddr, arguments['<extid>']),
                   coinbase=(privtoaddr, arguments['<extid>']),

                   )
    for k in cmd_map:
        if arguments.get(k):
            cmd_args = cmd_map.get(k)
            out = cmd_args[0](*cmd_args[1:])
            print out
            break

if __name__ == '__main__':
    main()
