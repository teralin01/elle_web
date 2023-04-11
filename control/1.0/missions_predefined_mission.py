from datetime import datetime
import logging
from http import HTTPStatus

from tornado_swagger.parameter import register_swagger_parameter
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
        parameters:
        - in: body
          name: body
          description: match predefined mission number
          schema:
            $ref: '#/components/parameters/PredefinedMissionTrigger'
        responses:
          "201":
              description: successful operation
          "408":
              description: fail to append mission              
        """
        # self._status_code = HTTPStatus.CREATED.value
        # err_return = None
        # try:
        #     data = json_decode(self.request.body)
        #     logging.debug(data)

        #     validating_return = JsonValidator.validate_paramater_schema(JsonValidator,data, self.request.uri, 'post')
        #     if not validating_return:
        #         raise ValueError("JSON Validating fail")
        # except ValueError as exception:
        #     logging.debug(err_return)
        #     self._status_code = HTTPStatus.BAD_REQUEST.value
        #     self.rest_response({'result':False,'reason':str(exception)})
        # else:
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
    