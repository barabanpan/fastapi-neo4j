from neo4j import GraphDatabase

from src.settings import settings

uri = settings.neo4j_uri
username = settings.neo4j_username
password = settings.neo4j_password
neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))
