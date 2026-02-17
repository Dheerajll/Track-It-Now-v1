from fastapi import APIRouter
from app.services.agent import search_for_agents,go_online
from fastapi import WebSocket


router = APIRouter(
    prefix="/agent",
    tags=["agents"]
)


@router.websocket("/go-online/{user_id}")
async def agent_go_online(user_id :str, websocket:WebSocket):
    token = websocket.query_params.get("token")
    if token:
        return await go_online(user_id,websocket,token)
    return {
        "message":"No token given in websocket query param"
    }

@router.websocket("/search-agents/{user_id}")
async def search_agents(user_id :str, websocket:WebSocket):
    token = websocket.query_params.get("token")
    lat = websocket.query_params.get("lat")
    lng = websocket.query_params.get("lng")
    if token:
            if lat is not None and lng is not None:
                return await search_for_agents(user_id=user_id,websocket=websocket,token=token,lat=float(lat),lng=float(lng))
            else:
                 return {
                      "message":"No query params"
                 }
    return {
        "message":"No token given in websocket query param"
    }
