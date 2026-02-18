from fastapi import APIRouter,WebSocket,Depends
from app.services.dependencies import get_location_repo
from app.database.repository.location import LocationRepo
from app.services.livelocation import start_live_share,listen_to_live_location
router = APIRouter(
    prefix="/track",
    tags=["track"]
)

@router.websocket("/{user_id}/{tracking_code}")
async def track_agent(user_id:str,tracking_code:str,websocket:WebSocket,location_repo:LocationRepo=Depends(get_location_repo)):
    token = websocket.query_params.get("token")
    if token:
        return await listen_to_live_location(user_id=user_id,websocket=websocket,token=token,location_repo=location_repo,tracking_code=tracking_code)
    
@router.websocket("/live-share/{user_id}/{tracking_code}")
async def share_your_location(user_id:str,tracking_code:str,websocket:WebSocket):
    token = websocket.query_params.get("token")
    if token:
        return await start_live_share(user_id=user_id,websocket=websocket,token=token,tracking_code=tracking_code)
    

