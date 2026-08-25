from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import current_user
from app.models import Profile, User
from app.schemas import ProfileUpdate, UserOut
from app.services.storage import public_url, upload_image
from app.routers.auth import user_out

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search", response_model=list[UserOut])
def search(q: str = "", db: Session = Depends(get_db)):
    users = db.scalars(select(User).where(User.username.ilike(f"%{q}%")).limit(20)).all()
    return [user_out(user) for user in users]


@router.get("/username/{username}", response_model=UserOut)
def by_username(username: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return user_out(user)


@router.put("/me", response_model=UserOut)
def update_profile(payload: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.profile.bio = payload.bio
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.post("/me/photo", response_model=UserOut)
async def update_photo(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.profile.profile_photo = await upload_image(file, f"profile_photos/user_{user.id}")
    db.commit()
    db.refresh(user)
    return user_out(user)
