from asyncpg.pool import Pool
from app.schemas.delivery import DeliveryShow,DeliveryShowToAgent


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
        SELECT d.id as id,d.parcel_id as parcel_id,
        d.agent_id as agent_id,d.assigned_time as assigned_time,
        d.started_time as started_time,
        d.completed_time as completed_time,
        d.created_at as created_at,
        p.description as parcel_description,
        pp.destination as parcel_destination
        FROM delivery_assignment d
        JOIN parcels p
        ON d.parcel_id = p.id
        JOIN parcel_points pp
        ON p.id = pp.parcel_id
        WHERE d.agent_id = $1;
        """
        async with self.pool.acquire() as conn:
            deliveries = await conn.fetch(query,agent_id)
        
        return [DeliveryShowToAgent(**dict(delivery)) for delivery in deliveries]


