import json
import asyncio
import os
import logging
from datetime import datetime
import nest_asyncio
from tornado.escape import json_encode
import tornado.web
import tornado.websocket
import config
from control.system.ros_utility import ROSCommands
from control.system.ros_utility import SubscribeCommands
from control.system.ros_utility import SubscribeTypes
from control.system.mission_handler import MissionHandler as missionHandler
from control.system.cache_data import scheduler as TornadoScheduler
from control.system.cache_data import cache_subscribe_data

subscribe_commands = SubscribeCommands()
ros_commands = ROSCommands()
topic_table = SubscribeTypes()
ws_browser_clients = set()

ROSBRIDGE_RETRY_PERIOD = 1
ROSBRIDGE_RETRY_MAX = 3
ROSBRIDGE_RETRY_DELAY_TIME = 2
RESUMIT_PERIOD = 5e-3   # 5 ms sleep
SERVICE_CALL_TIMEOUT = 4


class ROSWebSocketConn:
    def __init__(self):
        self.initialize()

    async def initialize(self):  #init by instance, not class
        self.retry_counter = 0
        self.queue = []
        self.ros_websocket_connection = None
        self.recovery_mode = False # avoid auto unsubscribe topic during recovery mode
        self.checking_ros_connection = False
        self.future_callback = {}
        await self.connect(self)
        await self.subscribe_default_topics(self)

    def get_state(self,state_tag):
        if state_tag == "recovery_mode":
            return self.recovery_mode
        elif state_tag == "checking_ros_connection":
            return self.checking_ros_connection
        elif state_tag == "ros_websocket_connection":
            return self.ros_websocket_connection
        elif state_tag == "future_callback":
            return self.future_callback
        else:
            return None

    async def connect(self):
        try:
            rosbridge_uri = "ws://"+config.settings['hostIP']+":"+config.settings['rosbridgePort']
            self.ros_websocket_connection = await tornado.websocket.websocket_connect(
                    url= rosbridge_uri,
                    on_message_callback=self.recv_ros_message,
                    max_message_size=int(config.settings['rosbridgeMsgSize']),
                    #callback=self.retry_connection
                    ping_interval=1,
                    ping_timeout=5,
                    )
            logging.debug("ROSBridge connected at: %s",str(datetime.now()))

        except Exception as exception:
            logging.error("ROS bridge connection fail, retry later - %s", str(exception))
            self.retry_counter = self.retry_counter+1
            if (self.retry_counter > ROSBRIDGE_RETRY_MAX):
                logging.info("Calling Restart rosbridge shell")
                cmd = "sh ./control/system/kill_rosbridge.sh"
                returned_value = os.system(cmd)  # returns the exit code in unix
                logging.info('returned value: %s' , returned_value)
                # Rosbridge restart procedure is handle at rosbridge_websocket.launcy.py  -> Node -> respwan=True

            await asyncio.sleep(ROSBRIDGE_RETRY_PERIOD)
            await self.connect(self)

    async def reconnect(self):
        ros_websocket_connection = self.ros_websocket_connection
        logging.debug(ros_websocket_connection)

        if not self.recovery_mode:
            logging.info("Try to connect rosbridge: %s",str(datetime.now()))
            self.recovery_mode = True
            self.retry_counter = 0
            if ros_websocket_connection is not None:
                ros_websocket_connection.close()
                ros_websocket_connection = None
            # cacheSubscribeData.clear()

            await self.connect(self)  #only connect once even call reconnect multi times
        idx = 0
        while True:
            if self.ros_websocket_connection is not None:
                # TornadoScheduler.add_job(missionHandler.ResetMissionStatus, run_date = datetime.now())
                
                logging.debug("1: Submit predefined ROS command")
                self.recovery_mode = False
                await self.subscribe_default_topics(self)
                
                logging.debug("2: Submit runtime ROS command")
                await self.subscribe_runtime_topics(self)
                
                logging.debug("3: Submit presubmit ROS command")
                await self.resubmit_write_cmds(self)
                break
            else:
                idx = idx+1
                
                logging.debug("Wait for connecting rosbridge, sequence %s", str(idx) )
                if idx > ROSBRIDGE_RETRY_MAX:
                    await self.connect(self)
            await asyncio.sleep(ROSBRIDGE_RETRY_PERIOD)
        
    async def prepare_publish_to_ROS(self,rest_callback,url,data):
        advertise_message = {'op':'advertise','id':url,'latch':False,'topic':data['topic'],'type':data['type']}
        await self.write(json_encode(advertise_message))

        publish_message = {'op':'publish','id':url,'latch':False,'topic':data['topic'],'type':data['type'],'msg':data['msg']}
        await self.write(json_encode(publish_message))

        # Issue: Rosbridge Bug - unadvertise topic here might cause rosbridge crash, so skip this step.
        unadvertise_message = {'op':'unadvertise','id':url,'topic':data['topic']}
        await self.write(json_encode(unadvertise_message))

        result = {'result':True}
        #success publish topic doesn't means the subscriber have already handler topic. 
        rest_callback.set_result(result)  # Save result to Rest callback

    async def subscribe_default_topics(self):
        #subscribe mission
        subscribe_mission_string = {"op":"subscribe","id":"DefaultTopics","topic": "mission_control/states","type":"elle_interfaces/msg/MissionControlMissionArray"}
        cache_subscribe_data.update({"mission_control/states":{'data':None,'lastUpdateTime':datetime.now()}})
        await self.write(json_encode(subscribe_mission_string))
        await asyncio.sleep(RESUMIT_PERIOD)
        #subscribe AMCL
        subscribe_amcl_string = {"op":"subscribe","id":"DefaultTopics","topic": "amcl_pose","type":"geometry_msgs/msg/PoseWithCovarianceStamped"}
        cache_subscribe_data.update({"amcl_pose":{'data':None,'lastUpdateTime':datetime.now()}})
        await self.write(json_encode(subscribe_amcl_string))

    async def subscribe_runtime_topics(self):
        global subscribe_commands
        for key,value in subscribe_commands.ros_Sub_Commands.items():
            topic_type = topic_table.get(key.lstrip("/")) # only subscribe to predefined types now
            if topic_type is not None:
                #skip newly subscribe topic in previous function
                if cache_subscribe_data.get(key) is not None:
                    logging.debug("##Skip Key: %s", key)
                    continue

                subscribe_command_string = {"op":"subscribe","id":"ResubmitTopics_"+key,"topic": key,"type":topic_type,"throttle_rate":0,"queue_length":0}
                await self.write(json_encode(subscribe_command_string))
            
            logging.debug("subscribe %s",str(subscribe_command_string))


    async def resubmit_write_cmds(self):
        logging.debug("Resubmit queuing ROS command")

        if hasattr(self,'queue'):
            length = len(self.queue)
            for i in range(length):
                cmd = self.queue[i]

                logging.debug("resubmit cmd from queue %s",cmd)
                if not "mission_control/states" in cmd  and not "TestRestServiceCall" in cmd : #skip defualt topic and test connection call
                    await asyncio.sleep(RESUMIT_PERIOD)
                    await self.write(cmd)

        self.queue = []
    @classmethod
    async def prepare_subscribe_from_ros(self,rest_callback,subscribe_message,needcache):
        future_callback = ROSWebSocketConn.get_state(ROSWebSocketConn,"future_callback")
        prev = cache_subscribe_data.get(subscribe_message['topic'])
        if needcache and prev is not None and prev['data'] is not None : # Cache hit, just return without new subscription
            result = {'result':True}
            rest_callback.set_result(result)
        else:                                      # Subscribe topic and wait for callback
            cache_subscribe_data.update({subscribe_message['topic']:{'data':None,'lastUpdateTime':datetime.now()}})
            loop = asyncio.get_running_loop()
            future_object = loop.create_future()
            future_callback.update({subscribe_message['topic']:future_object}) #append ros callback to dict
            loop.create_task(self.write(json_encode(subscribe_message)))

            await future_object
            data = future_object.result() # Get result from ROS callback
            rest_callback.set_result(data)  # Save result to Rest callback
            del future_callback[subscribe_message['topic']] # remove ros callback from dict
    @classmethod
    async def prepare_unsubscribe_to_ROS(self,rest_callback,unsubscribe_message):
        find = subscribe_commands.get(unsubscribe_message['topic'])
        if find is None : # Cache hit, just return without unsubscribe
            result = {'result':False,"info":"No subscription found"}
            rest_callback.set_result(result)
        else:
            await self.write(json_encode(unsubscribe_message))
            rest_callback.set_result({'result':True})
            subscribe_commands.deleteOP(unsubscribe_message['topic'])
            cache_subscribe_data.update({unsubscribe_message['topic']:None})

    def clear_service_call(self,url):
        del self.future_callback[url]

    @classmethod
    async def prepare_serviceCall_to_ROS(self,rest_callback,url,msg):
        recovery_mode = ROSWebSocketConn.get_state(ROSWebSocketConn,"recovery_mode")
        future_callback = ROSWebSocketConn.get_state(ROSWebSocketConn,"future_callback")
        loop = asyncio.get_running_loop()
        future_object = loop.create_future()
        future_callback.update({url:future_object}) #append ros callback to dict
        loop.create_task(self.write(json_encode(msg)))

        try:
            if recovery_mode:
                asyncio.sleep(1)
            await future_object
            data = future_object.result() # Get result from ROS callback
            rest_callback.set_result(data)  # Save result to Rest callback

        except asyncio.CancelledError:
            logging.error("## Service call error due to asyncio.CancelledError. Form URL: %s", url)
            await self.reconnect(self)
            rest_callback.set_result({"result":False,
                               "values":{"state":"","result":""},
                               "msg":{
                                "state":0,    
                                "mission_state":-1,    
                                "missions":[]},
                                "reason":"CancelledError exception, Rosbridge connection abnormal"})  # Save result to Rest callback

        except Exception as exception_content:
            logging.error("## Service call error: msg %s",str(exception_content) )
            rest_callback.set_result({"result":False,"reason":str(exception_content)})  # Save result to Rest callback

        finally:
            del future_callback[url]

    def update_write_queue(self,msg):
        for item in self.queue:
            if item == msg:  #Avoid duplicate message
                logging.debug("Skip duplicate cmd: %s" , msg)
                return

        self.queue.append(msg)
    @classmethod
    async def write(self,msg):
        logging.debug(" -> write Message: %s ", msg)
        ros_websocket_connection = ROSWebSocketConn.get_state(ROSWebSocketConn,"ros_websocket_connection")
        recovery_mode = ROSWebSocketConn.get_state(ROSWebSocketConn,"recovery_mode")
        checking_ros_connection = ROSWebSocketConn.get_state(ROSWebSocketConn,"checking_ros_connection")
        
        if ros_websocket_connection is not None:
            try:
                await ros_websocket_connection.write_message(msg)
            except Exception as exception_content:  # The rosbridge abnormal observe by write function
                if not recovery_mode and not checking_ros_connection:
                    self.queue = []
                    logging.error("## write to rosbridge exception %s", str(exception_content))
                    ros_websocket_connection = None
                    await self.reconnect(self)

                if not hasattr(self,'queue'):
                    self.queue = []
                self.update_write_queue(self,msg)

        elif not recovery_mode: # The rosbridge abnormal observe by recv_ros_message function
            self.queue = []
            self.update_write_queue(self,msg)
            logging.debug("#### RWS == None and not recoveryMode")
            await self.reconnect(self)
        else:  # already stay in recovery mode
            if not hasattr(self,'queue'):
                self.queue = []
            self.update_write_queue(self,msg)

    def clearROSConn():
        checking_ros_connection = ROSWebSocketConn.get_state(ROSWebSocketConn,"checking_ros_connection")
        ros_websocket_connection = ROSWebSocketConn.get_state(ROSWebSocketConn,"ros_websocket_connection")
        logging.info("Before Clear ROS connection")
        if  checking_ros_connection: #Still not receive service call response after 5 seconds
            if ros_websocket_connection is not None:
                ros_websocket_connection.close()
                ros_websocket_connection = None
            logging.info("Clear ROS connection, trying to reconnect")
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(ROSWebSocketConn.reconnect(ROSWebSocketConn)))

    def testROSConn():
        nest_asyncio.apply()
        msg = {"op":"call_service","id":"TestRestServiceCall","service": "/amcl/get_state","type":"lifecycle_msgs/srv/GetState"}
        asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(ROSWebSocketConn.write(json_encode(msg))))

    def double_check_ros_conn():
        loop = asyncio.get_event_loop()
        loop.call_later(ROSBRIDGE_RETRY_DELAY_TIME-1,ROSWebSocketConn.testROSConn)  #send test reqeust before retry  
        loop.call_later(ROSBRIDGE_RETRY_DELAY_TIME,ROSWebSocketConn.clearROSConn)

    def recv_ros_message(msg): # receive data from rosbridge. this callback is synchronous not async
        recovery_mode = ROSWebSocketConn.get_state(ROSWebSocketConn,"recovery_mode")
        checking_ros_connection = ROSWebSocketConn.get_state(ROSWebSocketConn,"checking_ros_connection")
        future_callback = ROSWebSocketConn.get_state(ROSWebSocketConn,"future_callback")
        if msg is None:
            logging.info("## Recv None from rosbridge, something wrong. CheckRosConn: %s", str(checking_ros_connection) + " RecoverMode:"+str(recovery_mode))        
            if checking_ros_connection is False and not recovery_mode : #only check connection once
                ROSWebSocketConn.double_check_ros_conn()
            checking_ros_connection = True
        else:
            if checking_ros_connection:
                checking_ros_connection = False
            data = json.loads(msg)
            data['values'] = {"state":"","result":""}
            data['reason'] = ""
            if data['op'] == 'publish':
                logging.debug(" <- topic: %s", data['topic'])
                browsers = subscribe_commands.get(data['topic'])
                topic_alive = None
                if browsers is not None:               # Browser client exist
                    for cbws in ws_browser_clients:   # Iterate all browser clients
                        for bws in browsers:
                            try:
                                if len(list(bws.keys())) > 0 and str(cbws) == list(bws.keys())[0]:   # Find corresponding browser client
                                    cbws.write_message(msg)
                                    topic_alive = True
                            except Exception as exception_content:
                                logging.error("ROS publish exception 1 %s", str(exception_content))
                #callback to REST client
                cb = future_callback.get(data['topic'])
                if cb is not None:
                    try:
                        cb.set_result(data)
                    except Exception as exception_content:
                        logging.error("Ros publish exception 2 %s", str(exception_content))
                    topic_alive = True
                #unsubscribe this topic if no browser client or REST client found
                if cache_subscribe_data.get(data['topic']) is not None: # Default subscribe topic, shch as mission status
                    if data['topic'] == "mission_control/states":
                        try:
                            TornadoScheduler.add_job(missionHandler.update_mission_status, \
                                args = [msg], run_date = datetime.now())
                        except Exception as exception_content:
                            logging.error("## Publish SSE fail msg: %s", str(exception_content))
                    else:
                        cache_subscribe_data.update({data['topic']:{'data':msg,'lastUpdateTime':datetime.now()}})
                elif topic_alive is None and not recovery_mode : # No way to publish
                    logging.debug("--Unsubscribe topic: %s", data['topic'])
                    try:
                        topicidstr = browsers[0]
                        topicid = topicidstr[list(topicidstr.keys())[0]]
                        message = {"op":"unsubscribe","id":topicid,"topic": data['topic'] }
                        ROSWebSocketConn.write(json_encode(message))
                        subscribe_commands.deleteOP(data['topic'])
                    except Exception as exception_content:
                        logging.error("the browser client had been removed from ws_browser_clients- %s",exception_content)

            if data['op'] == 'service_response':
                logging.debug("Service Response: server name=> %s, service id=> %s, service result=> %s", data['service'] , data['id'] , str(data['result']))                
                try:
                    browser = ros_commands.get(data['id'])
                    if browser is not None:  # id match in rosCmds
                        for cbws in ws_browser_clients:
                            if len(browser) > 0 and str(cbws) == browser[0]:
                                cbws.write_message(msg)
                                ros_commands.remove(data['id'])
                except Exception as exception_content:
                    logging.error("Service response error 1 %s", str(exception_content))
                else:
                    data['values'] = {"state":"","result":""}
                    data['reason'] = ""
                    #send data back to REST client
                    cb = future_callback.get(data['id'])
                    if cb != None:
                        try:
                            cb.set_result(data)
                        except Exception as exception_content:
                            logging.error("Service response error 2 %s", str(exception_content))
