import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import datetime;

rosbridgeURI = "ws://localhost:9090"

class ROSWebSocketConn:
    def __init__(self,bws):
        self.bws = bws
        self.rws = None 

    @tornado.gen.coroutine
    def connect(self):
        try:
            self.rws = yield tornado.websocket.websocket_connect(
            url=rosbridgeURI,
            on_message_callback=self.recv_ros_message,
            ping_interval=10,
            ping_timeout=30,
            )
        except Exception:
            print("ROS bridge Connection Error")

    def reconnect(self):
        print("reconnect to rosbridge")
        self.connect()

    @tornado.gen.coroutine
    def get_rosConn(self):
        yield self.connect()
        return self.rws
    
    @tornado.gen.coroutine
    def recv_ros_message(self,msg):
        if (self.bws.close_code == None): 
            if (msg != None):
                yield self.bws.write_message(msg)     
        else:
            # If browser close websocket, then close the rosbirdge socket 
            # print(self.bws.close_code,self.bws.close_reason )
            self.rws.close(1001)
            #TODO only keep one web socket connection between tornado and rosbridge 
        
    @tornado.gen.coroutine
    def close(self):
        if self.bws.close_code != None:
            yield self.reconnect()

# Websocket status code is defined in RFC6455 https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1  
# 1001 means browser terminate page
class RosWebSocketHandler(tornado.websocket.WebSocketHandler):
    browser_clients = set()
    rosConn = None
        
    def check_origin(self, origin):
        return True
    
    @tornado.gen.coroutine
    def open(self):
        RosWebSocketHandler.browser_clients.add(self)
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
            print("subscribe topic:" + data["topic"]+ " ID:  "+ data["id"])
        elif data["op"] == "publish" or data["op"] == "advertise"  :
            print("publish topic " + data["topic"]+ " ID: "+ data["id"])
        elif data["op"] == "call_service":
            print("Call service " + data["service"]+ " ID: "+ data["id"])

        self.write_to_ros(message)

    @tornado.gen.coroutine
    def write_to_ros(self,msg):
        if (self.rosConn.close_code == None):
            yield self.rosConn.write_message(msg)
        else:
            yield tornado.gen.sleep(3)
            if (self.rosConn.close_code == None):
                yield self.rosConn.write_message(msg)
            else:
                print("Error, can't send to rosbridge, maybe rosbridge is crash") 
                # TODO: restart rosbridge

    def on_close(self):
        RosWebSocketHandler.browser_clients.remove(self)
