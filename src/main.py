import time

from fastapi import FastAPI, Request, Depends
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from src.core.routes import router as core_router
from src.restaurants.routes import router as restaurant_router


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
]


app = FastAPI(
    title="Recommender System API",
    description="Recommender System API built with FastAPI & Neo4j",
    version="0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    middleware=middleware,
    debug=True,
)


app.include_router(
    core_router,
    tags=["Core"]
)


app.include_router(
    restaurant_router,
    prefix="/restaurants",
    tags=["Restaurants"]
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.on_event("startup")
async def startup() -> None:
    print("Waiting for Neo4j...")
    time.sleep(10)

