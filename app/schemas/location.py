from pydantic import BaseModel
from datetime import datetime
class Location(BaseModel):
    lat : float
    lng : float
    timestamp : datetime