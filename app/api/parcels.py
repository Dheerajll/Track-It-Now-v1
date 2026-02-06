from fastapi import APIRouter,Depends
from app.services.dependencies import get_parcel_service,get_current_active_user
from app.services.parcels import ParcelServices
from app.schemas.users import UserOut
from app.schemas.parcels import CreateParcel
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

@router.post("/status/update")
async def update_parcel_status(parcel_id:int,status:str,agent_user:UserOut=Depends(get_current_active_user),parcel_services:ParcelServices=Depends(get_parcel_service)):
    return await parcel_services.update_parcel_status_by_agent(parcel_id,status)