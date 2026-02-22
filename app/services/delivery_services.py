from app.database.repository.delivery_assignment import DeliveryRepo
from app.database.repository.trackingcode import TrackingCodeRepo
from app.services.parcels import ParcelServices
from app.schemas.users import UserOut
from app.schemas.delivery import DeliveryInfo
from app.services.websockets import RNmanager
from app.services.users import UserServices
from fastapi import HTTPException
'''
To assign parcel to an agent
'''

class DeliveryServices:
    def __init__(self,delivery_repo:DeliveryRepo,tracking_code_repo:TrackingCodeRepo,parcel_service:ParcelServices,userservice:UserServices) -> None:
        self.delivery_repo = delivery_repo
        self.tracking_code_repo = tracking_code_repo
        self.parcel_service = parcel_service
        self.userservice = userservice

    async def assign_parcel(self,user:UserOut,agent_id:int,parcel_id:int):
        '''
        Lets analyze what we have to do when the parcel has
        been assigned to an agent
        1. Create delivery assignment.
        2. Generate tracking code.
        3. Update the parcel status to "assigned."
        4. Send general delivery info to the sender.
        5. Notify agent that he has been assigned
            i. Send tracking code
            ii. Send parcel id.
            iii. After being notified agents start broadcasting their live location.
        6. Notify receiver that his parcel has been assigned and send the tracking code.
        '''

        try:
            '''
            Creating delivery assignment
            '''
            delivery = await self.delivery_repo.create_delivery(parcel_id,agent_id) #type:ignore

            print("Delivery assignment created.")
            '''
            Generating tracking code
            '''
            tracking_code = (await self.tracking_code_repo.create_tracking_code(agent_id,parcel_id))
            print("Tracking code generated.")
            '''
            Updating the parcel status to "assigned"
            '''
            await self.parcel_service.update_parcel_status_by_agent(parcel_id,"assigned")

            print("Parcel status updated.")
            '''
            Notifying agent that he has been assigned.
            '''
            message_to_agent = {
                "type":"parcel-assigned",
                "parcel_id":parcel_id,
                "tracking_code":tracking_code,
                "delivery_id" : delivery.id,
                "message":f"{user.name} has assigned you to deliver Parcel no.{parcel_id}"
            }
            await RNmanager.send_message(message=message_to_agent,receiver_id=str(agent_id))
            print("Notification send to agent.")
            '''
            Notifying receiver that his parcel has been assigned to a agent.
            '''
            agent = await self.userservice.get_user_by_id(agent_id)
            parcel = await self.parcel_service.get_a_parcel(parcel_id)

            if agent is None:
               raise HTTPException(
                   status_code=404,
                   detail=f"Error while assigning agent. Agent not found."
               )

            message_to_receiver = {
                "type" : "agent-assigned",
                "tracking_code" : tracking_code,
                "message":f"{agent.name} has been assigned for your parcel no.{parcel_id}"
            }
            '''
            Later send this tracking code in email or receiver.
            '''
            await RNmanager.send_message(message=message_to_receiver,receiver_id=str(parcel.receiver_id))
            print("Notification send to receiver.")
            return DeliveryInfo(agent_name=agent.name,tracking_code=tracking_code)

        except Exception as e:
            raise HTTPException(
                status_code= 500,
                detail=f"Error while assigning parcel to agent. {e}"
            )



