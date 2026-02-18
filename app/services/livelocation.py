from app.services.websockets import LLManager,verify_token,WebSocketAuthError
from app.database.repository.location import LocationRepo
from app.database.repository.trackingcode import TrackingCodeRepo
from app.database.redis_init import redis_client
from fastapi import WebSocket,WebSocketDisconnect
import json
'''
Method for live sharing of agent location 
'''
async def start_live_share(user_id:str,websocket:WebSocket,token:str,tracking_code:str):
    await LLManager.connect(user_id,websocket)
    try:
        verify_token(token=token,role=["agent"],sender_id=user_id)
        while True:
            try:
                data = await websocket.receive_json()
            
            except (ValueError,KeyError) as e:
                print("Invalid json format received.")
                continue

            '''
            Publish the message to the given tracking code channel
            '''
            await redis_client.publish(tracking_code,json.dumps(data))

    
    except WebSocketAuthError as e:
        await websocket.close(code=e.code,reason=e.reason)

    except WebSocketDisconnect :
        pass

    except Exception as e:
        print("Error while making sharing live location ",e)
        await websocket.close(code=1011,reason="Internal server error.")
        
    finally:
        LLManager.disconnect(user_id)
    

async def listen_to_live_location(user_id:str,websocket:WebSocket,token:str,location_repo:LocationRepo,tracking_code:str,tracking_repo:TrackingCodeRepo):
    await LLManager.connect(user_id,websocket,location_repo,tracking_code)
    try:
        verify_token(token=token,role=["customer"],sender_id=user_id)
        '''
        To verify validity of tracking code.
        '''
        tracking_code_fetched = await tracking_repo.get_tracking_code(tracking_code=tracking_code)
        if not tracking_code_fetched:
            raise WebSocketAuthError(code=1008,reason="Invalid tracking code.")

        while True:
            await websocket.receive_text()

    except WebSocketAuthError as e:
        await websocket.close(code=e.code,reason=e.reason)

    except WebSocketDisconnect :
        pass

    except Exception as e:
        print("Error while making sharing live location ",e)
        await websocket.close(code=1011,reason="Internal server error.")
        
    finally:
        LLManager.disconnect(user_id,tracking_code)