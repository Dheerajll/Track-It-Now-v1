from app.database.repository.parcel_requests import ParcelRequestRepo
from app.database.repository.users import UsersRepo
from app.schemas.users import UserOut
from fastapi import HTTPException,status
from app.schemas.parcel_requests import ParcelRequest
from app.schemas.parcels import CreateParcel
from app.services.parcels import ParcelServices
from fastapi import WebSocket,WebSocketDisconnect
from app.core.config import settings
import jwt
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

            return await self.parcel_service.create_parcel(parcel)

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

For notications using Websockets
'''


'''
At first we will create a simple websocket manager
'''
class RequestNotificationManager:
    def __init__(self) -> None:
        self.active_connections:dict[str,WebSocket] = {}
    
    async def connect(self,user_id:str,websocket:WebSocket):
        try:
            await websocket.accept()
            self.active_connections[user_id] = websocket
            print(f"User {user_id} connected to websocket")
        
        except Exception as e:
            print("Error while connecting to websocket." ,e)
    
    def disconnect(self,user_id:str):
        try:
            self.active_connections.pop(user_id,None)
            print(f"User {user_id} disconnect from websocket.")
        
        except Exception as e:
            print("Error while disconnecting from websocket. ",e)
        
    async def send_message(self, message:dict,receiver_id:str):
        try:
            receiver_ws = self.active_connections.get(receiver_id)

            if receiver_ws:
                await receiver_ws.send_json(message)
        except WebSocketDisconnect:
            self.disconnect(receiver_id)
        except Exception as e:
            print("Error while sending message. ",e)


'''
As websocket doesn't need dependencies we create the instance here
'''
RNmanager = RequestNotificationManager()
'''
We would use the exception class to 
authenticate the websocket users
as we can't use dependency on websocket
'''
class WebSocketAuthError(Exception):
    def __init__(self,code,reason)-> None:
        self.code = code
        self.reason = reason


'''
To decode the token
'''
def decode_token_for_websocket(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise WebSocketAuthError(code=1008,reason="Token expired")

    except jwt.InvalidTokenError:
        raise WebSocketAuthError(code=1008,reason="Invalid token")

    except Exception:
        raise WebSocketAuthError(code=1011,reason="Token decode failed")

def verify_token(token:str,role:str, sender_id :str):
    payload = decode_token_for_websocket(token)
    user_role = payload.get("role")
    user_id = payload.get("id")
    if user_role != role or user_id != sender_id:
        raise WebSocketAuthError(code=1008,reason="No permission")

async def send_notification(websocket:WebSocket,user_id:str,token:str):
    await RNmanager.connect(user_id,websocket)

    '''
    First we will connect the websocket initially
    '''
    try:
        verify_token(token,"customer",user_id)
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except ValueError as e:
                    print("Can't parce the given json. ",e)
                    continue

                #fetch the receiver id from the data 
                receiver_id = data["receiver_id"]

                new_message = {
                    "request_id" : data["receiver_id"],
                    "sender_name" : data["sender_name"],
                }   

                await RNmanager.send_message(new_message,receiver_id) 
        except (WebSocketDisconnect, Exception) as e:
            RNmanager.disconnect(user_id)
    except WebSocketAuthError as e:
        RNmanager.disconnect(user_id)
        await websocket.close(code = e.code,reason=e.reason)
    
    except Exception as e:
        print("Unexpected error: ",e)
        await websocket.close(code=1011,reason="Internal server error")
    
async def receive_notification(websocket:WebSocket,user_id:str,token:str):
    await RNmanager.connect(user_id,websocket)
    try:
        verify_token(token,"customer",user_id)
        try:
            while True:
                await websocket.receive()
        except (WebSocketDisconnect,Exception) as e:
            RNmanager.disconnect(user_id)
    except WebSocketAuthError as e:
        RNmanager.disconnect(user_id)
        await websocket.close(code=e.code,reason=e.reason)
    except Exception as e:
        print("Unexpected error: ",e)
        await websocket.close(code=1011,reason="Internal server error")

    
