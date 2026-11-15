from sqlalchemy.exc import IntegrityError
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
    except IntegrityError:
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

class DishInput(BaseModel):
    name: Text
    paise: int = Field(gt=0, le=10000000)

@app.get('/api/restaurants')
def restaurants():
    with transaction() as db:
        return [{'id': place.id, 'name': place.name, 'menu': [asdict(dish) for dish in db.list(Dish, restaurant=place.id, active=1)]} for place in db.list(Restaurant)]

@app.get('/api/menu')
def owner_menu(user=Depends(auth.require('owner'))):
    with transaction() as db:
        place = db.get(Restaurant, owner=user.id)
        return {'name': place.name, 'menu': db.list(Dish, restaurant=place.id, active=1)}

@app.post('/api/menu', status_code=201)
def add_dish(data: DishInput, user=Depends(auth.require('owner'))):
    with transaction(True) as db:
        return db.add(Dish, restaurant=db.get(Restaurant, owner=user.id).id, active=1, **data.model_dump())

def owned_dish(db, user, dish_id):
    dish = db.get(Dish, id=dish_id, restaurant=db.get(Restaurant, owner=user.id).id, active=1)
    if not dish:
        raise HTTPException(404, 'Menu item unavailable.')
    return dish

@app.put('/api/menu/{dish_id}')
def edit_dish(dish_id: int, data: DishInput, user=Depends(auth.require('owner'))):
    with transaction(True) as db:
        dish = owned_dish(db, user, dish_id)
        dish.name, dish.paise = data.name, data.paise
        db.save(dish)
        return dish

@app.delete('/api/menu/{dish_id}', status_code=204)
def remove_dish(dish_id: int, user=Depends(auth.require('owner'))):
    with transaction(True) as db:
        dish = owned_dish(db, user, dish_id)
        dish.active = 0
        db.save(dish)

class Line(BaseModel):
    dish: int
    quantity: int = Field(ge=1, le=30)

class Checkout(BaseModel):
    restaurant: int
    address: Text
    items: list[Line] = Field(min_length=1, max_length=50)

@app.post('/api/orders', status_code=201)
def checkout(data: Checkout, user=Depends(auth.require('customer'))):
    with transaction(True) as db:
        lines = []
        seen = set()
        for item in data.items:
            dish = db.get(Dish, id=item.dish, restaurant=data.restaurant, active=1)
            if not dish or dish.id in seen:
                raise HTTPException(422, 'Choose available, distinct items from one kitchen.')
            seen.add(dish.id)
            lines.append((dish.id, dish.name, dish.paise, item.quantity))
        total = sum(price * count for _, _, price, count in lines)
        order = db.add(Purchase, customer=user.id, restaurant=data.restaurant, address=data.address, total=total)
        db.add_lines(order.id, lines)
        return order

@app.get('/api/orders')
def orders(user=Depends(auth.current)):
    with transaction() as db:
        if user.role == 'owner':
            scope = {'restaurant': db.get(Restaurant, owner=user.id).id}
        elif user.role == 'partner':
            scope = {'partner': user.id}
        else:
            scope = {'customer': user.id}
        result = []
        for order in reversed(db.list(Purchase, **scope)):
            items = db.query('SELECT dish, name, paise, quantity FROM OrderLine WHERE purchase=?', (order.id,))
            result.append({**asdict(order), 'items': [dict(row) for row in items],
                           'kitchen': db.get(Restaurant, id=order.restaurant).name})
        return result

def dispatch():
    """Reserve an idle partner and the oldest waiting order in one write transaction."""
    with transaction(True) as db:
        idle = db.query("""SELECT id FROM Account WHERE role='partner'
            AND id NOT IN (SELECT partner FROM Purchase WHERE status IN ('assigned','picked_up') AND partner IS NOT NULL)
            ORDER BY id""").fetchall()
        for order, partner in zip(db.list(Purchase, status='waiting'), idle):
            order.status, order.partner = 'assigned', partner['id']
            db.save(order)

@app.post('/api/orders/{order_id}/{action}')
def transition(order_id: int, action: Literal['accept','reject','pickup','deliver'], tasks: BackgroundTasks, user=Depends(auth.current)):
    rules = {'accept': ('owner','requested','waiting'), 'reject': ('owner','requested','rejected'),
             'pickup': ('partner','assigned','picked_up'), 'deliver': ('partner','picked_up','delivered')}
    role, before, after = rules[action]
    if user.role != role:
        raise HTTPException(403, 'This action belongs to another role.')
    with transaction(True) as db:
        scope = {'restaurant': db.get(Restaurant, owner=user.id).id} if role == 'owner' else {'partner': user.id}
        order = db.get(Purchase, id=order_id, **scope)
        if not order:
            raise HTTPException(404, 'Order unavailable.')
        if order.status != before:
            raise HTTPException(409, 'Order status has changed. Refresh the list.')
        order.status = after
        db.save(order)
    if action in ('accept', 'deliver'):
        tasks.add_task(dispatch)
    return order
