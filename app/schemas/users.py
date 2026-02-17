from pydantic import BaseModel


'''
Pydantic models for Users
'''
class User(BaseModel):
    id:int
    name:str
    email:str
    password:str
    role:str
    is_active:bool

class UserOut(BaseModel):
    id:int
    name:str
    email:str
    role:str
    is_active:bool

    class Config:
        extra = "ignore"

class CreateUser(BaseModel):
    name:str
    email:str
    password:str
    role:str
   

