import os
import uuid
import shutil
from datetime import datetime

from typing import List, Optional
from fastapi import APIRouter, Depends, Response, HTTPException, status

from src.core.db import neo4j_driver
from src.core.schemas import GUID, Message
from src.restaurants.schemas import Restaurant, RestaurantCreate, RestaurantUpdate
from src.restaurants.services import restaurant_with_this_name_exists


router = APIRouter()


@router.get("/", response_model=List[Restaurant])
async def get_list(name: Optional[str] = ""):
    """If name specified, uses searches restaurants by that exact name.<br/>
       If not, returns all the restaurants.
    """
    if name:
        query = """
           MATCH (res:Restaurant) WHERE res.name=$name
           RETURN res
        """
        with neo4j_driver.session() as session:
            restaurant_in_db = session.run(query=query, name=name)
            restaurant_data = restaurant_in_db.data()
    else:
        query = "MATCH (res:Restaurant) RETURN res"
        with neo4j_driver.session() as session:
            restaurant_in_db = session.run(query=query)
            restaurant_data = restaurant_in_db.data()

    restaurants = [Restaurant(**restaurant["res"]) for restaurant in restaurant_data]
    return restaurants


@router.post("/", response_model=GUID)
async def create_restaurant(new_restaurant: RestaurantCreate):
    restaurant_name = new_restaurant.name
    if restaurant_with_this_name_exists(restaurant_name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Restaurant with name \"{restaurant_name}\" already exists.")

    attributes = {
        "id": str(uuid.uuid4()),
        "created_at": str(datetime.utcnow()),
        "active": True
    }
    attributes.update(dict(new_restaurant))
    cypher_create = "CREATE (res:Restaurant $params) RETURN res"

    with neo4j_driver.session() as session:
        response = session.run(query=cypher_create, parameters={"params": attributes})
        try:
            restaurant_data = response.data()[0]["res"]
        except Exception as err:
            print(f"Err: {err}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error: '{err}'",
                headers={"WWW-Authenticate": "Bearer"}
            )
    restaurant = Restaurant(**restaurant_data)
    return {"id": restaurant.id}


@router.post("/{restaurant_id}/like", response_model=Message)
async def add_like(restaurant_id: str, user_id: str, add: bool):
    """If add==True, create LIKES relation between user and restaurant.<br/>
       If add==False, delete existing LIKES relation.<br/>
       If there is no existing LIKES relation, return 404 status code.
    """
    if add:
        query = """
            MATCH (u:User) WHERE u.id=$user_id
            MATCH (res:Restaurant) WHERE res.id=$restaurant_id
            CREATE (u)-[r:LIKES]->(res)
            RETURN r
        """
    else:
        query = """
            MATCH (u)-[r:LIKES]->(res)
            WHERE u.id=$user_id AND res.id=$restaurant_id
            DELETE r
            RETURN u
        """
    with neo4j_driver.session() as session:
        response = session.run(query=query, user_id=user_id, restaurant_id=restaurant_id)
        restaurant_data = response.data()
    if not restaurant_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request data not found"
        )

    return {"message": "Updated"}


@router.get("/{restaurant_id}", response_model=Restaurant)
async def get_one(restaurant_id):
    query = "MATCH (res:Restaurant) WHERE res.id = $restaurant_id RETURN res"

    with neo4j_driver.session() as session:
        restaurant_in_db = session.run(query=query, parameters={"restaurant_id": restaurant_id})
        restaurant_data = restaurant_in_db.data()

    if not restaurant_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request data not found"
        )
    return Restaurant(**restaurant_data[0]["res"])


@router.patch("/{restaurant_id}", response_model=Restaurant)
async def update_restaurant(restaurant_id, new_attrs: RestaurantUpdate):
    """Execute Cypher query to update Restaurant attributes"""
    attributes_string = ", ".join(f"res.{key}=\"{value}\"" for (key, value) in dict(new_attrs).items() if value)
    unpacked_attributes = "SET " + attributes_string
    if unpacked_attributes == "SET ":
        unpacked_attributes = ""

    cypher_update = ("MATCH (res: Restaurant) WHERE res.id = $restaurant_id\n"
                     f"{unpacked_attributes}\n"
                     "RETURN res")
    with neo4j_driver.session() as session:
        updated_restaurant = session.run(query=cypher_update, parameters={"restaurant_id": restaurant_id})
        restaurant_data = updated_restaurant.data()

    if not restaurant_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request data not found"
        )
    restaurant = Restaurant(**restaurant_data[0]["res"])
    return restaurant


@router.delete("/{restaurant_id}")
async def delete_restaurant(restaurant_id):
    """Execute Cypher query to make Restaurant inactive."""
    cypher_update = ("MATCH (res: Restaurant) WHERE res.id = $restaurant_id\n"
                     "SET res.active=False\n"
                     "RETURN res")
    with neo4j_driver.session() as session:
        updated_restaurant = session.run(query=cypher_update, parameters={"restaurant_id": restaurant_id})
        restaurant_data = updated_restaurant.data()

    if not restaurant_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request data not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)