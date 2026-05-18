from functools import reduce
from uuid import uuid4
import json
import os

from block import Block
from transaction import Transaction
from wallet import Wallet

from utility.hash_util import hash_block
from utility.verification import Verification

import requests

MINING_REWARD = 10.0  # Mining reward

"""In the class, double underscores + variable name represents the private type variable, such as: __chain"""
class Blockchain:
    def __init__(self, publick_key, node_id):
        genesis_block = Block(0, '', [], 100, 0) # Genesis block
        self.chain = [genesis_block]  # Initialize blockchain
        self.__open_transactions = []  # Transaction pool
        self.public_key = publick_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    """The "property" decorator is used to create a *read-only property*, which converts the method into a *read-only property*, and can be used with the defined property, so that the property cannot be modified"""    
    @property
    def chain(self):
        return self.__chain[:]

    # When you don't want users to modify self.chain directly, you can define chain as a property to control read and write
    # When assigning a value to self.chain, it is equivalent to assigning a value to self.__chain
    @chain.setter
    def chain(self, val):
        self.__chain = val
   
    # Load blockchain data
    def load_data(self):
        """ 1. mode 'rb' read the binary data
            2. use pickle to read and write data is better than using json
            3. because using json to load data may occur some order problem
        """
        try:
            with open('blockchain/blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()

                blockchain = json.loads(file_content[0][:-1]) # Add [:-1] to remove the \n at the end
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(tx['txid'], tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
                    updated_block = Block(
                        block['index'],
                        block['previous_hash'],
                        converted_tx,
                        block['proof'],
                        block['timestamp']
                    )
                    updated_blockchain.append(updated_block)
                
                # Store variables, here because setter is involved, and other places are getter
                # self.chain is assigned to self.__chain
                # Therefore, when reading chain elsewhere, still use self.__chain
                self.chain = updated_blockchain

                open_transactions = json.loads(file_content[1][:-1]) # Add [:-1] to remove the \n at the end
                updated_open_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx['txid'], tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    updated_open_transactions.append(updated_transaction)
                self.__open_transactions = updated_open_transactions
                
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError): # Handle the problem of empty file
            print('No blockchain data found, handle exception...')
            genesis_block = Block(0, '', [], 100, 0) # Genesis block
            self.chain = [genesis_block]
            self.__open_transactions = []
            self.__peer_nodes = set()
            self.save_data()
        finally:
            print('Cleanup!')
    
    # Save transactions to the local file
    def save_data(self): 
        try:
            # Create blockchain directory if it doesn't exist
            os.makedirs('blockchain', exist_ok=True)
            with open('blockchain/blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                # Because block is an object of the Block class, it cannot be converted to a String type directly using json.dumps
                # So we need to convert all blocks in the blockchain list to dicts, using block.__dict__
                saveable_chain = [block.__dict__
                                for block in [Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp)
                                                for block_el in self.__chain]]
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
    
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')
     
    # Calculate user balance
    def get_balance(self, sender=None):
        if sender is None:
            if self.public_key is None:
                return None

            participant = self.public_key
        else:
            participant = sender

        # Get all the amount records of the user's outgoing transactions from the past transactions
        tx_sender = [[tx.amount
                    for tx in block.transactions if tx.sender == participant] for block in self.__chain]
        # Get the amount records of the user's outgoing transactions in the transaction pool
        open_tx_sender = [tx.amount
                        for tx in self.__open_transactions if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        print(tx_sender, 'tx_sender')

        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt), tx_sender, 0) # Simplified version

        # Get the total amount of the user's incoming transactions from the past transactions
        tx_recipient = [[tx.amount
                        for tx in block.transactions if tx.recipient == participant] for block in self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt), tx_recipient, 0) # Simplified version
        print(tx_recipient, 'tx_recipient')

        return amount_received - amount_sent  # Received - Sent = Balance
    
        # Proof-of-work
    
    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0

        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof +=1
        return proof
   
    # Mining
    def mine_block(self):
        """Create a new block and add open transactions to it."""
        if self.public_key == None:
            return None
        
        # Step 1: Verify all transactions in the transaction pool
        copied_transactions = self.__open_transactions[:]  # Copy the transaction pool records (before adding the reward transaction) (deep copy!)
        for tx in copied_transactions: # Verify the signature
            if not Wallet.verify_transaction(tx):
                return None

        # Step 2: Hash the last block
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)  # Calculate the hash value of the previous block
        
        # Step 3: Proof-of-work
        proof = self.proof_of_work() # PoW only targets transactions in open_transactions, not including the system reward transaction

        # Step 4: Create a reward transaction
        txid = str(uuid4())
        reward_transaction = Transaction(txid, 'MINING', self.public_key, '', MINING_REWARD) # System reward
        
        # Step 5: Combine the reward transaction with the verified transactions
        copied_transactions.append(reward_transaction) # Add the system reward coinbase transaction
        
        # Step 6: Create a new block
        block = Block(  # Create a new block
            len(self.__chain),
            last_hash,
            copied_transactions,
            proof
        )

        # Step 7: Add the new block to the blockchain
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()

        # Step 8: Broadcast the new block
        for node in self.__peer_nodes:
            url = f'http://{node}/broadcast_block' if 'http' not in node else f'{node}/broadcast_block'
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    print('Block invalid or the local blockchain is shorter. Nees resolving')
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue

        return block
    
    # Add a new transaction to the transaction pool
    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """
        Arguments:
            :sender: The sender of the coins.
            :recipient: The recipient of the coins.
            :amont: The amount of coins sent with the transaction (default=1.0)
        """
        txid = str(uuid4())
        transaction = Transaction(txid, sender, recipient, signature, amount)

        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()

            # if the new transaction is self-initiated, broadcast it to other nodes
            if not is_receiving:
                # Broadcast transaction
                for node in self.__peer_nodes:
                    url = f'http://{node}/broadcast_transaction' if 'http' not in node else f'{node}/broadcast_transaction'
                    try:
                        response = requests.post(url, json={'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue

            return True
            


        return False
    
    # Return the open transactions list
    def get_open_transactions(self):
            return self.__open_transactions[:]
    
    # Receive the broadcast of other nodes, and process the block
    def add_block(self, block):
        transactions = [Transaction(tx['txid'], tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']

        if not proof_is_valid or not hashes_match:
            return False

        converted_block = Block(block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]

        # After adding the broadcasted block, clean up the records in the transaction pool
        for itx in block['transactions']:
            for opentx in stored_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed')

        self.save_data()
        return True 
    
    # Resolve conflicts
    # Find the longest chain in the network
    def resolve (self):
        winner_chain = self.chain
        replace = False

        for node in self.__peer_nodes:
            url = f'http://{node}/chain' if 'http' not in node else f'{node}/chain'
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'],
                                    block['previous_hash'],
                                    [Transaction(tx['txid'], tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']],
                                    block['proof'],
                                    block['timestamp']) for block in node_chain]
                
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain

        if replace:
            self.__open_transactions = []

        self.save_data()
        return replace