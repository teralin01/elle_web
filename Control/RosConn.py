from types import coroutine
import tornado.web
import tornado.websocket
import config
import json
import asyncio
from tornado.escape import json_encode
from control.RosUtility import ROSCommands
from control.RosUtility import SubscribeCommands 

subCmds = SubscribeCommands()
rosCmds = ROSCommands()
ws_browser_clients = set()

class ROSWebSocketConn:
    def __init__(self):
        self.rws = None
        self.futureCB = {}
        global rosCmds
        global ws_browser_clients
        global subCmds

    async def connect(self):
        try:
            rosbridgeURI = "ws://"+config.settings['hostIP']+":"+config.settings['rosbridgePort']  
            self.rws = await tornado.websocket.websocket_connect(
                    url= rosbridgeURI,
                    # callback=self.maybe_retry_connection,
                    on_message_callback=self.recv_ros_message,
                    ping_interval=3,
                    ping_timeout=10,
                    )
            
            return self.rws
        except Exception:
            print("ROS bridge Connection Error, wait 3 second to retry")
    
    #Reference code https://www.georgeho.org/tornado-websockets/
    def maybe_retry_connection(self,future):
        print("Disconnected ")
        try:
            self.rws = future.result()
        except:
            print("Could not reconnect, retrying in 3 seconds...")
            self.io_loop.call_later(3, self.connect)
            
    def reconnect(self):
        print("reconnect to rosbridge")
        self.connect()
        # TODO Notify browser to reconnect, in order to avoid request mission

    def get_rosConn(self):
        if self.rws != None:
            print("RWS exist. return previous one")
            return self.rws
        else:
            return self.connect()
    
    async def prepare_write_to_ROS(self,RESTCB,URL,msg):
        loop = asyncio.get_running_loop()
        futureObj = loop.create_future()
        self.futureCB.update({URL:futureObj}) #append ros callback to dict
        loop.create_task(self.write(msg,futureObj))
        
        await futureObj
        data = futureObj.result() # Get result from ROS callback
        RESTCB.set_result(data)  # Save result to Rest callback
        del self.futureCB[URL] # remove ros callback from dict

    async def write(self,msg,futureObj):        
        if self.rws != None:
            await self.rws.write_message(json_encode(msg))
        else:    
            await self.connect()
            await self.rws.write_message(json_encode(msg))


    @tornado.gen.coroutine
    def recv_ros_message(self,msg):
        if msg == None:
            print("Disconnected, reconnecting...")
            self.rws = None
            yield tornado.gen.sleep(3)
            self.reconnect()
            
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
                if topic_alive == None: # No way to publish
                    print("Unsubscribe topic: " + data['topic'])
                    topicidstr = browsers[0]
                    topicid = topicidstr[list(topicidstr.keys())[0]]
                    message = {"op":"unsubscribe","id":topicid,"topic": data['topic'] }
                    print (message)
                    self.rws._result.write_message(json_encode(message))
                    subCmds.deleteOP(data['topic'])
                # Issue: not able to unsubscribe topic if more then two browser open the same topic. 
                
                
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
                cb = self.futureCB.get(data['id'])
                if cb != None:
                    cb.set_result(data)
