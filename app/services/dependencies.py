from fastapi import Depends,HTTPException,status
from app.database.session import get_pool
from app.database.repository.users import UsersRepo
from app.database.repository.parcels import ParcelRepo
from app.database.repository.parcel_requests import ParcelRequestRepo
from app.database.repository.delivery_assignment import DeliveryRepo
from app.database.repository.trackingcode import TrackingCodeRepo
from app.services.parcel_requests import ParcelRequestService
from app.services.users import UserServices
from app.services.parcels import ParcelServices
from app.core.security import token_manager
from fastapi.security import OAuth2PasswordBearer
from app.schemas.users import UserOut

'''
Outh2 scheme will be used to make the routes and certain functions protected.
'''
outh2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

'''
Dependency to get users repo
'''
def get_user_repo(pool=Depends(get_pool))->UsersRepo:
    return UsersRepo(pool)

'''
Dependency to get users service
'''
def get_user_service(userrepo=Depends(get_user_repo))->UserServices:
    return UserServices(userrepo)


'''
Dependency to get parcels repo
'''
def get_parcel_repo(pool=Depends(get_pool)):
    return ParcelRepo(pool)


'''
Dependency to get parcels service
'''
def get_parcel_service(parcelrepo=Depends(get_parcel_repo)):
    return ParcelServices(parcelrepo)


'''
Dependency to get parcel_requests repo
'''
def get_parcel_requests_repo(pool=Depends(get_pool)):
    return ParcelRequestRepo(pool)


'''
Dependency to get parcel_requests service
'''

def get_parcel_requests_service(parcelrequestrepo=Depends(get_parcel_requests_repo),usersrepo=Depends(get_user_repo),parcel_service=Depends(get_parcel_service)):
    return ParcelRequestService(parcelrequestrepo,usersrepo,parcel_service)



'''
Dependency to get delivery_assignment repo
'''

def get_delivery_repo(pool=Depends(get_pool)):
    return DeliveryRepo(pool)


'''
Dependency  to get tracking code repo
'''
def get_tracking_code_repo(pool=Depends(get_pool)):
    return TrackingCodeRepo(pool)

'''
Dependency to get current user
'''
async def get_current_user(token:str=Depends(outh2_scheme),usersrepo:UsersRepo=Depends(get_user_repo)):
    try:
        payload = token_manager.decode_token(token)
        email = payload.get("email")
        if email:
            user =  await usersrepo.get(email=email)
            if user:
                return UserOut(**dict(user))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while getting current user. {e}")
    
'''
Dependency to get current active user
'''
async def get_current_active_user(current_user:UserOut=Depends(get_current_user)):
    if current_user.is_active:
        return current_user
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User not active.")
