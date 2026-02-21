from asyncpg.pool import Pool
from datetime import datetime,timedelta,timezone
from app.schemas.parcel_requests import ParcelRequest


'''
Before actually creating the parcel we send a parcel request from the 
sender to the receiver. This is done just to get the acknowledgement from
the receiver that they are ready to receive a parcel and also to get the 
location of the receiver.

'''

class ParcelRequestRepo:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool

    async def create_parcel_request(self,receiver_id:int,sender_id:int,parcel_description:str,sender_location:tuple):
        query ="""
        INSERT INTO parcel_requests(sender_id,receiver_id,expires_at,parcel_description,sender_location)
        VALUES ($1,$2,$3,$4,$5)
        RETURNING *;
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        try:
            async with self.pool.acquire() as conn:
                parcel_request = await conn.fetchrow(query,sender_id,receiver_id,expires_at,parcel_description,sender_location)
        except Exception as e:
            print(e)
        return ParcelRequest(**(dict(parcel_request)))
    
    async def update_parcel_request_status(self,request_id:int,status:str):
        query = """
        UPDATE parcel_requests 
        SET status = $1
        WHERE id = $2;
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query,status,request_id)
        if result == "UPDATE 0":
            return False
        else:
            return True
        
    async def get_all_pending_requests(self,receiver_id:int|None = None,sender_id:int|None = None):
        if sender_id:
            query = """
            SELECT * FROM parcel_requests
            WHERE status = 'pending' AND sender_id = $1;
            """
            async with self.pool.acquire() as conn:
                parcel_requests = await conn.fetch(query,sender_id)
            
            request_list = [dict(row) for row in parcel_requests]
            return {
                "requests":request_list 
            }
        if receiver_id:
            query = """
            SELECT * FROM parcel_requests
            WHERE status = 'pending' AND receiver_id = $1;
            """
            async with self.pool.acquire() as conn:
                parcel_requests = await conn.fetch(query,receiver_id)
            
            request_list = [dict(row) for row in parcel_requests]
            return {
                "requests":request_list 
            }
    async def get_request(self,request_id:int):
        query = """
        SELECT * FROM parcel_requests
        WHERE id = $1;
        """
        async with self.pool.acquire() as conn:
            parcel_request = await conn.fetchrow(query,request_id)
        
        return ParcelRequest(**dict(parcel_request))

        
