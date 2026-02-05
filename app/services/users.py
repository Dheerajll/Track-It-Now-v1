from fastapi import HTTPException,status,Response
from fastapi.responses import JSONResponse
from app.schemas.users import CreateUser,UserOut
from app.schemas.tokens import Token,TokenData
from fastapi.security import OAuth2PasswordRequestForm
from app.database.repository.users import UsersRepo
from app.core.security import password_manager,token_manager
from app.database.redis_init import redis_client
import asyncpg





'''
Class to handle to user services
'''
class UserServices:
    def __init__(self,usersrepo:UsersRepo) -> None:
        self.credential_exception =HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"}
)
        self.usersrepo = usersrepo

    async def register_user(self,user:CreateUser):
        try:
            user.password = password_manager.hashed_password(user.password)
            new_user= await self.usersrepo.create(user)
            return UserOut(**dict(new_user))
        except asyncpg.UniqueViolationError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Username already exist.")
        


    async def _authenticate_user(self,username:str,password:str)->UserOut: 
        user =  await self.usersrepo.get(username)
        
        if user is None or not password_manager.verify_password(password,user.password):
            raise self.credential_exception
        return UserOut(**dict(user))

        

    async def login_for_token(self,response:Response,form:OAuth2PasswordRequestForm):
        username = form.username
        password = form.password

        user =  await self._authenticate_user(username,password)
        
        token_data = TokenData(
            id = user.id,
            name=user.name,
            email = user.email,
            role = user.role
        )
        try:
            access_token = token_manager.create_access_token(dict(token_data))
            refresh_token = token_manager.create_refresh_token(dict(token_data))

            '''
            Storing the refresh token in cookie, and redis memory which can be used
            to generate another access token 
            '''

            response = JSONResponse(content=dict(Token(access_token=access_token)))

            '''
            Setting refresh token in cookie
            '''
            response.set_cookie(
                key=f"refresh_token",
                value=refresh_token,
                samesite="lax",
                httponly=True,
                path="/"
            )

            '''
            Storing in redis memory
            '''
            await redis_client.set(f"refresh_token_{user.id}",refresh_token,ex=5*24*60*60)

            '''
            Updating the active status as the user will be active after logging in.
            '''
            await self.usersrepo.update_status(user.email,True)

            return response
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while creating jwt token, {e}")
        
        
    async def _verify_refresh_token(self,token:str):
        '''
        Verify the refresh token from the browser cookie to the one
        in the redis memory
        '''
        payload = token_manager.decode_token(token)
        user_id = payload.get("id")
        if not payload:
            raise HTTPException(status_code=401,detail="Invalid token.")
        
        '''
        We will compare the stored refresh token in redis with the received token
        '''
        stored_refresh_token = await redis_client.get(f"refresh_token_{user_id}")

        if stored_refresh_token == token:
            return payload
        else:
            raise HTTPException(status_code=401,detail=("Token invalid."))


    async def access_token_refresh(self,response:Response,token:str):
        payload = await self._verify_refresh_token(token)

        try:
            '''
            Now we create new access token and refresh token 
            '''
            access_token = token_manager.create_access_token(payload)
            new_refresh_token = token_manager.create_refresh_token(payload)

            #setting up the response
            response = JSONResponse(content=dict(Token(access_token=access_token)))

            '''
            Update the refresh token in the cookie and the redis memory
            '''
            user_id = payload.get("id")

            await redis_client.set(f"refresh_token_{user_id}",new_refresh_token)

            response.set_cookie(
                key=f"refresh_token",
                value=new_refresh_token,
                samesite="lax",
                httponly=True,
                path="/"
            )
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error while refreshing access token. {e}")

    async def logout_user(self,response:Response,user:UserOut):
        '''
        For logout, we remove the refresh token from the redis memory
        and cookie this will automatically 
        '''
        await redis_client.delete(f"refresh_token_{user.id}")

        response = JSONResponse(content={"message":"User logged out."})

        response.delete_cookie(
            key="refresh_token",
            samesite="lax",
            path="/"
        )
        '''
        Updating the status when user logs out
        '''
        await self.usersrepo.update_status(user.email,False)

        return response
    

    
       





