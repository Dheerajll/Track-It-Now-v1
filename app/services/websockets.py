from fastapi import WebSocket,WebSocketDisconnect,Depends
from app.core.config import settings
import asyncio
from app.database.redis_init import redis_client
from app.database.repository.location import LocationRepo
from app.schemas.location import Location
import json
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
            print("Error while connecting to notification websocket." ,e)
    
    def disconnect(self,user_id:str):
        try:
            self.active_connections.pop(user_id,None)
            print(f"User {user_id} disconnected from notification websocket.")
        
        except Exception as e:
            print("Error while disconnecting from notification websocket. ",e)
        
    async def send_message(self, message:dict,receiver_id:str):
        try:
            receiver_ws = self.active_connections.get(receiver_id)

            if receiver_ws:
                await receiver_ws.send_json(message)
            else:
                print("No receiver notification websocket connected.")
        except WebSocketDisconnect:
            self.disconnect(receiver_id)
        except Exception as e:
            print("Error while sending notification. ",e)

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

def verify_token(token:str,role:list[str], sender_id :str):
    payload = decode_token_for_websocket(token)
    user_role = payload.get("role")
    user_id = payload.get("id")
    if user_role not in role or str(user_id) != sender_id:
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
                return
        except WebSocketDisconnect:
            self.disconnect(user_id)

        except Exception as e:
            self.disconnect(user_id)
            print("Error while broadcasting the agent location. ",e)



'''
This block handles all the code for live 
location sharing from agent and listeners 
'''

'''
Redis listener for the channel to read the live-location
'''
async def redis_listener(channel:str,location_repo:LocationRepo):
    try:
        pubsub = redis_client.pubsub() 

        await pubsub.subscribe(channel)

        try:
            async for messages in pubsub.listen():
                if messages["type"] == "message":
                    data = json.loads(messages["data"])
                    delivery_id = data["delivery_id"]
                    agent_id = data["agent_id"]
        
                    
                    location = Location(lat=float(data["lat"]),
                                        lng=float(data["lng"]),
                                        timestamp=data["timestamp"])
                    
                    await LLManager.stream_location(data,channel)
                    '''
                    Storing in database
                    '''
                    await location_repo.add_location(agent_id,delivery_id,location)

        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            print(f"Listener unsubscribed from room: {channel}")
    except Exception as e:
        print("Error while listening to redis pubsub. ",e)
    
    finally:
        await pubsub.close()



'''
Websocket Manager for Live-Location
'''
class LiveLocationManager:
    def __init__(self) -> None:
        self.active_connections : dict[str,WebSocket] = {}
        self.broadcast_channel : dict[str,dict[str,WebSocket]] = {}
        self.redis_task : dict[str,asyncio.Task] = {}

        #Lock to prevent race condition
        self._channel_locks : dict[str,asyncio.Lock] = {}
    
    async def connect(self,user_id:str,websocket:WebSocket,location_repo:LocationRepo|None = None,channel:str|None = None):
        try:
            await websocket.accept()
            #If we get connection for the broadcast channel
            if channel:
                #First we check if the channel has already been created
                #If not we create the channel
                if channel not in self.broadcast_channel:
                    self.broadcast_channel[channel]={}

                #First we create a channel lock per channel to
                #prevent race condition
                lock = self._channel_locks.setdefault(channel, asyncio.Lock())

                #Now we check if a task for that channel 
                # exists if not we create a task for that channel
                async with lock:
                    if channel not in self.redis_task:
                        if location_repo:
                            self.redis_task[channel] = asyncio.create_task(redis_listener(channel,location_repo))  
                            print(f"Redis listener for live-share started for channel: {channel}")
                        
                        
                #Now we register the user to this channnel
                self.broadcast_channel[channel][user_id] = websocket
                print(f"User {user_id} entered the broadcast channel:{channel}")
            else:
                #If there is no channel then the agent is connecting to 
                #Share their location so we just register the agent in websocket
                #Connection
                self.active_connections[user_id] = websocket
                print(f"User {user_id} started streaming.")

        except Exception as e:
            print("Error while connecting to live-share websocket. ",e)

    def disconnect(self,user_id:str,channel:str|None =None):
        try:
            if channel:
                #Checking if the their already is channel in broadcast_channel
                channel_conn = self.broadcast_channel.get(channel)
                #And if there is we remove the user from it
                if channel_conn:
                    channel_conn.pop(user_id,None)
                    print(f"User{user_id} left channel: {channel}")
                
                #We check again if there are any user
                #If no users are in the channel we 
                #Close the channel and cancel the task
                channel_conn = self.broadcast_channel.get(channel)
                if not channel_conn:
                    self.broadcast_channel.pop(channel,None)
                    self._channel_locks.pop(channel, None)
                    print("Channel broadcast closed.")
                    task = self.redis_task.pop(channel,None)
                    if task:
                        task.cancel()
            else:
                self.active_connections.pop(user_id)
                print(f"User {user_id} stopped streaming.")

        except Exception as e:
            print("Error while disconnecting from live-share websocket.")

    async def stream_location(self,message:dict,channel:str):
        channel_conn = self.broadcast_channel.get(channel)
        #We fetched the channel now we broadcast the 
        #message to every user in that channel
        try:
            if channel_conn:
                for user_id,ws in list(channel_conn.items()):
                    try:
                        if ws:
                            await ws.send_json(message)
                    except WebSocketDisconnect:
                        self.disconnect(user_id,channel)
                        continue
        except Exception as e:
            print("Error while streaming location. ",e)
'''
Creating instance of websocket manager that handles Request notification
'''
RNmanager = RequestNotificationManager()

'''
Creating instance of websocket manager that handle agent availability
'''
AAmanager = AgentAvailabilityManager()

'''
Creating instance of websocket manager for live-location manager.
'''
LLManager = LiveLocationManager()