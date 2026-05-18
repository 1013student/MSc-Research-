from collections import OrderedDict

class Transaction:
    """A transaction which can be added to a block in the blockchain"""
    def __init__(self, txid, sender, recipient, signature, amount):
        self.txid = txid            # The transaction ID created by uuid
        self.sender = sender        # The public key of the sender
        self.recipient = recipient  # The public key of the recipient
        self.amount = amount        # The amount of coins sent
        self.signature = signature  # The signature of the transaction signed by the sender's private key
 
    def to_ordered_dict(self):
        # Use the Python built-in OrderedDict library to create a sorted dictionary
        # This can avoid the problem of verification failure due to the order of the string
        return OrderedDict([
            ('sender', self.sender),
            ('recipient', self.recipient),
            ('amount', self.amount)
        ])