from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import session
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import (users,parcels,agents,delivery)

'''
This is a method which triggers certain functions
on the app startup and app shutdown. We will use this to initialize database 
connection pool and close the pool.
'''

@asynccontextmanager
async def lifespan(app:FastAPI):
    try:
        await session.connect()
        print("Database connection formed.")
    except Exception as e:
        print("Error on connecting database. ",e)
    yield

    try:
        await session.close()
        print("Database connection closed.")
    except Exception as e:
        print("Error on closing app. ",e)


app = FastAPI(lifespan=lifespan)

'''
Setting up the CORS
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_ORIGINS, # just for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
Including the routers
'''
app.include_router(users.router,prefix="/api") # Router for users
app.include_router(parcels.router,prefix="/api") # Router for parcels
app.include_router(agents.router,prefix="/api") # Router for agents
app.include_router(delivery.router,prefix="/api") # Router for delivery


@app.get("/")
def home():
    return {
        "message":"Hello world."
    }