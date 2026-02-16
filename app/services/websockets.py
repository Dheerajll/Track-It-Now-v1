from fastapi import WebSocket,WebSocketDisconnect
from app.core.config import settings
import jwt


'''
Websocket manager to hanlde the parcel request notifications
'''

class RequestNotificationManager:
    def __init__(self) -> None:
        '''
        Fine for now but needs to be improved while 
        scaling up
        '''
        self.active_connections:dict[str,WebSocket] = {}
    
    async def connect(self,user_id:str,websocket:WebSocket):
        try:
            await websocket.accept()
            self.active_connections[user_id] = websocket
            print(f"User {user_id} connected to notification websocket")
        
        except Exception as e:
            print("Error while connecting to websocket." ,e)
    
    def disconnect(self,user_id:str):
        try:
            self.active_connections.pop(user_id,None)
            print(f"User {user_id} disconnect from websocket.")
        
        except Exception as e:
            print("Error while disconnecting from websocket. ",e)
        
    async def send_message(self, message:dict,receiver_id:str):
        try:
            receiver_ws = self.active_connections.get(receiver_id)

            if receiver_ws:
                await receiver_ws.send_json(message)
            else:
                print("No receiver websocker connected.")
        except WebSocketDisconnect:
            self.disconnect(receiver_id)
        except Exception as e:
            print("Error while sending message. ",e)

'''
We would use the exception class to 
authenticate the websocket users
as we can't use dependency on websocket
'''
class WebSocketAuthError(Exception):
    def __init__(self,code,reason)-> None:
        self.code = code
        self.reason = reason


'''
To decode the token
'''
def decode_token_for_websocket(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise WebSocketAuthError(code=1008,reason="Token expired")

    except jwt.InvalidTokenError:
        raise WebSocketAuthError(code=1008,reason="Invalid token")

    except Exception:
        raise WebSocketAuthError(code=1011,reason="Token decode failed")

def verify_token(token:str,role:str, sender_id :str):
    payload = decode_token_for_websocket(token)
    user_role = payload.get("role")
    user_id = payload.get("id")
    if user_role != role or str(user_id) != sender_id:
        raise WebSocketAuthError(code=1008,reason="No permission")


class AgentAvailabilityManager:
    def __init__(self) -> None:
        '''
        Fine for now but needs to be improved while 
        scaling up
        '''
        self.active_connections : dict[str,WebSocket] = {}

    async def connect(self,user_id:str,websocket:WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected to search online agent.")
    
    def disconnect(self,user_id :str):
        self.active_connections.pop(user_id,None)
        print(f"User {user_id} went offline.")

    async def broadcast_message(self,message:dict,user_id:str):
        try:
            websocket = self.active_connections.get(user_id)
            if websocket:
                await websocket.send_json(message)
            else:
                print(f"User {user_id} is not connected to search agent websocket.")
        except WebSocketDisconnect:
            pass

        except Exception as e:
            print("Error while broadcasting the agent location. ",e)

        finally:
            self.disconnect(user_id)



