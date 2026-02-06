from pydantic import BaseModel
from datetime import datetime

class ParcelRequest(BaseModel):
    sender_id :int
    receiver_id :int
    status : str  # status should only have "accepted", "pending" ,"declined" and "expired(optional)"
    created_at : datetime
    expired_at : datetime


