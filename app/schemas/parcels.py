from pydantic import BaseModel
from datetime import timezone
class CreateParcel(BaseModel):
    sender_id : int
    receiver_id : int 
    current_status : str
    '''
    'created' , 'assigned' , 'picked_up' , 'in_transit' , 'delivered'
    '''

class ShowParcel(CreateParcel):
   id : int
   created_at : timezone
   updated_at : timezone

class Parcel(ShowParcel):
    pass
