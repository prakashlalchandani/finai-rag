import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.database import get_db
import models.model as models

# Security Settings (Production me inhe .env me daal dena)
SECRET_KEY = "super_secret_finaudit_key_change_me_later"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 Days token validity

def get_password_hash(password: str):
    """Converts plain text into unreadable bcrypt hash using native bcrypt."""
    # 1. Strip spaces and limit to 72 chars (Bcrypt limitation bypass)
    clean_pw = password.strip()[:72]
    
    # 2. Bcrypt natively requires bytes, not strings
    pwd_bytes = clean_pw.encode('utf-8')
    salt = bcrypt.gensalt()
    
    # 3. Hash the password
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    
    # 4. Decode back to string so PostgreSQL can save it easily
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    """Checks if the user's entered password matches the DB."""
    # Clean the input password same as during registration
    clean_pw = plain_password.strip()[:72]
    
    # Convert both to bytes for comparison
    password_byte_enc = clean_pw.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    
    # Check if they match
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password_byte_enc)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generates the JWT Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    stmt = select(models.User).where(models.User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user