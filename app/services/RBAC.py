from app.services.dependencies import get_current_active_user
from app.schemas.users import UserOut
from fastapi import Depends,HTTPException


def required_roles(roles:list[str]):
    def role_checker(user:UserOut=Depends(get_current_active_user))->UserOut:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="No permission to access."
            )
        return user
    return role_checker
