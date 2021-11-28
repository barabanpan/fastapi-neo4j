import os
import uuid
import shutil
from datetime import datetime

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile

from src.auth.services import get_current_active_user, create_password_hash, verify_password
from src.core.db import neo4j_driver
from src.core.schemas import GUID
from src.users.schemas import User, UserChangePassword, UserInDB, UserUpdate


router = APIRouter()


@router.get("/me", response_model=User)
async def my_profile(current_user: User = Depends(get_current_active_user)):
    """GET Current user's information."""
    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    user_change_pass: UserChangePassword,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Change User's password."""
    old_password, new_password = user_change_pass.old_password, user_change_pass.new_password
    old_password_hash = current_user.hashed_password
    user_id = current_user.id

    """Checking if user entered correct old_password, if not - raise 400."""
    if not verify_password(old_password, old_password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong old_password was provided"
        )

    new_password_hash = create_password_hash(new_password)
    query_change_password = """
        MATCH (user:User) WHERE user.id = $user_id
        SET user.hashed_password = $new_password_hash
        RETURN user
    """

    with neo4j_driver.session() as session:
        """Changing password with a new one."""
        session.run(query_change_password, user_id=user_id, new_password_hash=new_password_hash)

    return {"detail": "Password successfully updated"}



@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Write Cypher query and run against the database."""
    query = "MATCH (user:User) WHERE user.id = $user_id RETURN user"

    with neo4j_driver.session() as session:
        user_in_db = session.run(query=query, parameters={"user_id": user_id})
        try:
            user_data = user_in_db.data()[0]["user"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Operation not permitted, user with id {user_id} doesn't exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    return User(**user_data)


@router.patch("/{user_id}")
async def update_profile(user_id: str, attributes: UserUpdate):
    """Add check to stop call if password is being changed."""
    attributes = dict(attributes)
    for k in attributes:
        if k == "hashed_password":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Operation not permitted, cannot update password with this method.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    if attributes:
        unpacked_attributes = (
            "SET " + ", ".join(f"user.{key}=\"{value}\"" for (key, value) in attributes.items() if value)
        )
    else:
        unpacked_attributes = ""

    """Execute Cypher query to reset the hashed_password attribute."""
    cypher_update_user = f"MATCH (user: User) WHERE user.id = $user_id {unpacked_attributes} RETURN user"

    with neo4j_driver.session() as session:
        updated_user = session.run(
            query=cypher_update_user,
            parameters={"user_id": user_id}
        )
        user_data = updated_user.data()[0]["user"]

    user = User(**user_data)
    return user
