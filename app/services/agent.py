from app.services.websockets import AgentAvailabilityManager,verify_token,WebSocketAuthError
from fastapi import WebSocket,WebSocketDisconnect
from app.database.redis_init import redis_client
import json
import asyncio
from collections import defaultdict
'''
Creating the instance of the websocket manager.
'''
AAmanager = AgentAvailabilityManager()


'''
Method to generate a single region based on given lat and lng
'''
def get_region(latitude,longitude):
    region_x = int(latitude/0.01) #region with approx. 1 km
    region_y = int(longitude/0.01) #region with approx. 1 km

    return f"{region_x}:{region_y}"

'''
Method that returns the neighboring regions
'''
def get_neighbor_regions(lat, lng, radius=1):
    center_x = int(lat / 0.01)
    center_y = int(lng / 0.01)

    regions = []

    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            region_x = center_x + dx
            region_y = center_y + dy
            regions.append(f"{region_x}:{region_y}")

    return regions

'''
This block will consist the function after agent goes online.
'''
async def go_online(user_id:str,websocket:WebSocket,token:str):
    await AAmanager.connect(user_id,websocket)
    agent_id = None
    try:
        print(f"Verifying token for user_id: {user_id}")
        print(f"Token: {token[:20]}...")  
        verify_token(token=token,role=["agent"],sender_id=user_id)
        last_lat,last_lng = None,None
        while True:
            try:
                data = await websocket.receive_json()
            except ValueError as e:
                print("Invalid json format received. ",e)
                continue
            '''
            This data should be in this format:
            data = {

                'agent_id' : 'agent_id',
                'lat':'lat',
                'lng' : 'lng'
            }
            '''
            try:
                lat = float(data.get("lat", 0))
                lng = float(data.get("lng", 0))
                agent_id = str(data.get("agent_id", ""))
                
                if not agent_id or lat == 0 or lng == 0:
                    print(f"Invalid data received: {data}")
                    continue
                    
            except (ValueError, KeyError) as e:
                print(f"Error parsing location data: {e}")
                continue


            '''
            This block helps avoid redis pubsub load
            if the lat and lng very small 
            althoug we plan to avoid such scenario front the
            frontend by only sending the lat lng when location chnages 
            but keeping it here just help solve even if we get tiny movements
            '''
            # if last_lng is not None and last_lat is not None:
            #     if last_lat and abs(lat - last_lat) < 0.0001 and abs(lng - last_lng) < 0.0001:
            #         continue  # skip tiny movement

            # last_lat, last_lng = lat, lng

            '''
            ------------------------------------------------------------------------
            '''
            try:
                
                #Adding to redis.
                await redis_client.geoadd("agents_location",[lng,lat,agent_id])


            except Exception as e:
                print("Error while adding location to redis.",e)
                continue # to skip publish as geoadd() failed.
            '''
            To get the current region the agent is in
            '''
            region_id  = get_region(lat,lng)
            #To debug
            print(f"Agent {agent_id} in region: {region_id}")
            print(f"Neighboring regions: {get_neighbor_regions(lat, lng)}")
            
            #channel for specific region
            region_channel = f"region:{region_id}"
            print(f"Agent {agent_id} in region: {region_id}")
            print(f"Neighboring regions: {get_neighbor_regions(lat, lng)}")
            
            message_to_publish = {
                "type" : "online-agent-location",
                "agent_id":agent_id,
                "lat":lat,
                "lng":lng
            }
            #we have to send the json string so we use json.dumps()
            #publishing in that channel
            print(f"Publishing to channel: {region_channel}")
            print(message_to_publish)
            await asyncio.sleep(delay=3)
            await redis_client.publish(region_channel,json.dumps(message_to_publish))
            print("Agent location send to respective region.")

    except WebSocketDisconnect :
        pass

    except WebSocketAuthError as e:
        await websocket.close(e.code,e.reason)
    
    except Exception as e:
        print("Error while making agent online ",e)
        await websocket.close(code=1011,reason="Internal server error.")
        
    finally:
        if agent_id is not None:
            await redis_client.zrem("agents_location", str(agent_id))
            print("Location removed from redis geoadd")
        AAmanager.disconnect(user_id)


'''
Geosearch task that runs every 15 second to update nearby online agents
'''
async def nearby_agents_snapshot(lat:float,lng:float,user_id:str):
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"Snapshot iteration {iteration} for user {user_id}")
            '''
            Do geosearch periodically to get the nearby agents and their position
            every 15 second
            '''
            #we provide the received customer longitude and latitude.
            nearby_agents = await redis_client.geosearch("agents_location",longitude=lng,latitude=lat,radius=3,unit="km",withcoord=True)
            print(f"Found {len(nearby_agents)} agents")
            '''
            the nearby_agents gets 
            list of tuples with the agent_id and and tuple of positions
            [
            (member/agent_id,(lng,lat)),
            ]
            '''
            snapshot_detail = defaultdict(list)
            for agent_id,(agent_lng,agent_lat) in nearby_agents:
                nearby_agent = {
                "type":"online-agents-snapshot",
                "agent_id" : int(agent_id), # type consistency
                "lng" : agent_lng,
                "lat": agent_lat
                }
                snapshot_detail["nearby_agents"].append(nearby_agent)
            
            if not snapshot_detail["nearby_agents"]:
                snapshot_detail["nearby_agents"] = []
                snapshot_detail["message"] = ["No agents nearby"]

            await AAmanager.broadcast_message(snapshot_detail,user_id)
            print(f"Sent snapshot to user {user_id}")
            '''
            Send the snapshot message with agent id and their location to websocket
            with type agents-snapshot
            '''
            #wait for 15s before looping again.
            await asyncio.sleep(delay=15)
    except asyncio.CancelledError:
        print("Snapshoting online agent task has been cancelled.")
    
    except Exception as e:
        print("Error while sending online agent snapshot. ",e)



'''
Redis pubsub listener that listens to any publish in certain channels
'''

async def redis_pubsub_listener(channels:list,user_id:str):
    pubsub = redis_client.pubsub()
    
    #Subscribing the regions
    await pubsub.subscribe(*channels)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                print(f"Forwarding to user {user_id}: {data}")
                await AAmanager.broadcast_message(data,user_id)
    except asyncio.CancelledError:
        print("Listener task cancelled.")

    except Exception as e:
        print("Error while listening pubsub. ",e)
    
    finally:
        await pubsub.unsubscribe(*channels)


'''
Now this block will handle to search agent section from the customer side.
'''
async def search_for_agents(user_id:str,websocket:WebSocket,token:str,lat:float,lng:float):
    await AAmanager.connect(user_id,websocket)
    task_to_listen_pubsub = None
    task_to_send_snapshot = None
    try:
        verify_token(token=token,role=["customer"],sender_id=user_id)

        '''
        Initial snapshot
        '''
         #we provide the received customer longitude and latitude.
        nearby_agents = await redis_client.geosearch("agents_location",longitude=lng,latitude=lat,radius=3,unit="km",withcoord=True)

        print(f"Customer at: {lat}, {lng}")
        print(f"Found {len(nearby_agents)} agents within 3km")
        print(f"Agents: {nearby_agents}")

        '''
        the nearby_agents gets 
        list of tuples with the agent_id and and tuple of positions
        [
        (member/agent_id,(lng,lat)),
        ]
        '''
        snapshot_detail = defaultdict(list)
        for agent_id,(agent_lng,agent_lat) in nearby_agents:
            nearby_agent = {
            "type":"online-agents-snapshot",
            "agent_id" : int(agent_id), # type consistency
            "lng" : agent_lng,
            "lat": agent_lat
            }
            snapshot_detail["nearby_agents"].append(nearby_agent)
        
        

        await AAmanager.broadcast_message(snapshot_detail,user_id)

        '''
        Task to send online agents locatio snapshot
        '''
        task_to_send_snapshot = asyncio.create_task(nearby_agents_snapshot(lat,lng,user_id))
        '''
        We would calculate the neighboring regions just once as the 
        customer location is static
        '''
        neighboring_regions = get_neighbor_regions(lat,lng)

        #Creating regional channels
        channels = [f"region:{r}" for r in neighboring_regions]

        print(f"Customer subscribed to channels: {channels}")
        print(f"Neighboring regions: {neighboring_regions}")

        #Creating a backgroud task that continuously listens for agent publishes.
        task_to_listen_pubsub = asyncio.create_task(redis_pubsub_listener(channels,user_id))

        while True:
            await websocket.receive_text()  # #just to keep the connection open
    except WebSocketDisconnect:
        pass
    
    except WebSocketAuthError as e:
        await websocket.close(code=e.code,reason=e.reason)
    except Exception as e:
        print("Error while searching for agents.", e)
    
    finally:
        AAmanager.disconnect(user_id)
        if task_to_send_snapshot:
            task_to_send_snapshot.cancel()
        if task_to_listen_pubsub:    
            task_to_listen_pubsub.cancel()

