from pydantic import BaseModel
from datetime import datetime

class ParcelRequest(BaseModel):
    id :int
    sender_id :int
    receiver_id :int
    status : str  # status should only have "accepted", "pending" ,"declined" and "expired"(optional)
    parcel_description : str
    sender_location : tuple[float,float]
    created_at : datetime
    expired_at : datetime


