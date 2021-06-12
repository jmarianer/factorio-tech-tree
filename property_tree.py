import struct
from collections import defaultdict

BOOL = 1
NUM  = 2
STR  = 3
LIST = 4
DICT = 5


def read_string(file):
    # Not handling empty keys or len>255
    value_len = file.read(2)[1]
    return file.read(value_len).decode('ascii')


def read_tree_rec(file):
    tree_type = file.read(2)[0]

    if tree_type == DICT:
        tree = defaultdict(lambda: None)
        count, = struct.unpack('I', file.read(4))
        for _ in range(count):
            key = read_string(file)
            value = read_tree_rec(file)
            tree[key] = value
        return tree

    if tree_type == BOOL:
        return file.read(1)[0] == 1

    if tree_type == NUM:
        value, = struct.unpack('d', file.read(8))
        return value

    if tree_type == STR:
        return read_string(file)

    # This doesn't handle LIST, nor any other future tree type.
    raise Exception(f'Unknown/unhandled tree type {tree_type}')


def read_tree_file(filename):
    with open(filename, 'rb') as file:
        # Skip nine-byte header
        file.read(9).hex()
        return read_tree_rec(file)
