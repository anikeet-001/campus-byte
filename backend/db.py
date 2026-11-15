"""SQLAlchemy maps domain dataclasses onto the schema in schema.sql."""
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from sqlalchemy import create_engine, event, select, insert
from sqlalchemy.engine import URL
from sqlalchemy.orm import registry, Session

mapping = registry()

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

class Repository:
    def __init__(self, session):
        self.session = session

    def list(self, model, **filters):
        query = select(model).filter_by(**filters).order_by(model.id)
        return self.session.scalars(query).all()

    def get(self, model, **filters):
        return self.session.scalar(select(model).filter_by(**filters))

    def add(self, model, **values):
        key = self.session.scalar(insert(model).values(**values).returning(model.id))
        return self.session.get(model, key)

    def save(self, entity):
        self.session.add(entity)
        self.session.flush()

    def query(self, statement, params=()):
        return self.session.connection().exec_driver_sql(statement, params).mappings()

    def add_lines(self, order_id, lines):
        table = mapping.metadata.tables['OrderLine']
        self.session.execute(table.insert(), [
            dict(purchase=order_id, dish=dish, name=name, paise=price, quantity=count)
            for dish, name, price, count in lines
        ])

@lru_cache(maxsize=8)
def engine_for(path):
    engine = create_engine(URL.create('sqlite', database=path), connect_args={'timeout': 15})
    @event.listens_for(engine, 'connect')
    def foreign_keys(connection, record):
        connection.execute('PRAGMA foreign_keys=ON')
    return engine

def engine():
    return engine_for(os.getenv('DB_PATH', 'campus.sqlite'))

@contextmanager
def transaction(write=False):
    with Session(engine(), expire_on_commit=False) as session, session.begin():
        # Serialize write decisions (especially rider reservations) across processes.
        session.connection().exec_driver_sql('BEGIN IMMEDIATE' if write else 'BEGIN')
        yield Repository(session)

def initialize():
    path = os.getenv('DB_PATH', 'campus.sqlite')
    connection = sqlite3.connect(path)
    try:
        connection.executescript(Path(__file__).with_name('schema.sql').read_text())
    finally:
        connection.close()
    if not mapping.metadata.tables:
        mapping.metadata.reflect(engine())
        for model in (Account, Restaurant, Dish, Purchase):
            mapping.map_imperatively(model, mapping.metadata.tables[model.__name__])
