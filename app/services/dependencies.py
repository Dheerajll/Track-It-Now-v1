from fastapi import Depends
from app.database.session import get_pool
from app.database.repository.users import UsersRepo
from app.services.users import UserServices


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

