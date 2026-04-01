import hashlib


def hash_bytes(data_bytes):
    m = hashlib.md5()
    m.update(data_bytes)
    return m.hexdigest()
