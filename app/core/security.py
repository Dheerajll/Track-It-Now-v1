from pwdlib import PasswordHash
from app.core.config import settings
from datetime import datetime,timezone,timedelta
from jwt.exceptions import PyJWTError
import jwt


'''
Class to manage password hashing and verification
'''
#creating the instance of password hasher 
pwd_hasher = PasswordHash.recommended()

class PasswordManager:
    def __init__(self) -> None:
        self.pwd_hasher = pwd_hasher

    def hashed_password(self,password:str):
        return self.pwd_hasher.hash(password)
    
    def verify_password(self,plain_password:str,hashed_password:str):
        return self.pwd_hasher.verify(plain_password,hashed_password)
    
'''
Class to manage the tokens:
'''
class TokenManager:
    def __init__(self) -> None:
        pass

    '''
    To create jwt access token for authentication
    '''
    def create_access_token(self,user_data:dict):
        to_encode = user_data.copy()
        expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
        to_encode.update({'exp':expiry})

        try:
            encoded_jwt = jwt.encode(user_data,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
            return encoded_jwt
        except PyJWTError as e:
            raise e #to raise if any error occur during token encoding
        
    '''
    To create a refresh token which will be used to recreate the access token
    when the token expires, refresh token are used for longer session without 
    having to repeatedly login everytime access token expires as they have short
    TTL.
    '''
    def create_refresh_token(self,user_data:dict):
        to_encode = user_data.copy()
        expiry = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRY)
        to_encode.update({'exp':expiry})

        try:
            encoded_jwt = jwt.encode(user_data,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
            return encoded_jwt
        except PyJWTError as e:
            raise e #to raise if any error occur during token encoding
        
    def decode_token(self,token:str):
        try:
            payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
            return payload
        except PyJWTError as e:
            raise e #to raise if any error occur during token decoding
    
'''
Creating the instances of the managers
'''
password_manager = PasswordManager()
token_manager = TokenManager()

    
