
from fastapi import APIRouter


router = APIRouter()


@router.get("/healthcheck")
def health_check():
    return {"status": "Ok"}
