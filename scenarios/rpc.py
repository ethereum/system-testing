import pyjsonrpc


def coinbase(endpoint):
    """
     curl -X POST --data '{"jsonrpc":"2.0","method":"eth_coinbase","params":[],"id":1}' http://54.67.35.229:20000
     """
    c = pyjsonrpc.HttpClient(endpoint)
    r = c.call('eth_coinbase')
    return r


def balance(endpoint, address_hex):
    """
    curl -X POST --data '{"jsonrpc":"2.0","method":"eth_balanceAt", "params":["0x4c6634475af56fe370d9841607c9f65099693ef8"],"id":1}' http://54.67.35.229:20000
{"id":1,"jsonrpc":"2.0","result":"0x058788cb94b1d7f6f0"}%
    """
    c = pyjsonrpc.HttpClient(endpoint)
    r = c.call('eth_balanceAt', address_hex)
    return long(r, 16)


def transact(endpoint, sender, to, value=0, data=''):
    """
    curl -X POST --data '{"jsonrpc":"2.0","method":"eth_transact","params":[{"from": "0x4c6634475af56fe370d9841607c9f65099693ef8", "to":"0xd46e8dd67c5d32be8058bb8eb970870f072445675", "value": "0x910"}],"id":1}' http://54.67.35.229:20000
    """
    c = pyjsonrpc.HttpClient(endpoint)
    r = c.call('eth_transact', {'from': sender, 'to': to, 'value': hex(value), 'data': data})
    return r


if __name__ == '__main__':
    endpoint = 'http://54.67.35.229:20000'
    cb = coinbase(endpoint)
    print cb
    v = balance(endpoint, cb)
    print v
    receiver = '0xd46e8dd67c5d32be8058bb8eb970870f072445675'
    r = transact(endpoint, sender=cb, to=receiver, value=100)
    print r
