from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet

difficulty = 5  # You can change the difficulty level by changing the number of 0s

class Verification:
    """Proof-of-work"""
    """SHA256(Transaction Records + Previous Block's Hash + Random Number)"""
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        # Because transactions contains tx objects
        # Transaction class defines the to_ordered_dict method
        # Call the object's method to_ordered_dict() to convert to OrderedDict
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        guess_hash = hash_string_256(guess)
        # print(guess_hash)
        return guess_hash.startswith('0' * difficulty)

    # Verify the hash value in the block
    @classmethod
    def verify_chain(cls, blockchain):
        # block_index = 0
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False

            # block['transactions'][:-1]
            # We put the system reward transaction in the last position, so we exclude it by ending with index
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print('Proof of work is invalid')
                return False
        return True

    # Verify a single transaction
    # check_funds = True: verify the balance of the sender
    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)  # Check if the sender's balance is greater than the amount of the transaction
        else:
            return Wallet.verify_transaction(transaction)

    # Verify the transaction list
    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        # The all function is used to check if all values in the list are True
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])

