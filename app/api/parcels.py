from fastapi import APIRouter,Depends
from app.services.dependencies import get_parcel_service,get_current_active_user,get_parcel_requests_service
from app.services.parcels import ParcelServices
from app.services.parcel_requests import ParcelRequestService
from app.schemas.users import UserOut
from app.schemas.parcel_requests import ParcelRequestData,ParcelRequestAcceptData
from app.services.RBAC import required_roles
from fastapi import WebSocket
from app.services.parcel_requests import send_notification,receive_notification


router = APIRouter(
    prefix="/parcel",
    tags=["parcel"]
)

'''
This is test route we truly never create parcel from here
after thinking about it I planned using a ParcelRequest table from
where we will manage the parcels status and only create the parcel when 
the status is "accepted"
'''
# @router.post("/create")
# async def create_parcel(parcel:CreateParcel,user:UserOut=Depends(get_current_active_user),parcel_services:ParcelServices=Depends(get_parcel_service)):
#     return await parcel_services.create_parcel(parcel,user.id)

'''
We managed the permissions using the required roles dependencies from RBAC.py
'''



@router.post("/request")
async def create_parcel_request(request_info:ParcelRequestData,sender:UserOut=Depends(required_roles(["customer"])),parcel_request_service:ParcelRequestService=Depends(get_parcel_requests_service)):
    '''
    This should be only be permitted to customers
    '''
    return await parcel_request_service.create_parcel_request(sender,request_info.receiver_email,request_info.sender_location,request_info.parcel_description)

@router.post("/accept")
async def parcel_request_accept(accept_params:ParcelRequestAcceptData,receiver:UserOut=Depends(required_roles(["customer"])),parcel_request_service:ParcelRequestService=Depends(get_parcel_requests_service)):
    '''
    This should be only be permitted to customers
    '''
    return await parcel_request_service.parcel_request_accept(accept_params.request_id,receiver,accept_params.receiver_location)


@router.post("/decline")
async def parcel_request_decline(request_id:int,receiver:UserOut=Depends(required_roles(["customer"])),parcel_request_service:ParcelRequestService=Depends(get_parcel_requests_service)):
    '''
    This should be only be permitted to customers
    '''
    return await parcel_request_service.parcel_request_decline(request_id,receiver)


@router.post("/status/update")
async def update_parcel_status(parcel_id:int,status:str,agent_user:UserOut=Depends(required_roles(["agent"])),parcel_services:ParcelServices=Depends(get_parcel_service)):
    '''
    This should only be permitted to agents
    '''
    return await parcel_services.update_parcel_status_by_agent(parcel_id,status)

@router.get("/get-request")
async def get_request(request_id:int,customer:UserOut=Depends(required_roles(["customer"])),parcel_request_service:ParcelRequestService=Depends(get_parcel_requests_service)):
    return await parcel_request_service.get_request_by_id(request_id)


@router.get("/sent-requests")
async def sent_requests(parcel_request_services:ParcelRequestService=Depends(get_parcel_requests_service),sender:UserOut = Depends(get_current_active_user)):
    return await parcel_request_services.sent_parcel_requests(sender.id)


@router.get("/received-requests")
async def received_requests(parcel_request_services:ParcelRequestService=Depends(get_parcel_requests_service),receiver:UserOut = Depends(get_current_active_user)):
    return await parcel_request_services.received_parcel_requests(receiver.id)


@router.get("/parcels")
async def get_parcels(created:bool=True,received:bool=False,user:UserOut=Depends(required_roles(["customer"])),parcel_services:ParcelServices=Depends(get_parcel_service)):
    if created and not received:
        return await parcel_services.get_created_parcel(user.id)
    if received and not created:
        return await parcel_services.get_parcel_to_receive(user.id)
    

@router.get("/read")
async def get_a_only_parcel(parcel_id :int,user:UserOut=Depends(required_roles(["customer"])),parcel_services:ParcelServices=Depends(get_parcel_service)):
    return await parcel_services.get_a_parcel(parcel_id)
   
'''
To send and receive the notifications about
parcel requests we will use websockets
'''
@router.websocket("/send_notification/{user_id}")
async def notify_receiver(websocket:WebSocket,user_id:str):
    token = websocket.query_params.get("token")
    if token:
        return await send_notification(websocket,user_id,token)
    return {
        "message":"No token given in websocket query param"
    }


@router.websocket("/receive_notification/{user_id}")
async def get_notification(websocket:WebSocket,user_id:str):
    token = websocket.query_params.get("token")
    if token:
        return await receive_notification(websocket,user_id,token)
    return {
        "message":"No token given in websocket query param"
    }