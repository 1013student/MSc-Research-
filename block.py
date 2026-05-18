from time import time

class Block:
    def __init__(self, index, previous_hash, transactions, proof, time=time()):
        self.index = index                  # The index of the block in the blockchain
        self.previous_hash = previous_hash  # The hash of the previous block
        self.timestamp = time               # The time the block was created
        self.transactions = transactions    # The transactions included in the block
        self.proof = proof                  # The proof number that meets the difficulty requirement
