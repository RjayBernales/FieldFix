"""One-process SQLite store. Every mutation uses an explicit transaction."""
import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, path):
        if path != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS samples(sequence INTEGER PRIMARY KEY, sampled_at REAL NOT NULL,
            received_at REAL, value REAL NOT NULL, quality TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS incidents(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, observed_at REAL, message TEXT);
        CREATE TABLE IF NOT EXISTS inference(id INTEGER PRIMARY KEY, incident_id TEXT, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY CHECK(id=1), used INTEGER NOT NULL);
        INSERT OR IGNORE INTO budget VALUES(1,0);
        ''')

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise

    def get(self, table, id):
        assert table in {'config', 'incidents', 'proposals', 'evidence'}
        with self.lock:
            row = self.db.execute(f'SELECT body FROM {table} WHERE id=?', (id,)).fetchone()
            return json.loads(row[0]) if row else None

    def put(self, table, id, body):
        assert table in {'config', 'incidents', 'proposals'}
        self.db.execute(f'INSERT OR REPLACE INTO {table}(id,body) VALUES(?,?)', (id, json.dumps(body)))

    def all(self, table):
        assert table in {'incidents', 'proposals'}
        with self.lock:
            return [json.loads(r[0]) for r in self.db.execute(f'SELECT body FROM {table} ORDER BY rowid')]

    def close(self):
        self.db.close()
