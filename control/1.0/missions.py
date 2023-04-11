from datetime import datetime
import logging
import asyncio
from http import HTTPStatus
from tornado.escape import json_decode
from control.schema.mission_unit import MissionUnit #The openAPI and JSON validating rule for response
from control.schema.mission_unit import MissionItem #The openAPI and JSON validating rule for request
from control.schema.mission_unit import MissionActivityTrigger #The openAPI and JSON validating rule for request
from control.system.tornado_ros_handler import TornadoROSHandler
from control.system.cache_data import cache_subscribe_data as cache_subscription
from control.system.mission_handler import MissionHandler as mission_cache
from control.system.json_validator import JsonValidator

class RequestHandler(TornadoROSHandler):
    def __init__(self, *args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)

    def initialize(self):
        self.cache_hit = False
        self.future = asyncio.get_running_loop().create_future()
        self.cache_rest_data = dict()
        self.rest_cache_period = 5

    def prepare(self):
        cache = self.cache_rest_data.get(self.uri)
        if cache is None:
            self.cache_rest_data.update({self.uri:{'cacheData':None,'lastUpdateTime':datetime.now()}})
        elif (datetime.now() - cache['lastUpdateTime']).seconds < self.rest_cache_period and cache['cacheData'] is not None:
            self.cache_hit = True

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
                    type: array
                    items:
                      $ref: '#/components/parameters/MissionItem'
          "204":
            description: No content
        """

        subscribe_data = cache_subscription.get('mission_control/states')
        if subscribe_data is not None:
            if subscribe_data['data'] is None:
                self._status_code = HTTPStatus.NO_CONTENT.value
                self.rest_response({"result":False,"info":"Current cached date is None"})
            else:
                self.cache_hit = True
                self.cache_rest_data.update({self.uri:{'cacheData':subscribe_data,'lastUpdateTime':datetime.now()}})
            self.rest_response(subscribe_data['data'])
        else:
            self._status_code = HTTPStatus.NO_CONTENT.value
            self.rest_response({"result":False,"info":"Backend have never receieve mission data"})

    async def post(self,*args):
        """        
        ---
        tags:
        - Missions
        summary: Append a mission to queue
        description: The mission will be bypass to ROS via publish  
        produces:
        - application/json
        parameters:
        - in: body
          name: body
          description: Create mission
          required: false
          schema: 
            $ref: '#/components/parameters/MissionItem'
        responses:
          "201":
              description: successful operation
          "400":
              description: fail to append mission
        """

        self._status_code = HTTPStatus.CREATED.value
        try:
            data = json_decode(self.request.body)
            logging.debug(data)

            validating_return = JsonValidator.validate_paramater_schema(JsonValidator,data, self.request.uri, 'post')
            if not validating_return:
                raise ValueError("JSON Validating fail")

        except ValueError as exception:
            logging.error(exception)
            self._status_code = HTTPStatus.BAD_REQUEST.value
            self.rest_response({'result':False,'reason':str(exception)})

        else:
            call_data = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "mission_control/mission",'msg':data['mission']}
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
        parameters:
        - in: body
          name: body
          description: set mission state
          required: true
          type: object
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
        self._status_code = HTTPStatus.CREATED.value
        default_return = {
            "op": "service_response", "topic": "/mission_control/command","backendMsg":"Not support parameter", 
            "reason":"",
            "values":{"state":"","result":""},
            "result": False,"msg":{
            "state":0,    
            "mission_state":0,    
            "missions":[]} }        
        try:
            data = json_decode(self.request.body)
            logging.debug(data)
            
            validating_return = JsonValidator.validate_paramater_schema(JsonValidator, data, self.request.uri, 'put')
            if not validating_return:
                raise ValueError("JSON Validating fail")
                
        except ValueError as exception:
            logging.error(exception)
            self._status_code = HTTPStatus.BAD_REQUEST.value
            self.rest_response(default_return)
        else:
            mission = mission_cache.get_mission(mission_cache)

            if int(data['command']) == 1 or int(data['command']) == 2:#Not support stop,reload mission
                self.rest_response(default_return)
            elif int(data['command']) == 0 and mission['msg']['state'] == 0: # allow to start mission only when mission state is 0
                service_call_parameters = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(data['command'])} }
                await self.ros_service_handler(service_call_parameters,None)
            elif int(data['command']) == 3 or int(data['command']) == 4:
                service_call_parameters = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(data['command'])} }
                await self.ros_service_handler(service_call_parameters,None)
            else:
                self._status_code = HTTPStatus.METHOD_NOT_ALLOWED.value
                default_return['backendMsg'] = "Not support at this time"
                self.rest_response(default_return)
