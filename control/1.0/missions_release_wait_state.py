from datetime import datetime
import logging
import asyncio
from http import HTTPStatus
from tornado.escape import json_decode
from control.system.tornado_ros_handler import TornadoROSHandler
from control.system.mission_handler import MissionHandler as mission_cache

class RequestHandler(TornadoROSHandler):
    def __init__(self, *args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)

    async def get(self,*args):
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
        """
        
        # Check mission stage
        mission = mission_cache.get_mission(mission_cache)
        if mission['msg']['actionPtr'] == 5 and mission['msg']['action_state'] == 1: # The action is Wait and status in 1
            call_data = {'id':self.uri, 'op':"call_service",'type': "std_srvs/srv/Empty",'service': "/mission_control/trigger_button",'args': {} }
            await self.ros_service_handler(call_data,None)
        else:
            self.cache_hit = True
            response_string = {"op": "service_response", "service": "/mission_control/trigger_button", "values": {"state":""}, "result": False,"reason": "Not allow to trigger button now.", "id": "/1.0/missions/release_wait_state"}
            logging.debug("Release wait is not allow to trigger")
            self.rest_response(response_string)        