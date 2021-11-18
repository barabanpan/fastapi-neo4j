from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, status, HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt, JWTError

from src.settings import settings
from src.core.db import neo4j_driver
from src.users.schemas import User, UserInDB


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.access_token_expire_minutes)


"""Generate password hash."""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, password_hash):
    return pwd_context.verify(plain_password, password_hash)


def check_user_exists(unique_attr: str):
    query_by_email = "MATCH (user:User) WHERE user.email = $email RETURN user"
    query_by_id = "MATCH (user:User) WHERE user.id = $user_id RETURN user"

    with neo4j_driver.session() as session:
        if "@" in unique_attr:
            user_in_db = session.run(query_by_email, email=unique_attr)
        else:
            user_in_db = session.run(query_by_id, user_id=unique_attr)
        if user_in_db.data():
            return True
        return False


def get_user(user: str):
    """Search the database for user.

     For sign-in, searching is by email.
     For function get_current_user, searching is by id.
     """
    query_id = "MATCH (user:User) WHERE user.id = $user_id RETURN user"
    query_email = "MATCH (user:User) WHERE user.email = $email RETURN user"

    with neo4j_driver.session() as session:
        if "@" in user:
            user_in_db = session.run(query_email, email=user)
        else:
            user_in_db = session.run(query_id, user_id=user)

        try:
            user_data = user_in_db.data()[0]["user"]
        except IndexError as err:
            print(f"Err: {err}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Operation not permitted, wrong id or email provided: '{user}'",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return UserInDB(**user_data)


def authenticate_user(email, password):
    """Authenticate user by checking they exist and that the password is correct."""
    user = get_user(email)
    if not user:
        return False

    """If present, verify password against password hash in database."""
    password_hash = user.hashed_password

    if not verify_password(password, password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(HTTPBearer())):
    """Decrypt the token and retrieve the user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(user=user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Check that current user is active and return the user."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
