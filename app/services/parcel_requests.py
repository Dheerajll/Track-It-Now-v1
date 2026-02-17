from app.database.repository.parcel_requests import ParcelRequestRepo
from app.database.repository.users import UsersRepo
from app.schemas.users import UserOut
from fastapi import HTTPException,status
from app.schemas.parcel_requests import ParcelRequest
from app.schemas.parcels import CreateParcel
from app.services.parcels import ParcelServices
from app.services.websockets import RequestNotificationManager,verify_token,WebSocketAuthError
from fastapi import WebSocket,WebSocketDisconnect
from app.core.config import settings





'''
Creating instance of websocket manager that handles Request notification
'''
RNmanager = RequestNotificationManager()


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
            '''
            Sending notification to the receiver that parcel is created.
            We will do that by sending a message in the receiver's websocket.
            '''
            message = {
                "type" : "parcel_request",
                "message" : f"{sender.name} sent parcel request.",
                "request_id" : new_request.id,
            }

            '''
            we convert the receiver id into 
            into string as send_message expects string
            '''
            receiver_id = str(new_request.receiver_id)
            
            await RNmanager.send_message(message,receiver_id)

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

            created_parcel =  await self.parcel_service.create_parcel(parcel)

            
            '''
            Now to send a notification to the sender
            that the receiver has accepted the request 
            and parcel has been created.
            '''
            sender_id = str(created_parcel.sender_id)
            message = {
                "type" : "parcel_created",
                "sender_id" :created_parcel.sender_id,
                "parcel_id" : created_parcel.id,
                "message" : f"Your parcel to {user.name} has been created."
            }
            '''
            As the sender should receiver the notification
            '''
            await RNmanager.send_message(message,sender_id)

            return created_parcel

        except Exception as e:
            raise HTTPException(status_code=500,detail="Error while accepting parcel request.")
    
    async def parcel_request_decline(self,request_id:int, user:UserOut):
        try:
            request = await self.request_repo.get_request(request_id)
            if request.receiver_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed to decline parcel request.")
            
            updated = await self.request_repo.update_parcel_request_status(request_id,"declined")

            return {
                "message":"Parcel request declined"
            }
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Error while declining parcel request. {e}")
        
    async def sent_parcel_requests(self,sender_id:int):
        try:

            return await self.request_repo.get_all_pending_requests(sender_id=sender_id)
        except Exception as e:
            raise HTTPException(status_code=500,detail="Error while fetching sent requests.")
    async def received_parcel_requests(self,receiver_id:int):
        try:
            return await self.request_repo.get_all_pending_requests(receiver_id=receiver_id)
        except Exception as e:
            raise HTTPException(status_code=500,detail="Error while fetching received requests.")

    async def get_request_by_id(self,request_id : int):
        try:
            return await self.request_repo.get_request(request_id)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error while getting request by id. {e}")
'''

For notications using Websockets------------------------------------------------------------------------------------------------------------------------------------------------------------
'''
async def receive_notification(websocket:WebSocket,user_id:str,token:str):
    await RNmanager.connect(user_id,websocket)
    try:
        verify_token(token,["customer","agent"],user_id)

        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        pass

    except WebSocketAuthError as e:
        await websocket.close(code=e.code,reason=e.reason)

    except Exception as e:
        print("Unexpected error: ",e)
        await websocket.close(code=1011,reason="Internal server error")
    
    finally:
        '''
        Doing this after the all exception are passed.
        '''
        RNmanager.disconnect(user_id)
    

    
