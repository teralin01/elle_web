from numpy import NaN
import tornado.web
import tornado.ioloop
from dataModel.AuthModel import AuthDB
from datetime import datetime
from control.RosConn import ROSWebSocketConn
import asyncio

cacheRESTData = dict()
TimeoutStr = {"result":False}
waitPeriod = 10

ROSConn = ROSWebSocketConn()
#TODO user authenication
# class BaseHandler(tornado.web.RequestHandler):
#     def get_current_user(self):
#         return self.get_secure_cookie("user")     
          
# class RESTHandler(BaseHandler):
class rMissionHandler(tornado.web.RequestHandler):
    def initialize(self,UniqueCommand):
        self.UniqueCommand = UniqueCommand
        self.cacheHit = False
        self._status_code = 200
        self.future = asyncio.get_running_loop().create_future()
        global ROSConn
        
    def prepare(self):
        global cacheRESTData
        self.URI = self.request.path
        targetRaw = self.UniqueCommand.getRow('requestURI',[self.URI])
        
        if  len(targetRaw) == 0:
            self.UniqueCommand.insert({'requestURI':self.URI,'requestProtocol':"http",'lastRequestTime':datetime.now()})
        # elif targetRaw['cacheData'] != NaN:
        #     #TODO the following code have not yet verified. the datatype of time1 may not a string type
        #     time1 = datetime.strptime(targetRaw['lastRequestTime'].apply(str), '%d/%m/%y %H:%M:%S')
        #     time2 = datetime.now()
        #     if (time1 - time2).seconds > 120: 
        #         print("Cache data hit, return without insert to client request")
        #         self.cachHit = true
        # 
        

    #/1.0/missions
    #/1.0/mission/missionId
    async def get(self,*args):
        if self.cacheHit:
            print("return cache data")
            self.write(cacheRESTData.get(self.URI))     
        
        elif self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':
            callData = {'id':self.URI, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command"}
            await self.ROS_request_handler(callData)

    async def ROS_request_handler(self,calldata):
        try:                    
            await asyncio.wait_for( ROSConn.prepare_write_to_ROS(self.future,self.URI,calldata) , timeout=10)
            self.REST_response(self.future.result())
            #TODO if status_code = 200,  Save data to cache table self.UniqueCommand
                
        except asyncio.TimeoutError:
            self._status_code = 500
            self.REST_response(TimeoutStr)
            #TODO trigger rosbrodge process         
            
            
    def REST_response(self,data):
        # Todo add log if necessary

        self.write(data)
        self.finish()        
        
    def post(self):
        pass
        #/1.0/mission/Id
    def delete(self):
        pass
    def put(self):
        pass
    def on_finish(self):
        #TODO if cacheData exist, then update it
        print("Finish RST API " + self.URI + " at " + str(datetime.now()))
        self.UniqueCommand.update('requestURI',self.URI,'lastRequestTime',datetime.now())

    def write_error(self, status_code: int, **kwargs) -> None:
        print(super().write_error(status_code, **kwargs))
        
class RESTMapController(tornado.web.RequestHandler): 
    def initialize(self,UniqueCommand):
        self.UniqueCommand = UniqueCommand
        self.status = 200
        
    def prepare(self):
        self.URI = self.request.path
        #TODO cache REST: get Raw, if cachedata exist and lastRequestTime < 2 second, then return directlly. 
        targetRaw = self.UniqueCommand.getRow('requestURI',[self.URI])
        
        time1 = targetRaw['lastRequestTime']
        time2 = datetime.now()
        if (time1 - time2).seconds > 120: 
            print("Cache data hit, return without insert to client request")
        
        if  len(targetRaw) == 0:
            self.UniqueCommand.insert({'requestURI':self.URI,'requestProtocol':"http",'lastRequestTime':datetime.now()})
        elif targetRaw['cacheData'] != NaN:
            time1 = targetRaw['lastRequestTime']
            time2 = datetime.now()
            if (time1 - time2).seconds > 120: 
                print("Cache data hit, return without insert to client request")
        
        
        # self.ClientRequests.insert({'requestURI':self.URI,'callback':self, 'issueTime':datetime.now()})


class RESTStatusController(tornado.web.RequestHandler): 
    pass

class RESTLogController(tornado.web.RequestHandler): 
    pass       

class RESTSystemController(tornado.web.RequestHandler): 
    pass

class RESTVDA5050Controller(tornado.web.RequestHandler): 
    pass