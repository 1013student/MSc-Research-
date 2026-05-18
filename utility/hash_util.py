import json
import hashlib as _hl # Add single underscore, indicating that this variable is only used internally ）

def hash_string_256(string):
    return _hl.sha256(string).hexdigest()


# Use SHA256 to hash the block
def hash_block(block):
    """Hashes a block and returns a string representation of it

    Arguments
        block: The block that should be hashed 
    """
    # Add copy because hashable_block is used to convert to String by json.dumps
    # To avoid modifying the original data, use copy
    hashable_block = block.__dict__.copy()
    hashable_block['transactions'] = [tx.to_ordered_dict() for tx in hashable_block['transactions']]

    # Set sort_keys to True because to avoid the hash value being different due to the change of the order of the keys in the dictionary, thus causing verification failure
    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())
    