
from fastapi import APIRouter

from src.core.db import neo4j_driver
from src.core.schemas import Query


router = APIRouter()


@router.get(
    "/q",
    response_model=Query,
    summary="Query the database with a custom Cypher string"
)
async def cypher_query(cypher_string: str):
    with neo4j_driver.session() as session:
        response = session.run(query=cypher_string)
        query_response = Query(response=response.data())
        return query_response
