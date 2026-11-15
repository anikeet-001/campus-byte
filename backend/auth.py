import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .db import Account, transaction

def secret():
    key = os.environ.get('JWT_SECRET', '')
    if len(key) < 32:
        raise RuntimeError('Set JWT_SECRET to at least 32 characters.')
    return key

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return salt + '.' + digest.hex()

def verify(password, stored):
    return hmac.compare_digest(stored, password_hash(password, stored.split('.')[0]))

def token(user):
    return jwt.encode({'sub': str(user.id), 'exp': datetime.now(timezone.utc) + timedelta(hours=8)}, secret(), algorithm='HS256')

def current(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    try:
        data = jwt.decode(credentials.credentials if credentials else '', secret(), algorithms=['HS256'], options={'require':['sub','exp']})
        with transaction() as db:
            user = db.get(Account, id=int(data['sub']))
        if user:
            return user
    except (jwt.InvalidTokenError, ValueError):
        pass
    raise HTTPException(401, 'Please sign in again.')

def require(role):
    def check(user=Depends(current)):
        if user.role != role:
            raise HTTPException(403, 'This action belongs to another role.')
        return user
    return check
