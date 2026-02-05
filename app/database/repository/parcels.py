from asyncpg.pool import Pool
from app.schemas.parcels import CreateParcel,Parcel
class ParcelRepository:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool
    
    #CREATE
    async def create_parcel(self,parcel:CreateParcel):
        query = """
        INSERT INTO parcels (sender_id,receiver_id,current_status)
        VALUES ($1,$2,$3)
        RETURNING *;
        """   
        async with self.pool.acquire() as conn:
            parcel = await conn.fetchrow(query,parcel.sender_id,parcel.receiver_id,parcel.current_status)
        
        return parcel
    #UPDATE
    async def update_parcel_status(self,parcel:Parcel,status:str):
        query = """
        UPDATE parcels 
        SET current_status = $1
        WHERE id = $2;
        """
        async with self.pool.acquire() as conn:
            parcel = await conn.fetchrow(query,status,parcel.id)
        return parcel
    #DELETE
    async def delete_parcel(self,parcel:Parcel):
        query = """
        DELETE FROM parcels
        WHERE id = $1;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query,parcel.id)
    
