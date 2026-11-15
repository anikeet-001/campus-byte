import sqlite3
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Annotated, Literal
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from . import auth
from .db import Account, Restaurant, Dish, Purchase, initialize, transaction

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Email = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$', max_length=200)]

class Login(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)

class Registration(Login):
    name: Text
    role: Literal['customer','owner','partner']
    restaurant: Text | None = None

def session(user):
    return {'token': auth.token(user), 'user': {'id': user.id, 'name': user.name, 'role': user.role}}

@asynccontextmanager
async def lifespan(app):
    auth.secret()
    initialize()
    dispatch()
    yield

app = FastAPI(title='Campus Byte', lifespan=lifespan)

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.post('/api/register', status_code=201)
def register(data: Registration, tasks: BackgroundTasks):
    if data.role == 'owner' and not data.restaurant:
        raise HTTPException(422, 'Enter a restaurant name.')
    try:
        with transaction(True) as db:
            user = db.add(Account, email=data.email, name=data.name, role=data.role, password_hash=auth.password_hash(data.password))
            if data.role == 'owner':
                db.add(Restaurant, owner=user.id, name=data.restaurant)
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Email already registered.')
    if user.role == 'partner':
        tasks.add_task(dispatch)
    return session(user)

@app.post('/api/login')
def login(data: Login):
    with transaction() as db:
        user = db.get(Account, email=data.email)
    if not user or not auth.verify(data.password, user.password_hash):
        raise HTTPException(401, 'Incorrect email or password.')
    return session(user)
