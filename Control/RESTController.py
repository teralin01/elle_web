from numpy import NaN
import tornado.web
import tornado.ioloop
from dataModel.AuthModel import AuthDB
from datetime import datetime
from control.RosConn import ROSWebSocketConn as ROSConn
from control.RosConn import cacheSubscribeData as cacheSub
from tornado.escape import json_decode, json_encode
import asyncio

cacheRESTData = dict()
TimeoutStr = {"result":False}
restTimeoutPeriod = 10
restCachePeriod = 2

#TODO user authenication
# class BaseHandler(tornado.web.RequestHandler):
#     def get_current_user(self):
#         return self.get_secure_cookie("user")     
          
# class RESTHandler(BaseHandler):
class RESTHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.cacheHit = False
        self.future = asyncio.get_running_loop().create_future()
        global ROSConn
        global cacheRESTData
        global cacheSub
        
    def prepare(self):
        self.URI = self.request.path
        cache = cacheRESTData.get(self.URI)
        if cache == None:
            cacheRESTData.update({self.URI:{'cacheData':None,'lastUpdateTime':datetime.now()}})
        elif (datetime.now() - cache['lastUpdateTime']).seconds > restCachePeriod and cache['cacheData'] != None:
            self.cacheHit = True

    async def ROS_service_call_handler(self,calldata):
        try:                    
            await asyncio.wait_for( ROSConn.prepare_serviceCall_to_ROS(ROSConn,self.future,self.URI,calldata) , timeout = restTimeoutPeriod)
            self.REST_response(self.future.result())

        except asyncio.TimeoutError:
            self._status_code = 500
            self.REST_response(TimeoutStr)
            #TODO trigger rosbrodge process         

    async def ROS_subscribe_call_handler(self,calldata):
        subdata = cacheSub.get(calldata['topic'])
        if  subdata != None:
            self.REST_response(subdata['data'])
        else:
            try:                    
                await asyncio.wait_for( ROSConn.prepare_subscribe_from_ROS(ROSConn,self.future,calldata) , timeout = restTimeoutPeriod)
                data = self.future.result()
                if data != None:
                    self.REST_response(data)
                else:
                    self._status_code = 204 # No content 
                    self.REST_response("result:False")

            except asyncio.TimeoutError:
                self._status_code = 500
                self.REST_response(TimeoutStr)

    async def ROS_publish_handler(self,calldata):
        try:                    
            await asyncio.wait_for( ROSConn.prepare_publish_to_ROS(ROSConn,self.future,self.URI,calldata) , timeout = restTimeoutPeriod)
            self.REST_response(self.future.result())

        except asyncio.TimeoutError:
            self._status_code = 500
            self.REST_response(TimeoutStr)
        
                
    def REST_response(self,data):
        # Todo add log if necessary
        if self._status_code == 200:
            cacheRESTData.update({self.URI:{'cacheData':data,'lastUpdateTime':datetime.now()}})
        self.write(data)
        self.finish()       
        
    #/1.0/missions
    #/1.0/mission/missionId
    async def get(self,*args):
        self._status_code = 200
        if self.cacheHit:
            print("return cache data")
            self.REST_response(cacheRESTData.get(self.URI)['cacheData'])     
        
        elif self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/mission_control/state","type":"elle_interfaces/msg/MissionControlMission"}
            await self.ROS_subscribe_call_handler(subscribeMsg)
            
        elif self.URI == '/1.0/maps' or self.URI == '/1.0/maps/GetMap':
            callData = {'id':self.URI, 'op':"call_service",'type': "nav_msgs/srv/GetMap",'service': "/map_server/map",'args': {} }
            await self.ROS_service_call_handler(callData)  
                        
        elif self.URI == '/1.0/maps/map_meta' :  #TODO add map ID if support multiple maps
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/amcl_pose","type":"geometry_msgs/msg/PoseWithCovarianceStamped"}
            await self.ROS_subscribe_call_handler(subscribeMsg)
            
        elif self.URI == '/1.0/maps/path':       #TODO add robotID to the URL in fleet version
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/plan","type":"nav_msgs/Path"}
            await self.ROS_subscribe_call_handler(subscribeMsg)
            
        elif self.URI == '/1.0/maps/costmap':    #TODO add robotID to the URL in fleet version
            callData = {'id':self.URI, 'op':"call_service",'type': "nav2_msgs/srv/GetCostmap",'service': "/global_costmap/get_costmap",'args': {} }
            await self.ROS_service_call_handler(callData)  
            
    async def post(self,*args):
        self._status_code = 201 # 201 means REST resource Created
        try:
            data = json_decode(self.request.body)
        except:            
            self._status_code = 400 #Bad Request
            
        if self._status_code != 201:
            self.REST_response({'result':False})
        elif self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':  
            #TODO validate with missionSchema 
            callData = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "/mission_control/mission",'msg':data['actions']}
            await self.ROS_publish_handler(callData)
        
        #/1.0/mission/Id
    async def delete(self,*args):
        await self.post(self,*args)
        pass
    async def put(self,*args):
        self._status_code = 201 # 201 means REST resource Created
        try:
            data = json_decode(self.request.body)
        except:            
            self._status_code = 400 #Bad Request
            
        if self._status_code != 201:
            self.REST_response({'result':False})
        elif self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':  #start/stop mission
            callData = {'id':self.URI, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':data['command']} }
            await self.ROS_service_call_handler(callData)        
        
    def on_finish(self):
        print("Finish RST API " + self.URI + " at " + str(datetime.now()))

    def write_error(self, status_code: int, **kwargs) -> None:
        print(super().write_error(status_code, **kwargs))
        
class RESTMapController(tornado.web.RequestHandler): 
    def initialize(self):
        self.status = 200
        
    def prepare(self):
        self.URI = self.request.path

class RESTStatusController(tornado.web.RequestHandler): 
    pass

class RESTLogController(tornado.web.RequestHandler): 
    pass       

class RESTSystemController(tornado.web.RequestHandler): 
    pass

class RESTVDA5050Controller(tornado.web.RequestHandler): 
    pass