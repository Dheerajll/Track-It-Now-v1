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
    expires_at : datetime


class ParcelRequestData(BaseModel):
    receiver_email : str
    sender_location : tuple[float,float]
    parcel_description : str

class ParcelRequestAcceptData(BaseModel):
    request_id :int
    receiver_location : tuple[float,float]

