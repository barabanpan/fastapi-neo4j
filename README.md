# fastapi-neoj4-docker-api
FastAPI and Neo4j API

Provides user API with registration.
Also has a list of restaurants that users can 'like'.

# RUN
1. Install docker and docker-compose
2. ```docker-compose up```
3. Open [http://128.0.0.1:8000/docs](http://128.0.0.1:8000/docs).

# CLOSE
1. ```docker-compose down```

# TODOs:
1. Add route GET /users/liked-restaurants
2. Add route POST /users/{id1}/befriend/{id2} to make FRIENDS relationship
3. Add route GET /users/recommendation by what friends liked (for authenticated users)
4. Add sending emails at registration
