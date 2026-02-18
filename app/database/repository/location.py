from asyncpg.pool import Pool
from app.schemas.location import Location
class LocationRepo:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool

    async def add_location(self,agent_id:int,delivery_id:int,location:Location):
        query = """
        INSERT INTO location_table (agent_id,delivery_id,lat,lng,location_timestamp)
        VALUES ($1,$2,$3,$4,$5)
        RETURNING *;
        """
        
        async with self.pool.acquire() as conn:
            new_location = await conn.fetchrow(query,agent_id,delivery_id,location.lat,location.lng,location.timestamp)
        
    