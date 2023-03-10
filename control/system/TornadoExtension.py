import tornado.web
import tornado.ioloop
from http import HTTPStatus   #Refer to https://docs.python.org/3/library/http.html
import asyncio
from asyncio import Future
from datetime import datetime
from control.system.RosConn import ROSWebSocketConn as ROSConn
from control.system.logger import Logger
logging = Logger()
from control.system.CacheData import cacheSubscribeData as cacheSub

TimeoutStr = {"result":False}
restTimeoutPeriod = 10

class BaseHandler(tornado.web.RequestHandler):
    def __init__(self):
        self.set_default_headers()        

    def set_default_headers(self):
        if self.application.settings.get('debug'): # debug mode is True then support CORS
            self.set_dev_cors_headers()    
    
    def get_current_user(self):
        return self.get_secure_cookie("user")    
    
    def set_dev_cors_headers(self):
        # For development only
        # Not safe for production
        origin = self.request.headers.get('Origin', '*') # use current requesting origin
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, x-requested-with, x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
        self.set_header('Access-Control-Expose-Headers', 'content-type, location, *, set-cookie')
        self.set_header('Access-Control-Request-Headers', '*')
        self.set_header('Access-Control-Allow-Credentials', 'true')
        
    async def ROS_service_handler(self,calldata,serviceResult):
        serviceFuture = Future()         
        uniqueURI = self.URI + "_"+ str(datetime.timestamp(datetime.now()))
        logging.debug("Service call ID "+uniqueURI)
        calldata['id'] = uniqueURI
        try:                    
            await asyncio.wait_for( ROSConn.prepare_serviceCall_to_ROS(ROSConn,serviceFuture,uniqueURI,calldata) , timeout = restTimeoutPeriod)
            data = serviceFuture.result()

            if None == serviceResult:
                self.cacheHit = True  # The result of ROS2 Service call is no need to cache
                self.REST_response(data)
            else:    
                serviceResult.set_result(data)        

        except asyncio.TimeoutError:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value
            logging.debug("##### REST Timeout "+ self.URI)
            ROSConn.clear_serviceCall(self.URI)
            await ROSConn.reconnect(ROSConn)
            if None == serviceResult:
                self.REST_response(TimeoutStr)
            else:
                return False

        except Exception as e:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value	
            logging.debug("## REST Default Error "+ self.URI + " "+ str(e) + " " + str(self.request.body))
            if None == serviceResult:
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
                        self._status_code = HTTPStatus.NO_CONTENT.value 
                        self.REST_response("result:False")
                else:
                    subResult.set_result(data)
                    
            except asyncio.TimeoutError:
                self._status_code = 504
                if None == subResult:
                    self.REST_response(TimeoutStr)
                else:
                    return False     
    async def ROS_unsubscribe_handler(self,calldata,needReturn):
        unsubFuture = Future()
        try:
            await asyncio.wait_for( ROSConn.prepare_unsubscribe_to_ROS(ROSConn,unsubFuture,calldata) , timeout = restTimeoutPeriod)
            if not needReturn:
                self.REST_response(unsubFuture.result())
            else:
                data = unsubFuture.result()
                if data['result'] == True:
                    return True
                else:
                    return False  
                
        except asyncio.TimeoutError:
            self._status_code = 504
            if not needReturn:
                self.REST_response(TimeoutStr)
            else:
                return False           
            
            
    async def ROS_publish_handler(self,calldata,needReturn):
        pubFuture = Future()
        try:                    
            await asyncio.wait_for( ROSConn.prepare_publish_to_ROS(ROSConn,pubFuture,self.URI,calldata) , timeout = restTimeoutPeriod)
            if not needReturn:
                self.cacheHit = True # The result of publish is no need to cache
                self.REST_response(pubFuture.result())
            else:
                data = pubFuture.result()
                if data['result'] == True:
                    return True
                else:
                    return False  

        except asyncio.TimeoutError:
            self._status_code = 504
            if not needReturn:
                self.REST_response(TimeoutStr)
            else:
                return False

    def REST_response(self,data):
        # Todo add log if necessary
        if self._status_code == HTTPStatus.OK.value:
            if data != None and not self.cacheHit:
                self.cacheRESTData.update({self.URI:{'cacheData':data,'lastUpdateTime':datetime.now()}})
        try:
            self.write(data)
            self.finish()       
        except Exception as e:
            logging.info("REST Response Error %s",str(e))        