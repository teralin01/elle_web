from numpy import NaN
import tornado.web
import tornado.ioloop
from dataModel.AuthModel import AuthDB
from datetime import datetime
from control.RosConn import ROSWebSocketConn as ROSConn
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
class rMissionHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.cacheHit = False
        self._status_code = 200
        self.future = asyncio.get_running_loop().create_future()
        global ROSConn
        global cacheRESTData
        
    def prepare(self):
        self.URI = self.request.path
        cache = cacheRESTData.get(self.URI)
        if cache == None:
            cacheRESTData.update({self.URI:{'cacheData':None,'lastUpdateTime':datetime.now()}})
        elif (datetime.now() - cache['lastUpdateTime']).seconds > restCachePeriod and cache['cacheData'] != None:
            self.cacheHit = True

    async def ROS_service_call_handler(self,calldata):
        try:                    
            await asyncio.wait_for( ROSConn.prepare_write_to_ROS(ROSConn,self.future,self.URI,calldata) , timeout = restTimeoutPeriod)
            self.REST_response(self.future.result())

        except asyncio.TimeoutError:
            self._status_code = 500
            self.REST_response(TimeoutStr)
            #TODO trigger rosbrodge process         

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
        if self.cacheHit:
            print("return cache data")
            self.REST_response(cacheRESTData.get(self.URI)['cacheData'])     
        
        elif self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':
            callData = {'id':self.URI, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command"}
            await self.ROS_service_call_handler(callData)


    async def post(self,*args):
        self._status_code == 201 # 201 means REST resource Created
        data = json_decode(self.request.body)
        if self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':
            callData = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "/mission_control/mission",'msg':data['actions']}
            await self.ROS_publish_handler(callData)
        
        #/1.0/mission/Id
    def delete(self):
        pass
    def put(self):
        pass
    def on_finish(self):
        #TODO if cacheData exist, then update it
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