from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from config.database import get_db
import models.model as models
from schemas.user_schema import UserRegister
from config.auth import get_password_hash, verify_password, create_access_token
from config.logger import logger

router = APIRouter()

@router.post("/register")
async def register_user(user: UserRegister, db: AsyncSession = Depends(get_db)):
    logger.info(f"Registering new user: {user.email}")
    
    stmt = select(models.User).where(models.User.email == user.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    await db.commit()
    
    return {"message": "User created successfully! You can now log in."}

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Swagger ka 'username' field yahan tera 'email' ban jayega
    user_email = form_data.username 
    user_password = form_data.password
    
    # Yahan 'user.email' ki jagah 'user_email' aayega
    logger.info(f"Login attempt for: {user_email}")
    
    # DB query mein bhi updated variable use hoga
    stmt = select(models.User).where(models.User.email == user_email)
    result = await db.execute(stmt)
    db_user = result.scalars().first()

    # Password verify karne ke liye bhi 'user_password' use hoga
    if not db_user or not verify_password(user_password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": db_user.id,
        "username": db_user.username
    }