from datetime import datetime
from http import HTTPStatus
from tornado.escape import json_decode
from control.schema.mission_unit import MissionUnit #The openAPI and JSON validating rule for response
from control.schema.mission_unit import MissionItem #The openAPI and JSON validating rule for request
from control.schema.mission_unit import MissionActivityTrigger #The openAPI and JSON validating rule for request
from control.system.tornado_ros_handler import TornadoROSHandler
from control.system.cache_data import cache_subscribe_data as cache_subscription
from control.system.mission_handler import MissionHandler as mission_cache

class RequestHandler(TornadoROSHandler):
    def __init__(self, *args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)

    # def initialize(self):
    #     self.cache_hit = False
    #     self.future = asyncio.get_running_loop().create_future()
    #     self.cache_rest_data = dict()
    #     self.rest_cache_period = 5

    # def prepare(self):
    #     cache = self.cache_rest_data.get(self.uri)
    #     if cache is None:
    #         self.cache_rest_data.update({self.uri:{'cacheData':None,'lastUpdateTime':datetime.now()}})
    #     elif (datetime.now() - cache['lastUpdateTime']).seconds < self.rest_cache_period and cache['cacheData'] is not None:
    #         self.cache_hit = True

    def get(self,*args):
        """
        ---
        tags:
        - Missions
        summary: Get mission state
        description: list all missions as array
        produces:
        - application/json        
        responses:
          "200":
              description: show mission array
              content:
                application/json:
                  schema:
                      $ref: '#/components/parameters/MissionItem'
          "204":
            description: No content
        """

        subscribe_data = cache_subscription.get('mission_control/states')
        ret = {}
        if subscribe_data is not None:
            if subscribe_data['data'] is None:
                ret = {"result":False,"reason":"Not mission data","mission":{}}
            else:
                self.cache_hit = True
                self.cache_rest_data.update({self.uri:{'cacheData':subscribe_data,'lastUpdateTime':datetime.now()}})
                ret = subscribe_data['data']
                ret['result'] = True
        else:
            ret = {"result":False,"reason":"Not mission data","mission":{}}

        self.rest_response(ret)

    async def post(self,*args):
        """        
        ---
        tags:
        - Missions
        summary: Append a mission to queue
        description: The mission will be bypass to ROS via publish  
        produces:
        - application/json
        requestBody:
          description: Create mission
          required: true
          content:
            application/json:          
              schema: 
                $ref: '#/components/parameters/MissionItem'
        responses:
          "201":
              description: successful operation
          "400":
              description: fail to append mission
          "500":
              description: Internal Server Error
        """

        if self.validating_success:
            call_data = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "mission_control/mission",'msg':self.request_data['mission']}
            await self.ros_publish_handler(call_data,False)


    async def put(self,*args):
        """        
        ---
        tags:
        - Missions
        summary: Trigger mission state
        description: This API is used to start/stop/skip/reset current mission
        produces:
        - application/json
        requestBody:
          description: trigger a mission state
          content:
            application/json:
              schema:
                $ref: '#/components/parameters/MissionActivityTrigger'
        responses:
          "201":
              description: successful operation
          "400":
              description: Bad request
          "405":
              description: Not allow to change mission by this method 
        """

        default_return = {
            "reason":"Not support parameter",
            "values":{"state":"","result":""},
            "result": False,"msg":{
            "state":0,    
            "mission_state":0,    
            "missions":[]} }        
        if self.validating_success:
            mission = mission_cache.get_mission(mission_cache)

            if int(self.request_data['command']) == 1 or int(self.request_data['command']) == 2:#Not support stop,reload mission
                self.rest_response(default_return)
            elif int(self.request_data['command']) == 0 and mission['msg']['state'] == 0: # allow to start mission only when mission state is 0
                service_call_parameters = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(self.request_data['command'])} }
                await self.ros_service_handler(service_call_parameters,None)
            elif int(self.request_data['command']) == 3 or int(self.request_data['command']) == 4:
                service_call_parameters = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(self.request_data['command'])} }
                await self.ros_service_handler(service_call_parameters,None)
            else:
                self._status_code = HTTPStatus.METHOD_NOT_ALLOWED.value
                default_return['reason'] = "Not support at this time"
                self.rest_response(default_return)
