from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    joined: Optional[datetime] = None


class UserInDB(User):
    hashed_password: str


class UserSignIn(BaseModel):
    email: str
    password: str


class UserSignInResponse(BaseModel):
    access_token: str
    token_type: str
    expired_in: int
    user_id: str


class UserSignUp(UserSignIn):
    pass


class UserResetPassword(BaseModel):
    email: str
    new_password: str
