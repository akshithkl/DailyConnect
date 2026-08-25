from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import current_user
from app.models import Comment, Like, Post, User
from app.schemas import CommentCreate, CommentOut, PostOut
from app.services.storage import delete_image, public_url, upload_image

router = APIRouter(prefix="/api", tags=["posts"])


def serialize(post: Post, user_id: int, db: Session) -> PostOut:
    return PostOut(id=post.id, image_url=public_url(post.image_key) or "", caption=post.caption, created_at=post.created_at, username=post.user.username, profile_photo=public_url(post.user.profile.profile_photo if post.user.profile else None), like_count=db.scalar(select(func.count(Like.id)).where(Like.post_id == post.id)) or 0, comment_count=db.scalar(select(func.count(Comment.id)).where(Comment.post_id == post.id)) or 0, liked_by_me=db.scalar(select(Like.id).where(Like.post_id == post.id, Like.user_id == user_id)) is not None)


@router.post("/posts", response_model=PostOut, status_code=201)
async def create_post(caption: str = "", file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    post = Post(user_id=user.id, image_key=await upload_image(file, "posts"), caption=caption)
    db.add(post)
    db.commit()
    db.refresh(post)
    return serialize(post, user.id, db)


@router.get("/posts", response_model=list[PostOut])
def feed(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [serialize(post, user.id, db) for post in db.scalars(select(Post).order_by(Post.created_at.desc()).limit(50)).all()]


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    delete_image(post.image_key)
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/like", status_code=204)
def like(post_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(Post.id).where(Post.id == post_id)) and not db.scalar(select(Like.id).where(Like.post_id == post_id, Like.user_id == user.id)):
        db.add(Like(post_id=post_id, user_id=user.id)); db.commit()


@router.delete("/posts/{post_id}/like", status_code=204)
def unlike(post_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(Like).where(Like.post_id == post_id, Like.user_id == user.id)); db.commit()


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def comment(post_id: int, payload: CommentCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Comment(post_id=post_id, user_id=user.id, text=payload.text); db.add(item); db.commit(); db.refresh(item); return item


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def comments(post_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)).all()


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Comment, comment_id)
    if item and item.user_id == user.id: db.delete(item); db.commit()
