from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List
load_dotenv()
class Settings(BaseSettings):
    #Database:
    database_name :str 
    database_password :str
    database_user :str
    database_host :str
    database_port : int = 5432
    redis_url :str = "rediss://default:AaBjAAIncDI0N2EyNTdhNWU5ODg0ZTg2ODI2YTJjYWY3MDc1ODZmM3AyNDEwNTk@unified-jennet-41059.upstash.io:6379"

  

    #token secrets
    SECRET_KEY : str
    ACCESS_TOKEN_EXPIRY : int = 30 #minutes
    REFRESH_TOKEN_EXPIRY : int = 5 #days
    ALGORITHM : str = "HS256"

    #CORS origin for backend
    BACKEND_ORIGINS: List[str] = ['http://localhost:5173','http://localhost:5174','https://t767qx3z-5173.inc1.devtunnels.ms','https://trackitnow-parcel.vercel.app']


    class Config:
        env_file = ".env" #this is the env file from where the environment variables will be fetched
        case_sensitive = True

settings = Settings() #type:ignore


