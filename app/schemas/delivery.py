from pydantic import BaseModel
from datetime import datetime

class DeliveryCreation(BaseModel):
    parcel_id : int
    agent_id : int

class DeliveryShow(BaseModel):
    id : int
    parcel_id :int
    agent_id :int
    assigned_time : datetime | None = None
    started_time : datetime | None = None
    completed_time : datetime | None = None
    created_at : datetime

class DeliveryInfo(BaseModel):
    agent_name : str
    tracking_code :str

