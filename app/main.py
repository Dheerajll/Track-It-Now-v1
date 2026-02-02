from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import session


'''
This is a method which triggers certain functions
on the app startup and app shutdown. We will use this to initialize database 
connection pool and close the pool.
'''
@asynccontextmanager
async def lifespan(app:FastAPI):
    try:
        await session.connect()
    except Exception as e:
        print("Error on connecting database. ",e)
    yield

    try:
        await session.close()
    except Exception as e:
        print("Error on closing app. ",e)


app = FastAPI(lifespan=lifespan)


@app.get("/")
def home():
    return {
        "message":"Hello world."
    }