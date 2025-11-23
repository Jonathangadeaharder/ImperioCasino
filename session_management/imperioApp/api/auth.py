"""
Authentication API routes for FastAPI
Migrated from Flask routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from ..database import get_db
from ..utils.auth_fastapi import create_access_token, get_current_user, generate_token
from ..utils.models_fastapi import User
from ..utils.config import Config

router = APIRouter()
templates = Jinja2Templates(directory="imperioApp/templates")

# Pydantic models for request/response
class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenVerification(BaseModel):
    token: str
    username: str


# API Routes (for programmatic access)
@router.post("/api/login", response_model=Token)
async def api_login(user_data: UserLogin, db: Session = Depends(get_db)):
    """API endpoint for user login"""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = generate_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/api/signup", status_code=status.HTTP_201_CREATED)
async def api_signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """API endpoint for user registration"""
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create new user
    new_user = User(username=user_data.username, email=user_data.email)
    new_user.set_password(user_data.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "username": new_user.username}


@router.post("/api/verify-token")
async def api_verify_token(token_data: TokenVerification, db: Session = Depends(get_db)):
    """API endpoint to verify JWT token"""
    try:
        from ..utils.auth_fastapi import decode_token
        decoded_token = decode_token(token_data.token)
        user = db.query(User).filter(User.username == decoded_token['user_id']).first()
        
        if user:
            return {"message": "Token is valid"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or username"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Web Routes (for HTML templates - backward compatibility)
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Sign In",
        "form": {"username": "", "password": "", "remember_me": False}
    })


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render signup page"""
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "title": "Register",
        "form": {"username": "", "email": "", "password": ""}
    })


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Render dashboard page (requires authentication)"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "current_user": current_user
    })


@router.get("/redirect-imperio")
async def redirect_to_imperio(current_user: User = Depends(get_current_user)):
    """Redirect to Cherry Charm game with authentication token"""
    token = generate_token(current_user.username)
    return RedirectResponse(
        url=f"{Config.CHERRY_CHARM_URL}/?username={current_user.username}&token={token}"
    )


@router.get("/redirect-blackjack")
async def redirect_to_blackjack(current_user: User = Depends(get_current_user)):
    """Redirect to Blackjack game with authentication token"""
    token = generate_token(current_user.username)
    return RedirectResponse(
        url=f"{Config.BLACK_JACK_URL}/?username={current_user.username}&token={token}"
    )


@router.get("/redirect-roulette")
async def redirect_to_roulette(current_user: User = Depends(get_current_user)):
    """Redirect to Roulette game with authentication token"""
    token = generate_token(current_user.username)
    return RedirectResponse(
        url=f"{Config.ROULETTE_URL}/?username={current_user.username}&token={token}"
    )


@router.get("/logout")
async def logout():
    """Logout endpoint"""
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# Legacy route compatibility
@router.post("/verify-token")
async def verify_token_legacy(token_data: TokenVerification, db: Session = Depends(get_db)):
    """Legacy verify-token endpoint (without /api prefix)"""
    return await api_verify_token(token_data, db)
