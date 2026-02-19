from fastapi import HTTPException
from app.database.repository.parcels import ParcelRepo
from app.database.repository.trackingcode import TrackingCodeRepo
from app.schemas.parcels import CreateParcel
from app.services.websockets import RNmanager

class ParcelServices:
    def __init__(self,parcelrepo:ParcelRepo,tracking_repo:TrackingCodeRepo) -> None:
        self.parcelrepo = parcelrepo
        self.tracking_repo = tracking_repo

    async def create_parcel(self,parcel:CreateParcel):
        try:
            return await self.parcelrepo.create_parcel(parcel)
        
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
        
            #updated =  await self.parcelrepo.update_parcel_status(parcel_id,status)
            '''
            To notify the sender and receiver about the updated status of the parcel
            '''
            updated_parcel = await self.parcelrepo.get_one_parcel(parcel_id)
            sender_id = str(updated_parcel.sender_id)
            receiver_id = str(updated_parcel.receiver_id)
            #if updated:
                #Notification about parcel status change.
            message = {
                "type" : "parcel-status-changed",
                "message" : f"Parcel {parcel_id}'s state changed to {status}",
                "parcel_id" :parcel_id,
                "status" : status
            }

            #To receiver
            await RNmanager.send_message(message=message,receiver_id=receiver_id)

            #To sender 
            await RNmanager.send_message(message=message,receiver_id=sender_id)
            return {
                "message" : "Status updated."
            }
            # else:
            #      return {
            #         "message" : "Status couldn't be updated."
            #     }
            
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while updating parcel status. {e}")
        
    async def get_created_parcel(self,user_id:int):
        try:
            return await self.parcelrepo.get_created_parcel(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while fetching created parcels. {e}"
            )
    async def get_parcel_to_receive(self,user_id:int):
        try:
            return await self.parcelrepo.get_parcel_to_receive(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while fetching parcels to receive. {e}"
            )
    async def get_a_parcel(self,parcel_id:int):
        try:
            return await self.parcelrepo.get_one_parcel(parcel_id)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while fetching a parcel. {e}"
            )
        
    async def delivery_completed(self,parcel_id:int,tracking_code:str):
        try:
        
            updated =  await self.parcelrepo.update_parcel_status(parcel_id,"delivered")
            '''
            To notify the sender and receiver about the updated status of the parcel
            '''
            updated_parcel = await self.parcelrepo.get_one_parcel(parcel_id)
            sender_id = str(updated_parcel.sender_id)
            receiver_id = str(updated_parcel.receiver_id)


            '''
            Delete the tracking code now that delivery has been completed.
            '''
            await self.tracking_repo.delete_tracking_code(track_code=tracking_code)

            if updated:
                #Notification about parcel status change.
                message = {
                    "type" : "parcel-status-changed",
                    "message" : f"Parcel {parcel_id}'s state changed to delivered",
                    "parcel_id" :parcel_id,
                    "status" : "delivered"
                }

                #To receiver
                await RNmanager.send_message(message=message,receiver_id=receiver_id)

                #To sender 
                await RNmanager.send_message(message=message,receiver_id=sender_id)
                return {
                    "message" : "Status updated."
                }
            else:
                return {
                    "message" : "Status couldn't be updated."
                }
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while updating parcel status. {e}")

        



