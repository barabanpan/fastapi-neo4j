from src.core.db import neo4j_driver


def restaurant_with_this_name_exists(name):
    query = "MATCH (res:Restaurant) WHERE res.name=$name RETURN res"

    with neo4j_driver.session() as session:
        restaurant_in_db = session.run(query=query, name=name)
        restaurant_data = restaurant_in_db.data()

    return bool(restaurant_data)
