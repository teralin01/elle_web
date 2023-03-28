from datetime import datetime
import logging
import asyncio
from asyncio import Future
import json
from http import HTTPStatus
from tornado_swagger.model import register_swagger_model
from tornado_swagger.parameter import register_swagger_parameter
from control.system.tornado_ros_handler import TornadoROSHandler
from control.system.cache_data import cache_subscribe_data as cache_subscription
from control.system.mission_handler import MissionHandler as mission_cache
from control.system.json_validator_schema import mission_schema


class RequestHandler(TornadoROSHandler):
    def __init__(self, *args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)

    def initialize(self):
        self.cache_hit = False
        self.future = asyncio.get_running_loop().create_future()
        self.cache_rest_data = dict()
        self.rest_cache_period = 5
        global cache_subscription

    def prepare(self):
        cache = self.cache_rest_data.get(self.uri)
        if cache is None:
            self.cache_rest_data.update({self.uri:{'cacheData':None,'lastUpdateTime':datetime.now()}})
        elif (datetime.now() - cache['lastUpdateTime']).seconds < self.rest_cache_period and cache['cacheData'] is not None:
            self.cache_hit = True
            
    async def get(self,*args):
        """
        ---
        tags:
        - Mission
        summary: Get mission state
        description: list all missions as array
        produces:
        - application/json        
        responses:
          "200":
              description: show mission array
        """

    async def post(self,*args):
        """        
        ---
        tags:
        - Mission
        summary: Append a mission to queue
        description: TBD
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
          "408":
              description: fail to append mission
        """

    async def put(self,*args):
        """        
        ---
        tags:
        - Mission
        summary: Append a mission to queue
        description: TBD
        produces:
        - application/json
        parameters:
        - in: body
          name: body
          description: Create mission
          required: false
          schema:
            type: string      
        responses:
          "201":
            description: successful operation
          "408":
            description: fail to append mission
        """

@register_swagger_parameter
class MissionItem:
    """
    ---
    name: mission
    in: path
    description: add a mission
    required: true
    type: object
    properties:
      action_state:
        type: integer
        format: int32
        minimum: 0
        maximum: 5
        example: 1
      coordinate:
        required:
        - x
        - y
        - z
        type: object
        properties:
          "x":
            type: number
            multipleOf: 0.001
            example: 1.234
          "y":
            type: number
            multipleOf: 0.001
            example: 6.789
          "z":
            type: number
            multipleOf: 0.00001
            example: 1.23456
    """


@register_swagger_model
class MissionModel:
    """
    ---
    type: object
    description: Post model representation
    properties:
        id:
            type: integer
            format: int64
        title:
            type: string
        text:
            type: string
        is_visible:
            type: boolean
            default: true
    """
    
    
@register_swagger_model
class MissionElement:
    """
    ---
    name: mission
    in: path
    description: add a mission
    required: true
    type: object
    properties:
      action_state:
        type: integer
        format: int32
        minimum: 0
        maximum: 5
        example: 1
      coordinate:
        required:
        - x
        - y
        - z
        type: object
        properties:
          "x":
            type: number
            multipleOf: 0.001
            example: 1.234
          "y":
            type: number
            multipleOf: 0.001
            example: 6.789
          "z":
            type: number
            multipleOf: 0.00001
            example: 1.23456
    """