from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet

from blockchain import Blockchain

app = Flask(__name__, template_folder='ui', static_folder='ui', static_url_path='/ui')
CORS(app)

wallet = None
blockchain = None

# Home page route
@app.route('/', methods=['GET'])  
def get_ui():
    return send_from_directory('ui', 'index.html')

# Node management page route
@app.route('/network', methods=['GET'])
def get_network_ui(): 
    return send_from_directory('ui', 'network.html')

# Create a wallet (public and private keys, balance)
@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating wallet failed.'
        }
        return jsonify(response), 500


# Get wallet
@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Wallet not found. Please create a new wallet.'
        }
        return jsonify(response), 500
    
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for block in dict_chain:
        block['transactions'] = [tx.__dict__ for tx in block['transactions']]
    return jsonify(dict_chain), 200
    
# Mining
@app.route('/mine', methods=['POST'])
def mine():
  if blockchain.resolve_conflicts:  # When mining, if there is a conflict with the blockchain and other nodes
      response = {'message': 'Resolve conflicts first, block not added!'}
      return jsonify(response), 409

  block = blockchain.mine_block()
  if block is not None:
      dict_block = block.__dict__.copy()
      dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
      response = {
          'message': 'Block added successfully',
          'block': dict_block,
          'funds': blockchain.get_balance()
      }
      return jsonify(response), 201
  else:
      response = {
          'message': 'Adding a block failed.',
          'wallet_set_up': wallet.public_key != None
      }
      return jsonify(response), 500

# Add transaction
@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key is None:
        response = {
            'message': 'No wallet set up.',
        }
        return jsonify(response), 400

    values = request.get_json() if request.data else None
    if not values:
        response = {
            'message': 'No data found.'
        }
        return jsonify(response), 400

    required_fields = ['recipient', 'amount']
    if not all(field in values for field in required_fields):
        response = {
            'message': 'Required data in missing.'
        }
        return jsonify(response), 400
        
    recipient = values['recipient']
    amount = float(values['amount'])
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(
        recipient,
        wallet.public_key,
        signature,
        amount
    )
    
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed.'
        }
        return jsonify(response), 500

# Get transaction pool
@app.route('/transactions', methods=['GET'])
def get_open_transaction():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    response = dict_transactions
    return jsonify(response), 200

# Broadcast transaction
@app.route('/broadcast_transaction', methods=['POST'])
def broadcast_transaction():
    values = request.get_json()
    if not values:
        response = {'message': 'No data found.'}
        return jsonify(response), 400
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(key in values for key in required):
        response = {'message': 'Some data is missing.'}
        return jsonify(response), 400
    success = blockchain.add_transaction(values['recipient'], values['sender'], values['signature'], values['amount'], is_receiving=True)
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': values['recipient'],
                'amount': values['amount'],
                'signature': values['signature']
            }
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed.'
        }
        return jsonify(response), 500
   
 
# Boradcast block
@app.route('/broadcast_block', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = {'message': 'No data found.'}
        return jsonify(response), 400
    if 'block' not in values:
        response = {'message': 'Some data is missing.'}
        return jsonify(response), 400
    block = values['block']
    
    # If the index of the broadcasted block is equal to the index of the last block + 1
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {'message': 'Block added.'}
            print('Block added.')
            return jsonify(response), 201
        else:
            response = {'message': 'Block seems invalid.'}
            print('Block seems invalid.')
            return jsonify(response), 409
    elif block['index'] > blockchain.chain[-1].index: # If the length of the broadcasted block is greater than the length of the current block
        response = {'message': 'Blockchain seems to differ from local blockchain'}
        print('Blockchain seems to differ from local blockchain')
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {'message': 'Blockchain seems to be shorter, block not added'}
        print('Blockchain seems to be shorter, block not added')
        return jsonify(response), 409

# resolve conflicts
@app.route('/resolve_conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain was replaced!'}
    else:
        response = {'message': 'Local chain kept!'}
    return jsonify(response), 200

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    parser.add_argument('-debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    port = args.port

    wallet = Wallet(port) # Create a wallet for the node

    blockchain = Blockchain(wallet.public_key, port) # Create a blockchain for the node

    app.run(host='0.0.0.0', port=port, debug=args.debug)