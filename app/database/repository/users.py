from fastapi import Depends
from app.database.session import get_pool
from app.schemas.users import CreateUser,User,UserOut
from asyncpg.pool import Pool




'''
User repository that performs the crud for users.
'''
class UsersRepo:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool

    #CREATE
    async def create(self,user:CreateUser):
        query = """
        INSERT INTO users (name,email,password,role)
        VALUES ($1,$2,$3,$4)
        RETURNING *;
        """
        async with self.pool.acquire() as conn:
            new_user = await conn.fetchrow(query,user.name,user.email,user.password,user.role)
        return UserOut(**dict(new_user))
    #READ
    async def get(self,email:str):
        query="""
            SELECT * FROM users
            WHERE email = $1;
        """
        async with self.pool.acquire() as conn:
           
            user = await conn.fetchrow(query,email)
            #Returns none is found nothing.
            if user is None:
                return None
            return User(**dict(user))
    async def get_by_id(self,user_id:int):
        query="""
            SELECT * FROM users
            WHERE id = $1;
        """
        async with self.pool.acquire() as conn:
           
            user = await conn.fetchrow(query,user_id)
            #Returns none is found nothing.
            if user is None:
                return None
            return UserOut(**dict(user))
        
    #UPDATE
    async def update_status(self,email:str,status:bool):
        query="""
            UPDATE users SET  is_active = $1
            WHERE email = $2;
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(query,status,email)
            if result == "UPDATE 0":
                return False
            else:
                return True
    #DELETE
    async def delete(self,email:str):
        query="""
            DELETE FROM  users
            WHERE email = $2;
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(query,email)
            if result == "DELETE 0":
                return False
            else:
                return True


    
