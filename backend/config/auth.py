import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

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