import tornado.web
import tornado.ioloop
import logging
import config
from dataModel.AuthModel import AuthDB
from datetime import datetime
from jsonschema import validate
from control.system.RosConn import ROSWebSocketConn as ROSConn
from control.system.RosConn import cacheSubscribeData as cacheSub
from control.system.HWStatus import HWInfoHandler as HWInfo
from control.system.jsonValidatorSchema import missionSchema
from tornado.escape import json_decode, json_encode
from dataModel import landmarkModel as LM
from dataModel import configModel as Config
import asyncio
from asyncio import Future
import json
import pynmcli

cacheRESTData = dict()
TimeoutStr = {"result":False}
restTimeoutPeriod = 10
restCachePeriod = 5

logging.basicConfig(filename='/var/log/tornado.log', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(message)s')

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
        elif (datetime.now() - cache['lastUpdateTime']).seconds < restCachePeriod and cache['cacheData'] != None:
            self.cacheHit = True

        if config.settings['hostIP'] == "":
            config.settings['hostIP'] = self.request.host

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET,PUT,DELETE, OPTIONS')

    async def ROS_service_handler(self,calldata,serviceResult):
        serviceFuture = Future() 
        try:                    
            await asyncio.wait_for( ROSConn.prepare_serviceCall_to_ROS(ROSConn,serviceFuture,self.URI,calldata) , timeout = restTimeoutPeriod)
            if None == serviceResult:
                self.REST_response(serviceFuture.result())
            else:
                data = serviceFuture.result()
                serviceResult.set_result(data)        

        except asyncio.TimeoutError:
            self._status_code = 500
            if None != serviceResult:
                self.REST_response(TimeoutStr)
            else:
                return False

    async def ROS_subscribe_handler(self,calldata,subResult,allowCache):
        subFuture = Future()
        if allowCache:
            subdata = cacheSub.get(calldata['topic']) # Get cached subscribe data
        if  allowCache and subdata != None and subdata['data'] != None:
            self.REST_response(subdata['data'])
        else:
            try:                    
                await asyncio.wait_for( ROSConn.prepare_subscribe_from_ROS(ROSConn,subFuture,calldata,allowCache) , timeout = restTimeoutPeriod)
                data = subFuture.result()
                if None == subResult:
                    if data != None:
                        self.REST_response(data)
                    else:
                        self._status_code = 204 # No content 
                        self.REST_response("result:False")
                else:
                    subResult.set_result(data)
                    
            except asyncio.TimeoutError:
                self._status_code = 500
                if None == subResult:
                    self.REST_response(TimeoutStr)
                else:
                    return False     

    async def ROS_publish_handler(self,calldata,needReturn):
        pubFuture = Future()
        try:                    
            await asyncio.wait_for( ROSConn.prepare_publish_to_ROS(ROSConn,pubFuture,self.URI,calldata) , timeout = restTimeoutPeriod)
            if not needReturn:
                self.REST_response(pubFuture.result())
            else:
                data = pubFuture.result()
                if data['result'] == True:
                    return True
                else:
                    return False  

        except asyncio.TimeoutError:
            self._status_code = 500
            if not needReturn:
                self.REST_response(TimeoutStr)
            else:
                return False

    def REST_response(self,data):
        # Todo add log if necessary
        if self._status_code == 200:
            if data != None and not self.cacheHit:
                cacheRESTData.update({self.URI:{'cacheData':data,'lastUpdateTime':datetime.now()}})
        self.write(data)
        self.finish()       

    def CheckMissionIsUpdated(self,pubMission,existMissions):
        for mission in existMissions['msg']['missions']:
            if pubMission['name'] == mission['name'] and \
               pubMission['actions'][0]['coordinate']['x'] == mission['actions'][0]['coordinate']['x'] and \
               pubMission['actions'][0]['coordinate']['y'] == mission['actions'][0]['coordinate']['y']:
               return True

        return False
    
    async def get(self,*args):
        self._status_code = 200
        if self.cacheHit:
            logging.debug("Return cache data")
            self.REST_response(cacheRESTData.get(self.URI)['cacheData'])     
        
        elif self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/mission_control/states","type":"elle_interfaces/msg/MissionControlMissionArray"}
            await self.ROS_subscribe_handler(subscribeMsg,None,True)
            
        elif self.URI == '/1.0/maps' or self.URI == '/1.0/maps/GetMap':
            callData = {'id':self.URI, 'op':"call_service",'type': "nav_msgs/GetMap",'service': "/map_server/map",'args': {} }
            await self.ROS_service_handler(callData,None)  
                        
        elif self.URI == '/1.0/maps/map_meta' :  #TODO add map ID if support multiple maps
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/amcl_pose","type":"geometry_msgs/msg/PoseWithCovarianceStamped"}
            await self.ROS_subscribe_handler(subscribeMsg,None,False)
            
        elif self.URI == '/1.0/maps/speed_maps' :
            callData = {'id':self.URI, 'op':"call_service",'type': "nav_msgs/GetMap",'service': "/speed_filter_mask_server/map",'args': {} }
            await self.ROS_service_handler(callData,None)      
            
        elif self.URI == '/1.0/maps/keepout_maps' :
            callData = {'id':self.URI, 'op':"call_service",'type': "nav_msgs/GetMap",'service': "/keepout_filter_mask_server/map",'args': {} }
            await self.ROS_service_handler(callData,None)                         
            
        elif self.URI == '/1.0/maps/path':       #TODO add robotID to the URL in fleet version
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/plan","type":"nav_msgs/Path"}
            await self.ROS_subscribe_handler(subscribeMsg,None,False)
            
        elif self.URI == '/1.0/maps/costmap':    #TODO add robotID to the URL in fleet version
            callData = {'id':self.URI, 'op':"call_service",'type': "nav2_msgs/srv/GetCostmap",'service': "/global_costmap/get_costmap",'args': {} }
            await self.ROS_service_handler(callData,None)  
            
        elif self.URI == '/1.0/ros/service':    
            callData = {'id':self.URI, 'op':"call_service",'type': self.get_argument("ros_type"),'service': self.get_argument("ros_service") }
            await self.ROS_service_handler(callData,None)              
            
        elif self.URI == '/1.0/ros/service/withArgs':    
            callData = {'id':self.URI, 'op':"call_service",'type': self.get_argument("ros_type"),'service': self.get_argument("ros_service"),'args': {self.get_argument("ros_args")} }
            await self.ROS_service_handler(callData,None)              
                        
        elif self.URI == '/1.0/ros/subscribe':       
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic":self.get_argument("ros_topic"),"type":self.get_argument("ros_type")}
            await self.ROS_subscribe_handler(subscribeMsg,None,False)            
            
        elif self.URI == '/1.0/status/hardware':    #TODO add robotID to the URL in fleet version
            self.REST_response(HWInfo.get())
        
        elif self.URI == '/1.0/maps/landmarks':
            self.REST_response(json.dumps(LM.GetPoints()))
        
        elif self.URI == '/1.0/config/viewer':
            self.REST_response(json.dumps(Config.GetViewerConfig()))
            
        elif self.URI == '/1.0/network/wifilist':
            self.REST_response(pynmcli.NetworkManager.Device().wifi('list').execute())                        
            
        elif self.URI == '/1.0/network/connected':
            self.REST_response(pynmcli.NetworkManager.Connection().show().execute())            
            
        elif self.URI == '/1.0/event/sse':
            self.REST_response(pynmcli.NetworkManager.Connection().show().execute())                        
            
            
    async def post(self,*args):
        self._status_code = 201 # 201 means REST resource Created
        errRet = None
        try:
            data = json_decode(self.request.body)
            print(data)
            logging.debug(data)
            
        except:            
            print(errRet)
            logging.warn(errRet)
            self._status_code = 400 #Bad Request
            self.REST_response({'result':False})
            return
            
        if self.URI == '/1.0/missions' or self.URI == '/1.0/missions/':  
            try:
                errRet = validate(instance=data, schema=missionSchema)
            except:
                print(errRet)
                logging.warn(errRet)
                self._status_code = 400 #Bad Request
                self.REST_response({'result':False})
                return
            
            callData = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "/mission_control/mission",'msg':data['mission']}
            await self.ROS_publish_handler(callData,False)

        elif self.URI == '/1.0/nav/initialpose': 
            publishMsg = {"op":"publish","id":"RestTopics","topic":"/initialpose","type":"geometry_msgs/msg/PoseWithCovarianceStamped",'msg':data['msg']}
            await self.ROS_publish_handler(publishMsg,False)  

        elif self.URI == '/1.0/nav/goalpose': 
            try:
                errRet = validate(instance=data, schema=missionSchema)
            except:
                print(errRet)
                logging.warn(errRet)
                self._status_code = 400 #Bad Request
                self.REST_response({'result':False})
                return
                        
            publishMsg = {'type': "elle_interfaces/msg/MissionControlMission",'topic': "/mission_control/mission",'msg':data['mission']}
            subscribeMsg = {"op":"subscribe","id":"RestTopics","topic": "/mission_control/states","type":"elle_interfaces/msg/MissionControlMissionArray"}
            callData = {'id':self.URI, 'op':"call_service",'type': "elle_interfaces/srv/MissionControlCmd",'service': "/mission_control/command",'args': {'command':0} }
            
            ret = await self.ROS_publish_handler(publishMsg,True)
            if ret == True:    
                idx = 0
                while True: #Check mission state until mission updated
                    subFuture = Future()
                    await self.ROS_subscribe_handler(subscribeMsg,subFuture,False)
                    missionState = subFuture.result()
                    if missionState != None:
                        missionUpdateStatus = self.CheckMissionIsUpdated(data['mission'],missionState)
                        if missionUpdateStatus:
                            await self.ROS_service_handler(callData,None)
                            break
                        else:
                            if idx > 3:
                                self.REST_response({'result':False,"info":"Can't subscribe mission status from ROS"})
                                break
                            idx += 1
                            print("wait for mission time "+ str(idx))
                        await asyncio.sleep(1)
            else:
                self.REST_response({'result':False,"info":"Can't publish data to ROS"})
            
        elif self.URI == '/1.0/nav/move': 
            #example: {linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z:0}}"
            callData = {'type': "geometry_msgs/msg/Twist",'topic': "/cmd_vel",'msg':{
                'linear':{ 'x':data['forwardspeed'],'y':0,'z':0 },'angular':{'x':0,'y':0,'z':data['turn']}  }}
            await self.ROS_publish_handler(callData,False)                       
            
        elif self.URI == '/1.0/ros/publish': 
            publishMsg = {"op":"publish","id":"RestTopics","topic":data['ros_topic'],"type":data['ros_type'],'msg':data['msg']}
            await self.ROS_publish_handler(publishMsg,False)  

        elif self.URI == '/1.0/maps/landmarks':
            #TODO validate with landmark Schema 
            ret = LM.SetPoints(data)
            #ret = LM.UpsertPoints(data)
            self.REST_response(ret)

        elif self.URI == '/1.0/config/viewer':
            ret = Config.SetViewerConfig(data)
            self.REST_response(ret)
        
        elif self.URI == '/1.0/network/WiFiconnectionUP':
            # the SSID shoud be replace to device name. such as wlx08beac0e2a82
            result = pynmcli.NetworkManager.Connection().up(data['SSID']).execute()
            self.REST_response({"result": True, 'info':result})            
                        
        elif self.URI == '/1.0/network/WiFiconnectionDown':
            # the SSID shoud be replace to device name. such as wlx08beac0e2a82
            result = pynmcli.NetworkManager.Connection().down(data['SSID']).execute()
            self.REST_response({"result": True, 'info':result})            
                                    
        elif self.URI == '/1.0/network/connectWiFi':
            pynmcli.NetworkManager.Device().wifi("connect ",data['SSID']," password ",data['PASSWORD']).execute()
            self.REST_response({"result": True})            
        #nmcli d wifi connect my_wifi password <password>    
        
        elif self.URI == '/1.0/network/disconnectWiFi':
            result = pynmcli.NetworkManager.Device().disconnect(data['SSID']).execute()
            self.REST_response({"result": True, 'info':result})                        
            
        elif self.URI == '/1.0/maps/SetMap':
            
            #if success setmap via ROS service, then update map width/height to database 
            
            pass

    async def delete(self,*args):
        self._status_code = 201 # 201 means REST resource Created
        errRet = None
        try:
            data = json_decode(self.request.body)
            print(data)
            logging.debug(data)
            
        except:            
            print(errRet)
            logging.warn(errRet)
            self._status_code = 400 #Bad Request
            self.REST_response({'result':False})
            return        
        
        if self.URI == '/1.0/maps/landmarks':
            #TODO validate with landmark Schema 
            ret = LM.DelWaypoints(data)
            self.REST_response(ret)
        
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
            await self.ROS_service_handler(callData,None)        
        elif self.URI == '/1.0/maps/landmarks':
            #TODO validate with landmark Schema 
            ret = LM.InsertPoint(data)
            print(ret)
            self.REST_response(ret)            
        
    def on_finish(self):
        print("Finish REST API " + self.URI + " at " + str(datetime.now()))
        logging.debug("Finish REST API " + self.URI + " at " + str(datetime.now()))

    def write_error(self, status_code: int, **kwargs) -> None:
        print(super().write_error(status_code, **kwargs))
        
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

class SSEHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(SSEHandler, self).__init__(*args, **kwargs)
        self.set_header('Content-Type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        
    async def get(self,*args):
        i = 0 
        while True:
            if True:
                await asyncio.sleep(5)
                i = i + 1
                await self.out_put("Event sequence "+ str(i) )
            
    async def out_put(self,data):
        self.write('data:{'+data+'}\n\n')
        await self.flush()
