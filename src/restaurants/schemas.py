from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class RestaurantOptional(BaseModel):
    about: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    geo: Optional[str] = None
    email: Optional[str] = None
    cuisine: Optional[str] = None


# For update every parameter must be optional
class RestaurantUpdate(RestaurantOptional):
    name: Optional[str] = None


# For create name must be required
class RestaurantCreate(RestaurantOptional):
    name: str


class Restaurant(RestaurantCreate):
    id: str
    active: Optional[bool] = None
    created_at: Optional[datetime] = None
    image: Optional[str] = None


class RestaurantShortInfo(BaseModel):
    id: str
    name: str
    image: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "some-long-id-here-1",
                "name": "Branch Name 1",
                "image": "some/path/to/the/image1.jpg"
            }
        }
