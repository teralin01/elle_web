from datetime import datetime
import logging

from packages.tornado_openapi.parameter import register_swagger_parameter
from control.system.tornado_ros_handler import TornadoROSHandler
from control.system.mission_handler import MissionHandler as mission_cache

from datamodel import event_model

class RequestHandler(TornadoROSHandler):
    def __init__(self, *args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)

    async def post(self,*args):
        """
        ---
        tags:
        - Missions
        summary: Call a predefined mission
        description: TBD
        produces:
        - application/json
        requestBody:
          description: match predefined mission number
          content:
            application/json:              
              schema:
                $ref: '#/components/parameters/PredefinedMissionTrigger'
        responses:
          "201":
              description: successful operation
          "400":
              description: fail to append mission              
        """
        if self.validating_success:
            if mission_cache.is_mission_duplication(mission_cache,self.request_data['remote_number']):
                event_model.save_mission_act({"status":"reject","action":self.request_data['remote_number'],"timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})    
                default_string = {"result": False, "values": {"state": "", "result": ""}, "msg": {"state": 0, "mission_state": -1, "missions": []}, "reason": "Mission is duplicated, reject this request temperatory"}
                self.rest_response(default_string)
            else:
                event_model.save_mission_act({"status":"success","action":self.request_data['remote_number'],"timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
                call_data = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlStationCall",'service': "/mission_control/station_call",'args': {'remote_number':int(self.request_data['remote_number'])} }
                await self.ros_service_handler(call_data,None)

@register_swagger_parameter
class PredefinedMissionTrigger:
    """
    ---
    in: path
    description: call a predefined mission with number
    type: object
    properties:
      remote_number:
        type: integer
        format: int32
        minimum: 1
        maximum: 4
        example: 4   
    required: 
    - remote_number
    """
    