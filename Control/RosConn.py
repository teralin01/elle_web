from types import coroutine
import tornado.web
import tornado.websocket
import config
import json
from tornado.escape import json_encode
from control.RosUtility import ROSCommands
from control.RosUtility import SubscribeCommands 
from control.RosUtility import RESTServiceCall
subCmds = SubscribeCommands()
rosCmds = ROSCommands()
ws_browser_clients = set()

rws = None 


class ROSWebSocketConn:
    def __init__(self):
        print("ROSWebSocket init")
        self.RServiceCallPool = RESTServiceCall()
        # self.rws = None
        global rws 
        if rws == None:
            self.connect()

    def connect(self):
        global rws 
        try:
            rosbridgeURI = "ws://"+config.settings['hostIP']+":"+config.settings['rosbridgePort']  
            rws = tornado.websocket.websocket_connect(
                    url= rosbridgeURI,
                    # callback=self.maybe_retry_connection,
                    on_message_callback=self.recv_ros_message,
                    ping_interval=3,
                    ping_timeout=10,
                    )
            
            return rws
        except Exception:
            print("ROS bridge Connection Error, wait 3 second to retry")
    
    #Reference code https://www.georgeho.org/tornado-websockets/
    def maybe_retry_connection(self,future):
        global rws
        print("Disconnected ")
        try:
            rws = future.result()
        except:
            print("Could not reconnect, retrying in 3 seconds...")
            self.io_loop.call_later(3, self.connect)
            
    def reconnect(self):
        print("reconnect to rosbridge")
        self.connect()
        # TODO Notify browser to reconnect, in order to avoid request mission

    def get_rosConn(self,obj):
        if obj != None:
            self.RServiceCallPool.addOne(obj.URI,obj)   
        global rws
        if rws != None:
            print("RWS exist. return previous one")
            return rws
        else:
            return self.connect()
    
    @tornado.gen.coroutine
    def write_to_ros(self,URL,msg):
        self.RServiceCallPool.addOne(URL,self)
        
        global rws
        print(msg)
        if rws != None:
            yield rws.write_message(msg)
        else:    
            yield self.connect()
            yield rws.write_message(msg)

        ret = yield self.rCB(self)
        return ret

    @tornado.gen.coroutine
    def write(self,msg):
        global rws
        print(msg)
        if rws != None:
            yield rws.write_message(msg)
        else:    
            self.connect()
            yield rws.write_message(msg)

    @tornado.gen.coroutine
    def recv_ros_message(self,msg):
        global rws
        if msg == None:
            print("Disconnected, reconnecting...")
            
            self.rws = None
            yield tornado.gen.sleep(3)
            self.reconnect()
            
        else:
            global ws_browser_clients
            data = json.loads(msg)
            
            if data['op'] == 'publish':
                print("topic: "+ data['topic'])
                global subCmds
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
                    #Example to unsubscribe {"op":"unsubscribe","id":"subscribe:amcl_pose:4","topic":"amcl_pose"}
                    topicidstr = browsers[0]
                    topicid = topicidstr[list(topicidstr.keys())[0]]
                    message = {"op":"unsubscribe","id":topicid,"topic": data['topic'] }
                    print (message)
                    rws._result.write_message(json_encode(message))
                    subCmds.deleteOP(data['topic'])
                # Issue: not able to unsubscribe topic if more then two browser open the same topic. 
                
                
            if data['op'] == 'service_response':
                # print(data['service'] + " " + "id" + data['id'] + " result" + str(data['result']))   
                global rosCmds
                browser = rosCmds.get(data['id'])
                if browser != None:  # id match in rosCmds
                    for cbws in ws_browser_clients:
                        if str(cbws) == browser[0] : #return to first matching browser client
                            cbws.write_message(msg)
                            rosCmds.remove(data['id'])
                
                #send data back to REST client
                self.RServiceCallPool.callback(data)
                self.RServiceCallPool.removeKey(data['id'])
                # rosCmds.remove(data['id'])
