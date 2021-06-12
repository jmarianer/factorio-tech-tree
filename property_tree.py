import struct
from collections import defaultdict

def read_tree_rec(file):
    tree_type = file.read(2)[0]
    if tree_type == 5:
        tree = defaultdict(lambda: None)
        count, = struct.unpack('I', file.read(4))
        for _ in range(count):
            # Not handling empty keys or len>255
            key_len = file.read(2)[1]
            key = file.read(key_len).decode('ascii')
            value = read_tree_rec(file)
            tree[key] = value
        return tree
    elif tree_type == 1:
        return file.read(1)[0] == 1
    elif tree_type == 2:
        value, = struct.unpack('d', file.read(8))
        return value
    elif tree_type == 3:
        # Not handling empty strings or len>255
        value_len = file.read(2)[1]
        return file.read(value_len).decode('ascii')
    else:
        print(tree_type)
        exit()


def read_tree_file(filename):
    with open(filename, 'rb') as file:
        # Skip header
        file.read(9).hex()
        return read_tree_rec(file)
