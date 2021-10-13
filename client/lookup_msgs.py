# Simple script to lookup messages
from datetime import datetime

from tinydb import Query, TinyDB
from pathlib import Path

script_path = Path(__file__)
db = TinyDB(script_path.parent / 'db.json')
msgs = db.search(Query().username == 'k0lush')

for msg in sorted(msgs, key=lambda x: x['timestamp']):
    print(f'{datetime.fromtimestamp(msg["timestamp"]).ctime()} {msg["from_user_modelname"]}: {msg["message"]}\n')