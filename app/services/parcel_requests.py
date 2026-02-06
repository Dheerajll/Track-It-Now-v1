from app.database.repository.parcel_requests import ParcelRequestRepo
from app.database.repository.users import UsersRepo
from app.schemas.users import UserOut
from fastapi import HTTPException,status
from app.schemas.parcel_requests import ParcelRequest
from app.schemas.parcels import CreateParcel
from app.services.parcels import ParcelServices
import json


class ParcelRequestService:
    def __init__(self,parcelrequestrepo:ParcelRequestRepo,usersrepo:UsersRepo,parcel_service:ParcelServices) -> None:
        self.request_repo = parcelrequestrepo
        self.users_repo = usersrepo
        self.parcel_service = parcel_service
    
    async def create_parcel_request(self,sender:UserOut,receiver_email:str,sender_location:tuple[float,float],parcel_description:str):
        try:
            receiver = await self.users_repo.get(email=receiver_email)
            if receiver:
                new_request = await self.request_repo.create_parcel_request(receiver.id,sender.id,parcel_description,sender_location)
            
            return new_request
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while creating a parcel request. {e} ")
        
    async def parcel_request_accept(self,request_id:int,user:UserOut,receiver_location:tuple[float,float]):
        try:
            request = await self.request_repo.get_request(request_id)
            if request.receiver_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed to accept parcel request.")
                    

            updated = await self.request_repo.update_parcel_request_status(request_id,"accepted")

            '''
            Parcel points
            '''
            source = request.sender_location
            destination = receiver_location

            '''
            Parcel description
            '''
            description = request.parcel_description

            parcel = CreateParcel(
                source=source,
                destination=destination,
                sender_id=request.sender_id,
                receiver_id=user.id,
                description=description
            )

            await self.parcel_service.create_parcel(parcel)

        except Exception as e:
            raise HTTPException(status_code=500,detail="Error while accepting parcel request.")
    
    async def parcel_request_decline(self,request_id:int, user:UserOut):
        try:
            request = await self.request_repo.get_request(request_id)
            if request_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed to accept parcel request.")
            
            updated = await self.request_repo.update_parcel_request_status(request_id,"declined")

            return {
                "message":"Parcel request declined"
            }
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while declining parcel request. {e}")





                

    
