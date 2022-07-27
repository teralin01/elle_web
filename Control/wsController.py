import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import datetime
import config
import json
from tornado.escape import json_encode
from control.RosUtility import ROSCommands
from control.RosUtility import SubscribeCommands 

rws = None 
browser_clients = set()
subCmds = SubscribeCommands()
rosCmds = ROSCommands()

class ROSWebSocketConn:
    def __init__(self,bws):
        self.bws = bws

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

    def get_rosConn(self):
        global rws
        if rws != None:
            print("RWS exist. return previous one")
            return rws
        else:
            return self.connect()
        
    @tornado.gen.coroutine
    def recv_ros_message(self,msg):
        global rws
        if msg == None:
            print("Disconnected, reconnecting...")
            
            rws = None
            yield tornado.gen.sleep(5)
            self.reconnect()
            
        else:
            global browser_clients
            data = json.loads(msg)
            
            if data['op'] == 'publish':
                print("topic: "+ data['topic'])
                global subCmds
                browsers = subCmds.get(data['topic'])
                topic_alive = None
                if browsers != None:               # Browser client exist
                    for cbws in browser_clients:   # Iterate all browser clients
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
                
            if data['op'] == 'service_response':
                print(data['service'] + " " + "id" + data['id'] + " result" + str(data['result']))   
                global rosCmds
                browser = rosCmds.get(data['id'])
                for cbws in browser_clients:
                    if str(cbws) == browser[0] : #return to first matching browser
                        cbws.write_message(msg)
                        rosCmds.remove(data['id'])
                
class RosWebSocketHandler(tornado.websocket.WebSocketHandler):
    rosConn = None
    global rws                    
    def check_origin(self, origin):
        return True
    
    @tornado.gen.coroutine
    def open(self):
        global browser_clients
        browser_clients.add(self)
        print(self)
        
        # Get host IP from client request. Instead of get local IP from docker
        config.settings['hostIP'] = self.request.host 
        print("WebSocket opened at: " + str(datetime.datetime.now()))
        if self.rosConn == None:
            self.rosConn = yield ROSWebSocketConn(self).get_rosConn()
            if (self.rosConn == None):
                print("Fail to connect to rosbridge")

    @tornado.gen.coroutine
    def on_message(self, message):
        self.browserMsg = message
        data = json.loads(message)
        if data["op"] == "subscribe":
            global subCmds
            print("subscribe topic:" + data["topic"]+ " ID:  "+ data["id"])
            already_subscribe = subCmds.get(data["topic"])
            # subCmds.add(data["topic"],str(self))
            subCmds.set(data["topic"],str(self),data["id"])
            if not already_subscribe:
                self.write_to_ros(message)
        elif data["op"] == "publish" or data["op"] == "advertise"  :
            print("publish topic " + data["topic"]+ " ID: "+ data["id"])
            self.write_to_ros(message)
        elif data["op"] == "call_service":
            global rosCmds
            print("Call service " + data["service"]+ " ID: "+ data["id"])
            rosCmds.set( data["id"],str(self))
            self.write_to_ros(message)

    @tornado.gen.coroutine
    def write_to_ros(self,msg):   
        if (self.rosConn.close_code == None):
            yield self.rosConn.write_message(msg)
        else:
            yield tornado.gen.sleep(6)
            if (self.rosConn.close_code == None):
                yield self.rosConn.write_message(msg)

    def on_close(self):
        print("Get Browser close event ")
        target = str(self)
        global rosCmds
        global subCmds
        subCmds.removeBrowser(target)
        rosCmds.removeBrowser(target)        
        
        global browser_clients
        browser_clients.remove(self)
