import os
import sqlite3
from datetime import date, datetime

class DataStore:
    def __init__(self):
        databaseFilepath = os.path.dirname(os.path.realpath(__file__)) + '/' + 'data/mydb'
        self.db = sqlite3.connect(databaseFilepath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.db.row_factory = sqlite3.Row

        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (id INTEGER PRIMARY KEY, created_at TIMESTAMP, open_positions INTEGER, closed_positions INTEGER)
        ''')
        self.db.commit()

    def _destroy(self):
        cursor = self.db.cursor()
        cursor.execute('''DROP TABLE emails''')
        self.db.commit()

    def add_entry(self, openPositions=None, closedPositions=None):
        cursor = self.db.cursor()

        now = datetime.now()
        cursor.execute('''INSERT INTO emails (created_at, open_positions, closed_positions)
                          VALUES(?,?,?)''', (now, openPositions, closedPositions))
        print('Email inserted with date: %s, buys: %s, sells: %s' % (now, openPositions, closedPositions))

        self.db.commit()

    def fetch_entries(self, startDate=None):
        cursor = self.db.cursor()

        cursor.execute('''SELECT id, created_at as "[timestamp]", open_positions, closed_positions
                          FROM emails
                          WHERE emails.created_at > ?''', (startDate,))

        matches = []
        for row in cursor:
            entry = EmailEntry(row['id'], row[1], row['open_positions'], row['closed_positions'])
            matches.append(entry)

        return matches

    def close(self):
        self.db.close()

class EmailEntry:
    def __init__(self, id, createdAt, openPositions, closedPositions):
        self.id = id
        self.createdAt = createdAt
        self.openPositions = openPositions
        self.closedPositions = closedPositions

    def description(self):
        return "id: %s, createdAt: %s, openPositions: %s, closedPositions: %s" % (self.id, self.createdAt, self.openPositions, self.closedPositions)
