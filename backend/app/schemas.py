from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    profile_photo: str | None = None
    bio: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    bio: str = Field(default="", max_length=500)


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    created_at: datetime
    user: UserOut


class PostOut(BaseModel):
    id: int
    image_url: str
    caption: str
    created_at: datetime
    username: str
    profile_photo: str | None
    like_count: int
    comment_count: int
    liked_by_me: bool


class ConversationCreate(BaseModel):
    user_id: int


class MessageOut(BaseModel):
    id: int
    sender_id: int
    text: str
    image_url: str | None
    created_at: datetime


class MessageCreate(BaseModel):
    text: str = Field(default="", max_length=5000)
