import hashlib
import json
from time import time


class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []

        # Create the genesis block
        self.create_block(previous_hash='1', proof=100)

    def create_block(self, proof, previous_hash=None):
        """
        Create a new block in the blockchain.
        :param proof: The proof given by the proof of work algorithm
        :param previous_hash: Hash of the previous block
        :return: New block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.pending_transactions = []
        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a block.
        :param block: Block
        :return: Hash
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def add_transaction(self, voter_id, party, timestamp):
        """
        Add a new transaction to the list of pending transactions.
        :param voter_id: ID of the voter
        :param party: Party voted for
        :param timestamp: Timestamp of the vote
        :return: Index of the block that will hold this transaction
        """
        self.pending_transactions.append({
            'voter_id': voter_id,
            'party': party,
            'timestamp': timestamp,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def proof_of_work(last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p such that hash(pp') contains 4 leading zeros
         - p is the previous proof, and p' is the new proof
        :param last_proof: Previous proof
        :return: New proof
        """
        proof = 0
        while not Blockchain.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof: Does hash(last_proof, proof) contain 4 leading zeros?
        :param last_proof: Previous proof
        :param proof: Current proof
        :return: True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @property
    def last_block(self):
        return self.chain[-1]
