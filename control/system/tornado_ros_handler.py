from http import HTTPStatus   #Refer to https://docs.python.org/3/library/http.html
import asyncio
import logging
from asyncio import Future
from datetime import datetime
from control.system.tornado_base_handler import TornadoBaseHandler
from control.system.ros_connection import ROSWebSocketConn as ROSConn
from control.system.cache_data import cache_subscribe_data as cache_subscription


class TornadoROSHandler(TornadoBaseHandler):
    def __init__(self,*args, **kwargs):
        super(TornadoROSHandler,self).__init__(*args, **kwargs)
        self._status_code = HTTPStatus.OK.value
        self.cache_hit = False
        
    async def ros_service_handler(self,calldata,service_result):
        service_future = Future()
        unique_uri = self.uri + "_"+ str(datetime.timestamp(datetime.now()))
        logging.debug("Service call ID %s ",unique_uri)
        calldata['id'] = unique_uri
        try:         
            await asyncio.wait_for( ROSConn.prepare_serviceCall_to_ROS(service_future,unique_uri,calldata) , timeout = self.rest_timeout_period)
            data = service_future.result()

            if None is service_result:
                self.cache_hit = True  # The result of ROS2 Service call is no need to cache
                self.rest_response(data)
            else:
                service_result.set_result(data)

        except asyncio.TimeoutError:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value
            logging.debug("##### REST Timeout, URL: %s ", unique_uri)
            ROSConn.clear_service_call(unique_uri)
            await ROSConn.reconnect()
            if None is service_result:
                self.rest_response(self.timeout_string)
            else:
                return False

        except Exception as exception:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value
            logging.debug("## REST Default Error "+ self.uri + " "+ str(exception) + " " + str(self.request.body))
            if None is service_result:
                self.rest_response(self.timeout_string)
            else:
                return False

    async def ros_subscribe_handler(self,calldata,sub_result,allow_cache):
        sub_future = Future()
        if allow_cache:
            subdata = cache_subscription.get(calldata['topic']) # Get cached subscribe data
        if  allow_cache and subdata is not None and subdata['data'] is not None:
            self.rest_response(subdata['data'])
        else:
            try:
                await asyncio.wait_for( ROSConn.prepare_subscribe_from_ros(sub_future,calldata,allow_cache) , timeout = self.rest_timeout_period)
                data = sub_future.result()
                if None is sub_result:
                    if data is not None:
                        self.rest_response(data)
                    else:
                        self._status_code = HTTPStatus.NO_CONTENT.value
                        self.rest_response("result:False")
                else:
                    sub_result.set_result(data)

            except asyncio.TimeoutError:
                self._status_code = HTTPStatus.REQUEST_TIMEOUT.value
                if None is sub_result:
                    self.rest_response(self.timeout_string)
                else:
                    return False     
    async def ros_unsubscribe_handler(self,calldata,need_return):
        unsub_future = Future()
        try:
            await asyncio.wait_for( ROSConn.prepare_unsubscribe_to_ROS(unsub_future,calldata) , timeout = self.rest_timeout_period)
            if not need_return:
                self.rest_response(unsub_future.result())
            else:
                data = unsub_future.result()
                if data['result'] is True:
                    return True
                else:
                    return False

        except asyncio.TimeoutError:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value
            if not need_return:
                self.rest_response(self.timeout_string)
            else:
                return False
 
    async def ros_publish_handler(self,calldata,need_return):
        publish_future = Future()
        try:
            await asyncio.wait_for( ROSConn.prepare_publish_to_ROS(publish_future,self.uri,calldata) , timeout = self.rest_timeout_period)
            if not need_return:
                self.cache_hit = True # The result of publish is no need to cache
                self.rest_response(publish_future.result())
            else:
                data = publish_future.result()
                if data['result'] is True:
                    return True
                else:
                    return False

        except asyncio.TimeoutError:
            self._status_code = HTTPStatus.REQUEST_TIMEOUT.value
            if not need_return:
                self.rest_response(self.timeout_string)
            else:
                return False
          