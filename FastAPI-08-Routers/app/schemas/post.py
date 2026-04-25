from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    user_id: int


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    id: int
    user_id: int
    date_posted: datetime
    author: UserResponse

    model_config = {"from_attributes": True}

