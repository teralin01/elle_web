from http import HTTPStatus   #Refer to https://docs.python.org/3/library/http.html
import asyncio
from asyncio import Future
from datetime import datetime
from control.system.logger import Logger
logging = Logger()
from control.system.TornadoBaseHandler import TornadoBaseHandler
from control.system.CacheData import cacheSubscribeData as cacheSub
from control.system.RosConn import ROSWebSocketConn as ROSConn

class TornadoROSHandler(TornadoBaseHandler):
    def __init__(self,*args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)     

    async def ROS_service_handler(self,calldata,serviceResult):
        serviceFuture = Future()         
        uniqueURI = self.URI + "_"+ str(datetime.timestamp(datetime.now()))
        logging.debug("Service call ID "+uniqueURI)
        calldata['id'] = uniqueURI
        try:                    
            await asyncio.wait_for( ROSConn.prepare_serviceCall_to_ROS(ROSConn,serviceFuture,uniqueURI,calldata) , timeout = self.restTimeoutPeriod)
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
            await ROSConn.reconnect(self.ROSConn)
            if None == serviceResult:
                self.REST_response(self.TimeoutStr)
            else:
                return False

        except Exception as e:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value	
            logging.debug("## REST Default Error "+ self.URI + " "+ str(e) + " " + str(self.request.body))
            if None == serviceResult:
                self.REST_response(self.TimeoutStr)
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
                await asyncio.wait_for( ROSConn.prepare_subscribe_from_ROS(ROSConn,subFuture,calldata,allowCache) , timeout = self.restTimeoutPeriod)
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
                    self.REST_response(self.TimeoutStr)
                else:
                    return False     
    async def ROS_unsubscribe_handler(self,calldata,needReturn):
        unsubFuture = Future()
        try:
            await asyncio.wait_for( ROSConn.prepare_unsubscribe_to_ROS(ROSConn,unsubFuture,calldata) , timeout = self.restTimeoutPeriod)
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
                self.REST_response(self.TimeoutStr)
            else:
                return False           
            
            
    async def ROS_publish_handler(self,calldata,needReturn):
        pubFuture = Future()
        try:                    
            await asyncio.wait_for( ROSConn.prepare_publish_to_ROS(ROSConn,pubFuture,self.URI,calldata) , timeout = self.restTimeoutPeriod)
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
                self.REST_response(self.TimeoutStr)
            else:
                return False
          