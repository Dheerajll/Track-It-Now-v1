from asyncpg.pool import Pool
from app.schemas.parcels import CreateParcel,Parcel,ShowParcel
class ParcelRepo:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool
    
    #CREATE
    '''
    This main thing to be aware while creating a parcel is that we also need to
    create a parcel points for this 
    '''
    async def create_parcel(self,parcel:CreateParcel):
        parcel_create_query= """
        INSERT INTO parcels (sender_id,receiver_id,description)
        VALUES ($1,$2,$3)
        RETURNING *;
        """   
        parcel_point_query ="""
        INSERT INTO parcel_points(parcel_id,source,destination)
        VALUES ($1,$2,$3)
        RETURNING *;
        """
        async with self.pool.acquire() as conn:
            '''
            Creating the parcel first.
            '''
            parcel_row = await conn.fetchrow(parcel_create_query,parcel.sender_id,parcel.receiver_id,parcel.description)

            '''
            Making the parcel points.
            '''                                                   #from db#
            parcel_point = await conn.fetchrow(parcel_point_query,parcel_row["id"],parcel.source,parcel.destination)

            '''
            Making the returning model of parcel
            '''
            parcel_out  = ShowParcel(
                id=parcel_row.get("id"),
                sender_id=parcel_row["sender_id"],
                receiver_id=parcel_row["receiver_id"],
                current_status=parcel_row["current_status"],
                description=parcel_row["description"],
                created_at=parcel_row["created_at"],
                updated_at=parcel_row["updated_at"],
                source=parcel_point["source"],
                destination=parcel_point["destination"]

            )
        return parcel_out
    #UPDATE
    async def update_parcel_status(self,parcel_id:int,status:str):
        query = """
        UPDATE parcels 
        SET current_status = $1
        WHERE id = $2;
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(query,status,parcel_id)
        if result == "UPDATE 0":
            return False
        else:
            return True
    #DELETE
    async def delete_parcel(self,parcel_id:int):
        query = """
        DELETE FROM parcels
        WHERE id = $1;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query,parcel_id)
    
