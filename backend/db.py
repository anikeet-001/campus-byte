"""SQLite data mapper. Dataclass fields map one-to-one to SQL columns."""
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass

@dataclass
class Account:
    id: int
    name: str
    email: str
    password_hash: str
    role: str

@dataclass
class Restaurant:
    id: int
    owner: int
    name: str

@dataclass
class Dish:
    id: int
    restaurant: int
    name: str
    paise: int
    active: int

@dataclass
class Purchase:
    id: int
    customer: int
    restaurant: int
    address: str
    status: str
    partner: int | None
    total: int
    created: str

class Mapper:
    """Types and column names come only from application code. Values are bound."""
    def __init__(self, connection):
        self.sql = connection

    def list(self, model, **filters):
        where = ' AND '.join(f'{key}=?' for key in filters) or '1'
        rows = self.sql.execute(f'SELECT * FROM {model.__name__} WHERE {where} ORDER BY id', tuple(filters.values()))
        return [model(**dict(row)) for row in rows]

    def get(self, model, **filters):
        return next(iter(self.list(model, **filters)), None)

    def add(self, model, **values):
        columns = ', '.join(values)
        slots = ', '.join('?' for _ in values)
        cursor = self.sql.execute(f'INSERT INTO {model.__name__} ({columns}) VALUES ({slots})', tuple(values.values()))
        return self.get(model, id=cursor.lastrowid)

    def save(self, entity):
        values = asdict(entity)
        key = values.pop('id')
        fields = ', '.join(f'{name}=?' for name in values)
        self.sql.execute(f'UPDATE {type(entity).__name__} SET {fields} WHERE id=?', (*values.values(), key))

@contextmanager
def transaction(write=False):
    connection = sqlite3.connect(os.getenv('DB_PATH', 'campus.sqlite'), timeout=15)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        yield Mapper(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize():
    from pathlib import Path
    with transaction(True) as db:
        db.sql.executescript(Path(__file__).with_name('schema.sql').read_text())
