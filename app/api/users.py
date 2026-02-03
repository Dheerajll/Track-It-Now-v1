from fastapi import APIRouter,Response,Depends,Request,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.services.dependencies import get_user_service
from app.services.users import UserServices
from app.schemas.users import CreateUser
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register")
async def register(user:CreateUser,userservices:UserServices=Depends(get_user_service)):
    return  await userservices.register_user(user)

@router.post("/login")
async def login(response:Response,form:OAuth2PasswordRequestForm = Depends(),userservices:UserServices=Depends(get_user_service)):
    return await userservices.login_for_token(response,form)

@router.get("/refresh")
async def refresh(response:Response,request:Request,userservices:UserServices = Depends(get_user_service)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401,detail="No refresh token received.")
    return await userservices.access_token_refresh(response,token)