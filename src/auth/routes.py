from uuid import uuid4
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from email_validator import validate_email, EmailNotValidError

from src.core.db import neo4j_driver
from src.users.schemas import User, UserSignIn, UserSignInResponse, UserSignUp, UserResetPassword
from src.auth.services import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_password_hash, check_user_exists, authenticate_user, create_access_token,
)


router = APIRouter()


@router.post("/sign-up", status_code=status.HTTP_200_OK, response_model=User)
async def sign_up(new_user: UserSignUp):
    try:
        valid = validate_email(new_user.email)
        """Update with the normalized form."""
        email = valid.email
    except EmailNotValidError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Operation not permitted, wrong email address provided: {new_user.email}",
            headers={"WWW-Authenticate": "Bearer"}
        )

    attributes = {
        "id": str(uuid4()),
        "email": email,
        "hashed_password": create_password_hash(new_user.password),
        "joined": str(datetime.utcnow()),
        "is_active": True
    }

    query_create_new_user = "CREATE (user:User $attributes) RETURN user"
    with neo4j_driver.session() as session:
        if check_user_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operation not permitted, user with email {email} already exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        new_user_create = session.run(query_create_new_user, attributes=attributes)
        new_user_data = new_user_create.data()[0]["user"]

    return User(**new_user_data)


@router.post("/sign-in", status_code=status.HTTP_200_OK, response_model=UserSignInResponse)
async def sign_in(user: UserSignIn):
    """Endpoint for token authentication."""
    user = authenticate_user(user.email, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires
    )
    login_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "expired_in": ACCESS_TOKEN_EXPIRE_MINUTES,
        "user_id": user.id
    }

    return UserSignInResponse(**login_data)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(user_reset_pass: UserResetPassword):
    """Reset User's password using user's email."""

    email, new_password = user_reset_pass.email, user_reset_pass.new_password
    try:
        valid = validate_email(email)
        """Update with the normalized form."""
        email = valid.email
    except EmailNotValidError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Not valid email address was provided: '{email}'"
        )

    query_reset_password = """
        MATCH (user:User) WHERE user.email = $email
        SET user.hashed_password = $new_password_hash
        RETURN user
    """
    with neo4j_driver.session() as session:
        """Checking if user exists, if not - raise 404."""
        if not check_user_exists(email):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        """Encrypt new password and update user's property."""
        new_password_hash = create_password_hash(new_password)
        session.run(query_reset_password, email=email, new_password_hash=new_password_hash)

    return {"detail": "Password successfully updated"}
