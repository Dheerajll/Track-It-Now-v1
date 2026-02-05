from pydantic import BaseModel
from datetime import datetime



class ParcelPoints(BaseModel):
    source : tuple[float,float] # tuple of source (lat,long) 
    destination : tuple[float,float] # tuple of destination (lat,long)
class CreateParcel(ParcelPoints):
    sender_id : int
    receiver_id : int 
    current_status : str
    '''
    'created' , 'assigned' , 'picked_up' , 'in_transit' , 'delivered'
    '''

class ShowParcel(BaseModel):
    id : int
    sender_id : int
    receiver_id : int 
    current_status : str
    '''
    'created' , 'assigned' , 'picked_up' , 'in_transit' , 'delivered'
    '''
    created_at : datetime
    updated_at : datetime
    source : tuple[float,float]
    destination : tuple[float,float]

class Parcel(ShowParcel):
    pass

