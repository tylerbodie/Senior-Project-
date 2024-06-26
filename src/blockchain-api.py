# MODIFIED FOR FEDERATED LEARNING
from flask import Flask, jsonify, request
import uuid
from blockchain import Blockchain


app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid.uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

NUM_TRAINERS = 2

@app.route('/mine', methods=['GET'])
def mine():
  
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    if 'type' not in values:
      return 'Missing values', 400

    if values['type'] == 'reward':
      required = ['sender', 'recipient', 'amount']
    elif values['type'] == 'local':
      required = ['trainer', 'gradient', 'data-size']
    elif values['type'] == 'global':
      required = ['gradient']
    else:
      return 'Invalid transaction type', 400

    # Check that the required fields are in the POST'ed data
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = None
    if values['type'] == 'reward':
      index = blockchain.new_transaction( values['sender'], values['recipient'], values['amount'])
    elif values['type'] == 'local':
      index = blockchain.new_gradients( values['trainer'], values['gradient'], values['data-size'])
    elif values['type'] == 'global':
      index = blockchain.new_global( values['gradient'])

    #index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/last', methods=['GET'])
def prev_block():
    response = {
        'chain': blockchain.chain[-1],
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/current', methods=['GET'])
def current_trns():
    response = {
        'current-transaction-length': len(blockchain.current_transactions),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
