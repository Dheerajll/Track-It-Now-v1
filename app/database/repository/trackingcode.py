from asyncpg.pool import Pool
from datetime import datetime,time,timezone
from app.schemas.trackingcode import ShowTrackCode
import uuid
def create_tracking_code(agent_id:int,parcel_id:int):
    '''
    Creating a tracking code
    '''
    # Date in YYMMDD format (UTC)
    date_part = datetime.now(timezone.utc).strftime("%y%m%d")
    trackcode = f"TRK-{uuid.uuid4().hex[:10].upper()}-{date_part}-{agent_id}{parcel_id}"

    return trackcode


class TrackingCodeRepo:
    def __init__(self,pool:Pool) -> None:
        self.pool = pool
    
    async def create_tracking_code(self,agent_id:int,parcel_id:int):
        query = """
        INSERT INTO trackingcode (agent_id,parcel_id,tracking_code)
        VALUES ($1,$2,$3)
        RETURNING tracking_code
        """

        async with self.pool.acquire() as conn:
            track_code = await conn.fetchrow(query,agent_id,parcel_id,create_tracking_code(agent_id,parcel_id))
        
        return track_code
    
    async def delete_tracking_code(self,track_code:str):
        query = """
        DELETE FROM trackingcode
        WHERE tracking_code = $1
        RETURNING tracking_code;
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query,track_code)
        
        return result is not None
        
        

