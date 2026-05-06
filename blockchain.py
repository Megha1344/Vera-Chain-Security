import hashlib
import json
import sqlite3
from datetime import datetime

class VeraChain:
    def __init__(self):
        self.db_path = 'verachain.db'
        self._create_table()
        self.chain = []
        self.load_from_db()

    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS blocks 
                        (id INTEGER PRIMARY KEY, timestamp TEXT, products TEXT, 
                         prev_hash TEXT, hash TEXT)''')
        conn.commit()
        conn.close()

    def create_block(self, products, prev_hash):
        block = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'products': products,
            'prev_hash': prev_hash,
        }
        encoded = json.dumps(block, sort_keys=True).encode()
        block['hash'] = hashlib.sha256(encoded).hexdigest()

        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO blocks (timestamp, products, prev_hash, hash) VALUES (?, ?, ?, ?)",
                     (block['timestamp'], json.dumps(products), block['prev_hash'], block['hash']))
        conn.commit()
        conn.close()
        self.load_from_db()
        return block

    def load_from_db(self):
        self.chain = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM blocks ORDER BY id ASC")
        for row in cursor:
            self.chain.append({
                'timestamp': row[1],
                'products': json.loads(row[2]),
                'prev_hash': row[3],
                'hash': row[4]
            })
        conn.close()
        if not self.chain:
            self.create_block([], '0')

    def verify_id(self, product_id):
        self.load_from_db()
        for block in self.chain:
            for p in block['products']:
                if p.get('product_id') == product_id:
                    return p
        return None

    def validate_chain(self):
        self.load_from_db()
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i-1]
            block_for_hash = {'timestamp': current['timestamp'], 'products': current['products'], 'prev_hash': current['prev_hash']}
            recalculated = hashlib.sha256(json.dumps(block_for_hash, sort_keys=True).encode()).hexdigest()
            if current['hash'] != recalculated or current['prev_hash'] != prev['hash']:
                return False
        return True

vera_ledger = VeraChain()
