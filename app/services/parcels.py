from fastapi import HTTPException
from app.database.repository.parcels import ParcelRepo
from app.schemas.parcels import CreateParcel

class ParcelServices:
    def __init__(self,parcelrepo:ParcelRepo) -> None:
        self.parcelrepo = parcelrepo

    async def create_parcel(self,parcel:CreateParcel,sender_id:int):
        try:
            return await self.parcelrepo.create_parcel(parcel,sender_id)
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while creating parcel. {e}")
    
    async def update_parcel_status_by_agent(self,parcel_id:int,status:str):
        '''
        Later we have to add role specific access to this method
        such that only "agent" can access this
        '''
        status_list = ("created","assigned","picked_up","in_transit","delivered")

        if status not in status_list:
            raise HTTPException(status_code=400,detail="Bad request, no such parcel status.")
        
        try:
        
            updated =  await self.parcelrepo.update_parcel_status(parcel_id,status)
            if updated:
                return {
                    "message" : "Status updated."
                }
            else:
                 return {
                    "message" : "Status couldn't be updated."
                }
            
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while updating parcel status. {e}")



