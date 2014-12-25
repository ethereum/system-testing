import events

# 'other.name' => 'expected_name'
substitutions = dict()

def add_substitutions(substs):
    for official, slang in substs.items():
        assert official in template
        assert slang and isinstance(slang, str)
        substitutions[slang] = template

template = \
{
    "notjson": "",
    "starting": "",
    "p2p.connecting": "",
    "p2p.connected": "",
    "p2p.handshaked": "",
    "p2p.disconnected": "",
    "p2p.disconnecting": "",
    "p2p.disconnecting.bad_handshake": "",
    "p2p.disconnecting.bad_block": "",
    "p2p.disconnecting.bad_tx": "",
    "p2p.disconnecting.bad_protocol": "",
    "p2p.disconnecting.reputation": "",
    "p2p.disconnecting.dht": "",
    "newblock.received": "",
    "newblock.mined": "",
    "newblock.broadcasted": "",
    "newblock.is_known": "",
    "newblock.is_new": "",
    "newblock.missing_parent": "",
    "newblock.is_invalid": "",
    "newblock.chain.is_older": "",
    "newblock.chain.is_current": "",
    "newblock.chain.switched": "",
    "tx.created": "",
    "tx.received": "",
    "tx.broadcasted": "",
    "tx.validated": "",
    "tx.is_invalid": ""
}

# currently fails. Haven't checked why
# assert template == events.event_name_map()

### pyeth (example)

pyeth = \
{
    "starting": "start",
    "p2p.connecting": "connecting",
    "p2p.connected": "connected",
    "p2p.handshaked": "recv_status",
}

add_substitutions(pyeth)

### cpp


### go


### J


### JS
