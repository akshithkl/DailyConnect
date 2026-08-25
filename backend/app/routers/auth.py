from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.deps import current_user
from app.models import Profile, User
from app.schemas import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, email=user.email, profile_photo=user.profile.profile_photo if user.profile else None, bio=user.profile.bio if user.profile else "")


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(or_(User.email == payload.email.lower(), User.username == payload.username.lower()))):
        raise HTTPException(status_code=409, detail="Username or email is already in use")
    user = User(username=payload.username, email=payload.email.lower(), hashed_password=hash_password(payload.password))
    user.profile = Profile(bio="")
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)), user=user_out(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return TokenOut(access_token=create_access_token(str(user.id)), user=user_out(user))


@router.post("/demo", response_model=TokenOut)
def demo_login(db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == "demo"))
    if not user:
        user = User(username="demo", email="demo@dailyconnect.app", hashed_password=hash_password("DailyConnectDemo!2026"))
        user.profile = Profile(bio="DailyConnect demo account")
        db.add(user)
        db.commit()
        db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)), user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user_out(user)
