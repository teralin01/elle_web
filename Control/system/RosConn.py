import tornado.web
import tornado.websocket
import config
import json
import asyncio
from tornado.escape import json_encode
from datetime import datetime
from control.system.RosUtility import ROSCommands
from control.system.RosUtility import SubscribeCommands 

subCmds = SubscribeCommands()
rosCmds = ROSCommands()
ws_browser_clients = set()
rws = None
futureCB = {}
cacheSubscribeData = dict()

class ROSWebSocketConn:
    def __init__(self):
        global futureCB
        global rosCmds
        global ws_browser_clients
        global subCmds
        global cacheSubscribeData
        self.connect(self)
        # self.subscribe_default_topics(self)
        
    async def connect(self):
        global rws
        try:
            rosbridgeURI = "ws://"+config.settings['hostIP']+":"+config.settings['rosbridgePort']  
            rws = await tornado.websocket.websocket_connect(
                    url= rosbridgeURI,
                    # callback=self.maybe_retry_connection,
                    on_message_callback=self.recv_ros_message,
                    ping_interval=3,
                    ping_timeout=10,
                    max_message_size=int(config.settings['rosbridgeMsgSize'])
                    )
            
            return rws
        except Exception:
            print("ROS bridge Connection Error, wait 3 second to retry")
    
    #Reference code https://www.georgeho.org/tornado-websockets/
    def maybe_retry_connection(self,future):
        print("Disconnected ")
        try:
            self.rws = future.result()
        except:
            print("Could not reconnect, retrying in 3 seconds...")
            self.io_loop.call_later(3, self.reconnect)
            
    def reconnect(self):
        print("reconnect to rosbridge")
        self.connect()
        # TODO Notify browser to reconnect, in order to avoid request mission
    
    async def prepare_publish_to_ROS(self,RESTCB,URL,data):
        advertiseMsg = {'op':'advertise','id':URL,'latch':False,'topic':data['topic'],'type':data['type']}
        await self.write(self,json_encode(advertiseMsg))
        
        publishMsg = {'op':'publish','id':URL,'latch':False,'topic':data['topic'],'type':data['type'],'msg':data['msg']}
        await self.write(self,json_encode(publishMsg))
        
        # Issue: Rosbridge Bug - unadvertise topic here might cause rosbridge crash, so skip this step.
        # unadvertiseMsg = {'op':'unadvertise','id':URL,'topic':data['topic']}
        # await self.write(self,json_encode(unadvertiseMsg))
        
        result = {'result':True}
        #success publish topic doesn't means the subscriber have already handler topic. 
        RESTCB.set_result(result)  # Save result to Rest callback

    async def subscribe_default_topics(self):
        #subscribe mission 
        subscribeMissionStr = {"op":"subscribe","id":"RestTopics","topic": "/mission_control/state","type":"elle_interfaces/msg/MissionControlMission"}
        cacheSubscribeData.update({"/mission_control/states":{'data':None,'lastUpdateTime':datetime.now()}})
        await self.write(self,json_encode(subscribeMissionStr))

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
        if rws != None:
            await rws.write_message(msg)
        else:    
            await self.connect(self)
            await rws.write_message(msg)

    def recv_ros_message(msg):
        global rws
        if msg == None:
            print("Recv nothing from rosbridge, clear rosbridge connection...")
            rws = None

        else:
            data = json.loads(msg)
            if data['op'] == 'publish':
                print("topic: "+ data['topic'])
                browsers = subCmds.get(data['topic'])
                topic_alive = None
                if browsers != None:               # Browser client exist
                    for cbws in ws_browser_clients:   # Iterate all browser clients
                        for bws in browsers:
                            if str(cbws) == list(bws.keys())[0]:   # Find corresponding browser client
                                cbws.write_message(msg) 
                                topic_alive = True

                #unsubscribe this topic if no browser client found
                if cacheSubscribeData.get(data['topic'])!= None:
                    cacheSubscribeData.update({data['topic']:{'data':msg,'lastUpdateTime':datetime.now()}})
                elif topic_alive == None : # No way to publish
                    print("Unsubscribe topic: " + data['topic'])
                    topicidstr = browsers[0]
                    topicid = topicidstr[list(topicidstr.keys())[0]]
                    message = {"op":"unsubscribe","id":topicid,"topic": data['topic'] }
                    print (message)
                    rws.write_message(json_encode(message))
                    subCmds.deleteOP(data['topic'])
                # Issue: not able to unsubscribe topic if more then two browser open the same topic. 
                                    
                cb = futureCB.get(data['topic'])
                if cb != None:
                    cb.set_result(data)

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
