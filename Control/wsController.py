import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import datetime
import config
import json

rws = None 
browser_clients = set()

class ROSWebSocketConn:
    def __init__(self,bws):
        self.bws = bws

    def connect(self):
        global rws
        try:
            rosbridgeURI = "ws://"+config.settings['hostIP']+":"+config.settings['rosbridgePort']  
            rws = tornado.websocket.websocket_connect(
                    url= rosbridgeURI,
                    on_message_callback=self.recv_ros_message,
                    ping_interval=3,
                    ping_timeout=10,
                    )
            
            return rws
        except Exception:
            print("ROS bridge Connection Error")

    def reconnect(self):
        print("reconnect to rosbridge")
        self.connect()

    def get_rosConn(self):
        global rws
        if rws != None:
            print("RWS exist. return previous one")
            return rws
        else:
            return self.connect()
        
    @tornado.gen.coroutine
    def recv_ros_message(self,msg):
        if msg == None:
            print("Disconnected, reconnecting...")
            global rws
            rws = None
            yield tornado.gen.sleep(5)
            self.reconnect()
            
        if msg != None:
            global browser_clients
            data = json.loads(msg)
            
            if data['op'] == 'publish':
                print("topic: "+ data['topic'])
            
            if data['op'] == 'service_response':
                print(data['service'] + " " + "id" + data['id'] + " result" + str(data['result']))   
                
            for cbws in browser_clients:
                cbws.write_message(msg) 

# Websocket status code is defined in RFC6455 https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1  
# 1001 means browser terminate page
class RosWebSocketHandler(tornado.websocket.WebSocketHandler):
    
    rosConn = None
    global rws                    
    def check_origin(self, origin):
        return True
    
    @tornado.gen.coroutine
    def open(self):
        global browser_clients
        browser_clients.add(self)
        
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
        global browser_clients
        browser_clients.remove(self)
