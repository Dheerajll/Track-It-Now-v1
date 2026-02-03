from pydantic import BaseModel

class Token(BaseModel):
    access_token :str 
    token_type :str = "Bearer"

class TokenData(BaseModel):
    id:int
    name:str
    email:str
    role:str