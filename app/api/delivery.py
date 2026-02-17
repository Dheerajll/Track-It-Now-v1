from fastapi import APIRouter,Depends
from app.services.dependencies import get_delivery_services
from app.services.RBAC import required_roles
from app.schemas.delivery import DeliveryCreation
from app.schemas.users import UserOut
from app.services.delivery_services import DeliveryServices
router = APIRouter(
    prefix="/delivery",
    tags=["delivery"]
)


@router.post("/assign")
async def assign_parcel(delivery_creation:DeliveryCreation,user:UserOut=Depends(required_roles(["customer"])),delivery_service:DeliveryServices = Depends(get_delivery_services)):
    return await delivery_service.assign_parcel(user,delivery_creation.agent_id,delivery_creation.parcel_id)