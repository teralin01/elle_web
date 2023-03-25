from datetime import datetime
import logging
import asyncio
from asyncio import Future
import json
from http import HTTPStatus   #Refer to https://docs.python.org/3/library/http.html
#from datamodel.auth_model import AuthDB
from tornado.escape import json_decode
from jsonschema import validate
from control.system.cache_data import cache_subscribe_data as cache_subscription
from control.system.mission_handler import MissionHandler as mission_cache
from control.system.json_validator_schema import mission_schema
from control.system.tornado_ros_handler import TornadoROSHandler
import pynmcli
from datamodel import event_model
from datamodel import landmark_model as LM
from datamodel import config_model as DBConfig
import config

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

        if config.settings['hostIP'] == "":
            config.settings['hostIP'] = self.request.host

    def check_mission_is_updated(self,publish_mission,existing_missions):
        for mission in existing_missions['msg']['missions']:
            if publish_mission['name'] == mission['name'] and \
                publish_mission['actions'][0]['coordinate']['x'] == mission['actions'][0]['coordinate']['x'] and \
                publish_mission['actions'][0]['coordinate']['y'] == mission['actions'][0]['coordinate']['y']:
                return True

        return False

    async def get(self,*args):
        """
        Description end-point
        ---
        tags:
        - REST
        summary: Create user
        description: This can only be done by the logged in user.
        operationId: examples.api.api.createUser
        produces:
        - application/json
        parameters:
        - in: body
          name: body
          description: Created user object
          required: false
          schema:
            type: object
            properties:
              id:
                type: integer
                format: int64
              username:
                type:
                  - "string"
                  - "null"
              firstName:
                type: string
              lastName:
                type: string
              email:
                type: string
              password:
                type: string
              phone:
                type: string
              userStatus:
                type: integer
                format: int32
                description: User Status
        responses:
        "201":
          description: successful operation
        """        
        
        
        self._status_code = HTTPStatus.CREATED.value
        if self.cache_hit:
            logging.debug("Return cache data")
            self.rest_response(self.cache_rest_data.get(self.uri)['cacheData'])

        elif self.uri == '/1.0/missions/release_wait_state':
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

        elif self.uri == '/1.0/missions' or self.uri == '/1.0/missions/':
            #TODO add cache fomr mission status
            subscribe_data = cache_subscription.get('mission_control/states')
            if subscribe_data is not None:
                if subscribe_data['data'] is None:
                    self._status_code = HTTPStatus.NO_CONTENT.value
                    self.rest_response({"result":False,"errno":102,"info":"Current cached date is None"})         
                else:
                    self.cache_hit = True
                    self.cache_rest_data.update({self.uri:{'cacheData':subscribe_data,'lastUpdateTime':datetime.now()}})
                self.rest_response(subscribe_data['data'])
            else:
                self._status_code = HTTPStatus.NO_CONTENT.value
                self.rest_response({"result":False,"errno":101,"info":"Backend have never receieve mission data"})

        elif self.uri == '/1.0/maps' or self.uri == '/1.0/maps/GetMap':
            call_data = {'id':self.uri, 'op':"call_service",'type': "nav_msgs/GetMap",'service': "/map_server/map",'args': {} }
            await self.ros_service_handler(call_data,None)

        elif self.uri == '/1.0/maps/map_meta' :  #TODO add map ID if support multiple maps
            subscribe_message = {"op":"subscribe","id":"RestTopics","topic": "/amcl_pose","type":"geometry_msgs/msg/PoseWithCovarianceStamped"}
            await self.ros_subscribe_handler(subscribe_message,None,False)

        elif self.uri == '/1.0/maps/speed_maps' :
            call_data = {'id':self.uri, 'op':"call_service",'type': "nav_msgs/GetMap",'service': "/speed_filter_mask_server/map",'args': {} }
            await self.ros_service_handler(call_data,None)

        elif self.uri == '/1.0/maps/keepout_maps' :
            call_data = {'id':self.uri, 'op':"call_service",'type': "nav_msgs/GetMap",'service': "/keepout_filter_mask_server/map",'args': {} }
            await self.ros_service_handler(call_data,None)         

        elif self.uri == '/1.0/maps/path':       #TODO add robotID to the URL in fleet version
            subscribe_message = {"op":"subscribe","id":"RestTopics","topic": "/plan","type":"nav_msgs/Path"}
            await self.ros_subscribe_handler(subscribe_message,None,False)

        elif self.uri == '/1.0/maps/costmap':    #TODO add robotID to the URL in fleet version
            call_data = {'id':self.uri, 'op':"call_service",'type': "nav2_msgs/srv/GetCostmap",'service': "/global_costmap/get_costmap",'args': {} }
            await self.ros_service_handler(call_data,None)

        elif self.uri == '/1.0/ros/service':
            call_data = {'id':self.uri, 'op':"call_service",'type': self.get_argument("ros_type"),'service': self.get_argument("ros_service") }
            await self.ros_service_handler(call_data,None)

        elif self.uri == '/1.0/ros/service/withArgs':
            call_data = {'id':self.uri, 'op':"call_service",'type': self.get_argument("ros_type"),'service': self.get_argument("ros_service"),'args': {self.get_argument("ros_args")} }
            await self.ros_service_handler(call_data,None)

        elif self.uri == '/1.0/ros/subscribe':
            subscribe_message = {"op":"subscribe","id":"RestTopics","topic":self.get_argument("ros_topic"),"type":self.get_argument("ros_type")}
            await self.ros_subscribe_handler(subscribe_message,None,False)

        elif self.uri == '/1.0/ros/unsubscribe':
            unsubscribe_message = {"op":"unsubscribe","id":"RestTopics","topic":self.get_argument("ros_topic"),"type":self.get_argument("ros_type")}
            await self.ros_unsubscribe_handler(unsubscribe_message,False)
   
        # elif self.uri == '/1.0/status/hardware':    #TODO add robotID to the URL in fleet version
        #     self.rest_response(HWInfo.get())

        elif self.uri == '/1.0/maps/landmarks':
            self.rest_response(json.dumps(LM.get_points()))

        elif self.uri == '/1.0/config/viewer':
            self.rest_response(json.dumps(DBConfig.GetViewerConfig()))

        elif self.uri == '/1.0/network/wifilist':
            self.rest_response(pynmcli.NetworkManager.Device().wifi('list').execute())

        elif self.uri == '/1.0/network/connected':
            self.rest_response(pynmcli.NetworkManager.Connection().show().execute())

        elif self.uri == '/1.0/event/sse':
            self.rest_response(pynmcli.NetworkManager.Connection().show().execute())

        elif '/1.0/config/user/' in self.uri: #Return privilige of this user
            self.rest_response(json.dumps(DBConfig.GetSingleUserConfig(self.uri[len('/1.0/config/user/'):])))

    async def post(self,*args):
        """
        Description end-point
        ---
        tags:
        - REST
        summary: Create user
        description: This can only be done by the logged in user.
        operationId: examples.api.api.createUser
        produces:
        - application/json
        parameters:
        - in: body
          name: body
          description: Created user object
          required: false
          schema:
            type: object
            properties:
              id:
                type: integer
                format: int64
              username:
                type:
                  - "string"
                  - "null"
              firstName:
                type: string
              lastName:
                type: string
              email:
                type: string
              password:
                type: string
              phone:
                type: string
              userStatus:
                type: integer
                format: int32
                description: User Status
        responses:
        "201":
          description: successful operation
        """           
        self._status_code = HTTPStatus.CREATED.value
        err_return = None
        try:
            data = json_decode(self.request.body)
            logging.debug(data)

        except Exception as exception:
            logging.debug(err_return)
            self._status_code = HTTPStatus.BAD_REQUEST.value
            self.rest_response({'result':False,'reason':str(exception)})

        if self.uri == '/1.0/missions' or self.uri == '/1.0/missions/':
            try:
                err_return = validate(instance=data, schema=mission_schema)
            except Exception as exception:
                logging.debug(err_return)
                self._status_code = HTTPStatus.BAD_REQUEST.value
                self.rest_response({'result':False,'reason':str(exception)})
                return
            else:
                call_data = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "mission_control/mission",'msg':data['mission']}
                await self.ros_publish_handler(call_data,False)
                return

        elif self.uri == '/1.0/nav/initialpose':
            publish_message = {"op":"publish","id":"RestTopics","topic":"/initialpose","type":"geometry_msgs/msg/PoseWithCovarianceStamped",'msg':data['msg']}
            await self.ros_publish_handler(publish_message,False)

        elif self.uri == '/1.0/nav/goalpose':
            try:
                err_return = validate(instance=data, schema=mission_schema)
            except Exception as exception:
                logging.debug(err_return)
                self._status_code = HTTPStatus.BAD_REQUEST.value
                self.rest_response({'result':False,'reason':str(exception)})
                return
            else:
                publish_message = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "/mission_control/mission",'msg':data['mission']}
                subscribe_message = {"op":"subscribe","id":"RestTopics","topic": "mission_control/states","type":"elle_interfaces/msg/MissionControlMissionArray"}
                call_data = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':0} }

                ret = await self.ros_publish_handler(publish_message,True)
                if ret is True:
                    idx = 0
                    while True: #Check mission state until mission updated
                        subscribe_future = Future()
                        await self.ros_subscribe_handler(subscribe_message,subscribe_future,False)
                        mission_state = subscribe_future.result()
                        if mission_state is not None:
                            mission_update_status = self.check_mission_is_updated(data['mission'],mission_state)
                            if mission_update_status:
                                await self.ros_service_handler(call_data,None)
                                break
                            else:
                                if idx > 3:
                                    self.rest_response({'result':False,"info":"Can't subscribe mission status from ROS"})
                                    break
                                idx += 1
                            await asyncio.sleep(1)
                else:
                    self.rest_response({'result':False,"info":"Can't publish data to ROS"})
                return
        
        elif self.uri == '/1.0/nav/move':
            #example: {linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z:0}}"
            call_data = {'type': "geometry_msgs/msg/Twist",'topic': "/cmd_vel",'msg':{
                'linear':{ 'x':data['forwardspeed'],'y':0,'z':0 },'angular':{'x':0,'y':0,'z':data['turn']}  }}
            await self.ros_publish_handler(call_data,False)

        elif self.uri == '/1.0/ros/publish':
            publish_message = {"op":"publish","id":"RestTopics","topic":data['ros_topic'],"type":data['ros_type'],'msg':data['msg']}
            await self.ros_publish_handler(publish_message,False)

        elif self.uri == '/1.0/maps/landmarks':
            #TODO validate with landmark Schema
            ret = LM.set_points(data)
            #ret = LM.UpsertPoints(data)
            self.rest_response(ret)

        elif self.uri == '/1.0/config/viewer':
            ret = DBConfig.SetUserConfig(data)
            self.rest_response(ret)

        elif self.uri == '/1.0/network/WiFiconnectionUP':
            # the SSID shoud be replace to device name. such as wlx08beac0e2a82
            result = pynmcli.NetworkManager.Connection().up(data['SSID']).execute()
            self.rest_response({"result": True, 'info':result})

        elif self.uri == '/1.0/network/WiFiconnectionDown':
            # the SSID shoud be replace to device name. such as wlx08beac0e2a82
            result = pynmcli.NetworkManager.Connection().down(data['SSID']).execute()
            self.rest_response({"result": True, 'info':result})

        elif self.uri == '/1.0/network/connectWiFi':
            pynmcli.NetworkManager.Device().wifi("connect ",data['SSID']," password ",data['PASSWORD']).execute()
            self.rest_response({"result": True})
        #nmcli d wifi connect my_wifi password <password>

        elif self.uri == '/1.0/network/disconnectWiFi':
            result = pynmcli.NetworkManager.Device().disconnect(data['SSID']).execute()
            self.rest_response({"result": True, 'info':result}) 

        elif self.uri == '/1.0/maps/SetMap':

            #if success setmap via ROS service, then update map width/height to database

            pass

        elif self.uri == '/1.0/missions/predefined_mission':
            if mission_cache.is_mission_duplication(mission_cache,data['remote_number']):
                event_model.save_mission_act({"status":"reject","action":data['remote_number'],"timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})    
                default_string = {"result": False, "values": {"state": "", "result": ""}, "msg": {"state": 0, "mission_state": -1, "missions": []}, "reason": "Mission is duplicated, reject this request temperatory"}
                self.rest_response(default_string)
            else:
                event_model.save_mission_act({"status":"success","action":data['remote_number'],"timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
                call_data = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlStationCall",'service': "/mission_control/station_call",'args': {'remote_number':int(data['remote_number'])} }
                await self.ros_service_handler(call_data,None)
        elif self.uri == '/1.0/missions' or self.uri == '/1.0/missions/':  #start/stop mission
            mission = mission_cache.get_mission(mission_cache)
            default_string = {
                "op": "service_response", "topic": "/mission_control/command","backendMsg":"Not support parameter", 
                "reason":"",
                "values":{"state":"","result":""},
                "result": False,"msg":{
                "state":0,    
                "mission_state":0,    
                "missions":[]} }
            if int(data['command']) == 1 or int(data['command']) == 2: # Not support stop, reload mission
                self.rest_response(default_string)  
            elif int(data['command']) == 0 and mission['msg']['state'] == 0: # allow to start mission only when mission state is 0
                call_data = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(data['command'])} }
                await self.ros_service_handler(call_data,None)
            elif int(data['command']) == 3 or int(data['command']) == 4:
                call_data = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(data['command'])} }
                await self.ros_service_handler(call_data,None)
            else:
                default_string['backendMsg'] = "Not support at this time"
                self.rest_response(default_string)

    async def delete(self,*args):
        """
        Description end-point
        ---
        tags:
        - REST
        summary: Create user
        description: This can only be done by the logged in user.
        operationId: examples.api.api.createUser
        produces:
        - application/json
        parameters:
        - in: body
          name: body
          description: Created user object
          required: false
          schema:
            type: object
            properties:
              id:
                type: integer
                format: int64
              username:
                type:
                  - "string"
                  - "null"
              firstName:
                type: string
              lastName:
                type: string
              email:
                type: string
              password:
                type: string
              phone:
                type: string
              userStatus:
                type: integer
                format: int32
                description: User Status
        responses:
        "201":
          description: successful operation
        """           
        self._status_code = HTTPStatus.CREATED.value
        error_return = None
        try:
            data = json_decode(self.request.body)
            logging.debug(data)
        except:    
            logging.warn(error_return)
            self._status_code = HTTPStatus.BAD_REQUEST.value
            self.rest_response({'result':False})
            return

        if self.uri == '/1.0/maps/landmarks':
            #TODO validate with landmark Schema
            ret = LM.delete_way_points(data)
            self.rest_response(ret)

    async def put(self,*args):
        """
        Description end-point
        ---
        tags:
        - Example
        summary: Create user
        description: This can only be done by the logged in user.
        operationId: examples.api.api.createUser
        produces:
        - application/json
        parameters:
        - in: body
          name: body
          description: Created user object
          required: false
          schema:
            type: object
            properties:
              id:
                type: integer
                format: int64
              username:
                type:
                  - "string"
                  - "null"
              firstName:
                type: string
              lastName:
                type: string
              email:
                type: string
              password:
                type: string
              phone:
                type: string
              userStatus:
                type: integer
                format: int32
                description: User Status
        responses:
        "201":
          description: successful operation
        """           
        self._status_code = HTTPStatus.CREATED.value
        try:
            data = json_decode(self.request.body)
        except:
            self._status_code = HTTPStatus.BAD_REQUEST.value

        if self._status_code != HTTPStatus.CREATED.value:
            self.rest_response({'result':False})
        elif self.uri == '/1.0/missions/predefined_mission':
            if mission_cache.is_mission_duplication(mission_cache,data['remote_number']):
                event_model.save_mission_act({"status":"reject","action":data['remote_number'],"timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})    
                defaultStr = {"result": False, "values": {"state": "", "result": ""}, "msg": {"state": 0, "mission_state": -1, "missions": []}, "reason": "Mission is duplicated, reject this request temperatory"}
                self.rest_response(defaultStr)
            else:
                event_model.save_mission_act({"status":"success","action":data['remote_number'],"timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
                callData = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlStationCall remote_number",'service': "/mission_control/station_call",'args': {'remote_number':int(data['remote_number'])} }
                await self.ros_service_handler(callData,None)
        elif self.uri == '/1.0/missions' or self.uri == '/1.0/missions/':  #start/stop mission
            mission = mission_cache.get_mission(mission_cache)
            defaultStr = {
                "op": "service_response", "topic": "/mission_control/command","backendMsg":"Not support parameter", 
                "reason":"",
                "values":{"state":"","result":""},
                "result": False,"msg":{
                "state":0,    
                "mission_state":0,    
                "missions":[]} }
            if int(data['command']) == 1 or int(data['command']) == 2: # Not support stop, reload mission
                self.rest_response(defaultStr)
            elif int(data['command']) == 0 and mission['msg']['state'] == 0: # allow to start mission only when mission state is 0
                callData = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(data['command'])} }
                await self.ros_service_handler(callData,None)
            elif int(data['command']) == 3 or int(data['command']) == 4:
                callData = {'id':self.uri, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':int(data['command'])} }
                await self.ros_service_handler(callData,None)
            else:
                defaultStr['backendMsg'] = "Not support at this time"
                self.rest_response(defaultStr)

        elif self.uri == '/1.0/maps/landmarks':
            #TODO validate with landmark Schema
            ret = LM.insert_point(data)
            self.rest_response(ret)

    def on_finish(self):
        logging.debug("Finish REST API " + self.uri + " at " + str(datetime.now()))

    def write_error(self, status_code: int, **kwargs) -> None:
        logging.debug(super().write_error(status_code, **kwargs))

# class RESTMapController(tornado.web.RequestHandler):
#     def initialize(self):
#         self.status = 200

#     def prepare(self):
#         self.URI = self.request.path

# class RESTStatusController(tornado.web.RequestHandler):
#     pass

# class RESTLogController(tornado.web.RequestHandler):
#     pass

# class RESTSystemController(tornado.web.RequestHandler):
#     pass

# class RESTVDA5050Controller(tornado.web.RequestHandler):
#     pass
