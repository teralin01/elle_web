import tornado.web
import tornado.websocket
import config
import json
import asyncio
import logging
from tornado.escape import json_encode
from datetime import datetime
from control.system.RosUtility import ROSCommands
from control.system.RosUtility import SubscribeCommands
from control.system.RosUtility import SubscribeTypes
from control.system.MissionHandler import MissionHandler

subCmds = SubscribeCommands()
rosCmds = ROSCommands()
topictable = SubscribeTypes()
ws_browser_clients = set()
missionHandler = MissionHandler()
rws = None
futureCB = {}
cacheSubscribeData = dict()
rosbridgeRetryPeriod = 3
rosbridgeRetryMax = 10
showdebug = True
recoveryMode = False # avoid auto unsubscribe topic during recovery mode
checkingROSConn = False

class ROSWebSocketConn:
    def __init__(self):
        global futureCB
        global rosCmds
        global ws_browser_clients
        global subCmds
        global cacheSubscribeData
        self.retryCnt = 0 
        self.queue = []
        self.connect(self)
        self.subscribe_default_topics(self)
        
    async def connect(self):
        global rws
        try:
            rosbridgeURI = "ws://"+config.settings['hostIP']+":"+config.settings['rosbridgePort']  
            rws = await tornado.websocket.websocket_connect(
                    url= rosbridgeURI,
                    on_message_callback=self.recv_ros_message,
                    max_message_size=int(config.settings['rosbridgeMsgSize']),
                    #callback=self.retry_connection
                    ping_interval=2,
                    ping_timeout=10,
                    )
            print("ROSBridge connected at: "+str(datetime.now()))
            return rws
        except Exception:
            print("ROS bridge connection fail, retry later")
            self.retryCnt = self.retryCnt+1
            if (self.retryCnt > rosbridgeRetryMax):
                print("Plan to trigger external command to restart rosbridge process")
            
            await asyncio.sleep(rosbridgeRetryPeriod)
            await self.connect(self)
    
    #Reference code https://www.georgeho.org/tornado-websockets/
    # def retry_connection(self):
    #     try:
    #         self.connect(self)
    #     except:
    #         print("Could not reconnect, retrying in 3 seconds...")
            
    async def reconnect(self):
        global rws 
        global recoveryMode
        
        if not recoveryMode:
            print("Try to connect rosbridge: "+ str(datetime.now()))
            recoveryMode = True
            self.retryCnt = 0 
            cacheSubscribeData.clear()
            
            await self.connect(self)  #only connect once even call reconnect multi times
        idx = 0
        while True:
            if rws != None: 
                if showdebug:
                    print("1: Submit predefined ROS command")
                recoveryMode = False
                await self.subscribe_default_topics(self)
                if showdebug:
                    print("2: Submit runtime ROS command")                
                await self.subscribe_runtime_topics(self)
                if showdebug:
                    print("3: Submit presubmit ROS command")                            
                await self.resubmit_write_cmds(self)
                break
            else:
                idx = idx+1
                if showdebug:
                    print("Wait for connecting rosbridge, sequence "+ int(idx) )
                if idx > 5:
                    await self.connect(self)
            await asyncio.sleep(3)
  
        # TODO Notify browser to reconnect, in order to avoid request mission
    
    async def prepare_publish_to_ROS(self,RESTCB,URL,data):
        advertiseMsg = {'op':'advertise','id':URL,'latch':False,'topic':data['topic'],'type':data['type']}
        await self.write(self,json_encode(advertiseMsg))
        
        publishMsg = {'op':'publish','id':URL,'latch':False,'topic':data['topic'],'type':data['type'],'msg':data['msg']}
        await self.write(self,json_encode(publishMsg))
        
        # Issue: Rosbridge Bug - unadvertise topic here might cause rosbridge crash, so skip this step.
        unadvertiseMsg = {'op':'unadvertise','id':URL,'topic':data['topic']}
        await self.write(self,json_encode(unadvertiseMsg))
        
        result = {'result':True}
        #success publish topic doesn't means the subscriber have already handler topic. 
        RESTCB.set_result(result)  # Save result to Rest callback

    async def subscribe_default_topics(self):
        #subscribe mission 
        subscribeMissionStr = {"op":"subscribe","id":"DefaultTopics","topic": "/mission_control/states","type":"elle_interfaces/msg/MissionControlMissionArray"}
        cacheSubscribeData.update({"/mission_control/states":{'data':None,'lastUpdateTime':datetime.now()}})
        await self.write(self,json_encode(subscribeMissionStr))

    async def subscribe_runtime_topics(self):
        global subCmds
        for key,value in subCmds.ros_Sub_Commands.items():
            type = topictable.get(key.lstrip("/")) # only subscribe to predefined types now
            if type != None:
                
                #skip newly subscribe topic in previous function
                if cacheSubscribeData.get(key) != None:
                    print("##Skip Key: "+ key)
                    continue
                
                subCmdStr = {"op":"subscribe","id":"ResubmitTopics_"+key,"topic": key,"type":type,"throttle_rate":0,"queue_length":0}
                await self.write(self,json_encode(subCmdStr))
            if showdebug:
                print("subscribe "+str(subCmdStr))
            

    async def resubmit_write_cmds(self):
        if showdebug:
            print("Resubmit queuing ROS command")
        length = len(self.queue)
        for i in range(length):
            cmd = self,self.queue[i]
            if cmd['topic'] != "/mission_control/states":
                await self.write(cmd)
            
        self.queue = []

    async def prepare_subscribe_from_ROS(self,RESTCB,subscribeMsg,needcache):
        prev = cacheSubscribeData.get(subscribeMsg['topic'])
        if needcache and prev != None and prev['data'] != None : # Cache hit, just return without new subscription
            result = {'result':True}
            RESTCB.set_result(result)
        else:                                      # Subscribe topic and wait for callback
            cacheSubscribeData.update({subscribeMsg['topic']:{'data':None,'lastUpdateTime':datetime.now()}})
            loop = asyncio.get_running_loop()
            futureObj = loop.create_future()
            futureCB.update({subscribeMsg['topic']:futureObj}) #append ros callback to dict
            loop.create_task(self.write(self,json_encode(subscribeMsg)))
            
            await futureObj
            data = futureObj.result() # Get result from ROS callback
            RESTCB.set_result(data)  # Save result to Rest callback
            del futureCB[subscribeMsg['topic']] # remove ros callback from dict

    async def prepare_unsubscribe_to_ROS(self,RESTCB,unsubscribeMsg):
        find = subCmds.get(unsubscribeMsg['topic'])
        if find == None : # Cache hit, just return without unsubscribe
            result = {'result':False,"info":"No subscription found"}
            RESTCB.set_result(result)
        else:                                     
            await self.write(self,json_encode(unsubscribeMsg))            
            RESTCB.set_result({'result':True})
            subCmds.deleteOP(unsubscribeMsg['topic'])
            cacheSubscribeData.update({unsubscribeMsg['topic']:None})
        
    async def prepare_serviceCall_to_ROS(self,RESTCB,URL,msg):
        loop = asyncio.get_running_loop()
        futureObj = loop.create_future()
        futureCB.update({URL:futureObj}) #append ros callback to dict
        loop.create_task(self.write(self,json_encode(msg)))
        
        await futureObj
        data = futureObj.result() # Get result from ROS callback
        RESTCB.set_result(data)  # Save result to Rest callback
        del futureCB[URL] # remove ros callback from dict

    async def write(self,msg):       
        global rws 
        global recoveryMode
        if showdebug:
            print(" -> write Message:"+msg)
        if rws != None:
            try:
                await rws.write_message(msg)
            except Exception:  # The rosbridge abnormal observe by write function
                if not recoveryMode:
                    self.queue = []
                    print("## write to rosbridge exception")
                    rws = None
                    await self.reconnect(self)    
                self.queue.append(msg)        
                
        elif not recoveryMode: # The rosbridge abnormal observe by recv_ros_message function
            self.queue = []
            self.queue.append(msg)        
            print("#### RWS == None and not recoveryMode")
            await self.reconnect(self)
        else:  # already stay in recovery mode
            self.queue.append(msg)        

    def clearROSConn():
        global checkingROSConn        
        if  checkingROSConn: #Still not receive service call response after 3 seconds
            global rws
            rws.close()
            rws = None
            print("Reconnect to rosbridge "+str(datetime.now()))
            asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(ROSWebSocketConn.reconnect(ROSWebSocketConn)))
                    
    def double_check_ros_conn():   
        # msg = {"op":"call_service","id":"TestRestServiceCall","service": "/amcl/get_state","type":"lifecycle_msgs/srv/GetState"}
        # asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(   ROSWebSocketConn.write(ROSWebSocketConn,json_encode(msg))   ))
                   
        loop = asyncio.get_event_loop()
        loop.call_later(3,ROSWebSocketConn.clearROSConn) 

    def recv_ros_message(msg): # receive data from rosbridge
        global rws
        global recoveryMode
        global checkingROSConn
        if msg == None:
            print("Recv nothing from rosbridge, checking rosbridge connection...")            
            checkingROSConn = True
            ROSWebSocketConn.double_check_ros_conn()
        else:
            if checkingROSConn:
                checkingROSConn = False
            data = json.loads(msg)
            if data['op'] == 'publish':
                if showdebug:
                    print(" <- topic: "+ data['topic'])
                browsers = subCmds.get(data['topic'])
                topic_alive = None
                if browsers != None:               # Browser client exist
                    for cbws in ws_browser_clients:   # Iterate all browser clients
                        for bws in browsers:
                            if str(cbws) == list(bws.keys())[0]:   # Find corresponding browser client
                                cbws.write_message(msg) 
                                topic_alive = True
                #callback to REST client  
                cb = futureCB.get(data['topic'])
                if cb != None:
                    cb.set_result(data)
                    topic_alive = True

                # if data['topic'] == "/mission_control/states":
                #    missionHandler.UpdateMissionStatus(data['msg'])

                #unsubscribe this topic if no browser client or REST client found
                if cacheSubscribeData.get(data['topic'])!= None: # Default subscribe topic, shch as mission status
                    cacheSubscribeData.update({data['topic']:{'data':msg,'lastUpdateTime':datetime.now()}})
                elif topic_alive == None and not recoveryMode : # No way to publish
                    print("--Unsubscribe topic: " + data['topic'])
                    topicidstr = browsers[0]
                    topicid = topicidstr[list(topicidstr.keys())[0]]
                    message = {"op":"unsubscribe","id":topicid,"topic": data['topic'] }
                    print (message)
                    rws.write_message(json_encode(message))
                    subCmds.deleteOP(data['topic'])

            if data['op'] == 'service_response':
                # print(data['service'] + " " + "id" + data['id'] + " result" + str(data['result']))   
                #send data back to web socket browser client
                browser = rosCmds.get(data['id'])
                if browser != None:  # id match in rosCmds
                    for cbws in ws_browser_clients:
                        if str(cbws) == browser[0] : #return to first matching browser client
                            cbws.write_message(msg)
                            rosCmds.remove(data['id'])

                #send data back to REST client
                cb = futureCB.get(data['id'])
                if cb != None:
                    cb.set_result(data)
