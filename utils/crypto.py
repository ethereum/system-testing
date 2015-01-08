import bitcoin
from sha3 import sha3_256


def sha3(seed):
    return sha3_256(seed).digest()


def my_privkey_to_pubkey(privkey):
    f = bitcoin.get_privkey_format(privkey)
    privkey = bitcoin.decode_privkey(privkey, f)
    assert privkey < bitcoin.N
    assert f == 'bin'
    return bitcoin.encode_pubkey(bitcoin.fast_multiply(bitcoin.G, privkey), f)

secret = 'heiko'
privkey = sha3(secret)
f = bitcoin.get_privkey_format(privkey)
pubkey = bitcoin.privkey_to_pubkey(privkey)
pubkey = bitcoin.encode_pubkey(pubkey, 'bin_electrum')
assert len(pubkey) == 64, len(pubkey)
print pubkey.encode('hex')
