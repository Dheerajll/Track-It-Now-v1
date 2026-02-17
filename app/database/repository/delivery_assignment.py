from asyncpg.pool import Pool
from app.schemas.delivery import DeliveryShow


class DeliveryRepo:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool
    
    async def create_delivery(self,parcel_id:int,agent_id:int):
        query = """
        INSERT INTO delivery_assignment(parcel_id,agent_id)
        VALUES ($1,$2)
        RETURNING *;
        """

        async with self.pool.acquire() as conn:
            new_delivery = await conn.fetchrow(query,parcel_id,agent_id)
        
        return DeliveryShow(**dict(new_delivery))
        
    async def get_deliveries(self,agent_id:int):
        query = """
        SELECT * FROM delivery_assignment
        WHERE agent_id = $1;
        """
        async with self.pool.acquire() as conn:
            deliveries = await conn.fetch(query,agent_id)
        
        return [DeliveryShow(**dict(delivery)) for delivery in deliveries]


