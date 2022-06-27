import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import datetime;

rosbridgeURI = "ws://localhost:9090"    

class RosSocketServiceCall:
    def __init__(self, bws, msg):
        self.bws = bws
        self.callMsg = msg
        self.ws = None
        self.ServiceCaller()
        
    @tornado.gen.coroutine
    def ServiceCaller(self):     
        yield self.connect()
        self.ws.write_message(self.callMsg)        

    @tornado.gen.coroutine        
    def connect(self):
        try:
            self.ws = yield tornado.websocket.websocket_connect(
            url=rosbridgeURI,
            on_message_callback=self.write_ros_message,
            ping_interval=10,
            ping_timeout=30,
            )              
        except Exception:
            print("ROS Connection Error")        
            self.bws.close(990)
                                    
    def write_ros_message(self,data):
        if (self.bws.close_code == None): 
            if (data != None):
                self.bws.write_message(data)         
            self.ws.close(996)
            self.bws.close(996)

    def close(self):
        print (self.close_code)
        self.bws.close(997)                                
                    
class RosSocketPublisher:
    def __init__(self, bws, msg):
        self.bws = bws
        self.topicMsg = msg
        self.ws = None
        self.SocketSubscriber()
        
    @tornado.gen.coroutine
    def SocketSubscriber(self):     
        try:
            yield self.connect()
            yield self.ws.write_message(self.topicMsg)  
            self.bws.close(999)
            self.ws.close(999)
        except Exception:
            print("ROS Connection Error")        
            self.bws.close(990)
            
    @tornado.gen.coroutine        
    def connect(self):
        self.ws = yield tornado.websocket.websocket_connect(
        url=rosbridgeURI,
        ping_interval=10,
        ping_timeout=30,
        )    

    def close(self):
        print (self.close_code)
        self.bws.close(998)
        
class RosSocketSubscriber:
    def __init__(self, bws, msg):
        self.bws = bws
        self.topicMsg = msg
        self.ws = None
        self.SocketSubscriber()
        
    @tornado.gen.coroutine
    def write_ros_message(self,data):
        if (self.bws.close_code == None): 
            if (data != None):
                yield self.bws.write_message(data)     
        else:
            print(self.bws.close_code,self.bws.close_reason )
            self.ws.close(1001)
            
    @tornado.gen.coroutine
    def SocketSubscriber(self):     
        yield self.connect()
        self.ws.write_message(self.topicMsg)  
    
    @tornado.gen.coroutine        
    def connect(self):
        try:
            self.ws = yield tornado.websocket.websocket_connect(
            url=rosbridgeURI,
            callback=self.on_rosconnected,
            on_message_callback=self.write_ros_message,
            ping_interval=10,
            ping_timeout=30,
            )
        except Exception:
            print("ROS Connection Error")        
            self.bws.close(990)
                            
    def on_rosconnected(self,data):
        callbacadata = data.result()
        #TODO log to database
    
    def keep_alive(self):
        if self.bws is None:
            self.ws.close(1001)
        elif self.ws is None:
            self.connect()
            
    def disonnectRos(self):
        self.ws.close(1001)
        
# Websocket status code is defined in RFC6455 https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1  
# 1001 means browser terminate page
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    ct = datetime.datetime.now()
    browser_clients = set()
    ros_clients = set()
    ws = None
    browserMsg = None
    def check_origin(self, origin): 
        return True
    async def open(self):          
        WebSocketHandler.browser_clients.add(self)
        print("WebSocket opened: " + str(self.ct))
        self.ct = datetime.datetime.now()
        
    async def webSocketPublisher(self):
        print("start websocket publish" + str(self.ct))
        # TODO add publish command
    
    
    async def on_message(self, message):  
        self.browserMsg = message
        data = json.loads(message)   
        if data["op"] == "subscribe":
            print("subscribe topic:" + data["topic"]+ " ID:  "+ data["id"] )
            conn = RosSocketSubscriber(self,message)
            WebSocketHandler.ros_clients.add(conn)
            
        elif data["op"] == "publish" or data["op"] == "advertise"  :
            print("publish topic " + data["topic"]+ " ID: "+ data["id"] )
            conn = RosSocketPublisher(self,message)
            WebSocketHandler.ros_clients.add(conn)
        
        elif data["op"] == "call_service":    
            print("Call service " + data["service"]+ " ID: "+ data["id"] )
            conn = RosSocketServiceCall(self,message)
            WebSocketHandler.ros_clients.add(conn)
            
    def on_close(self):  
        for client in self.ros_clients:
            if client.bws == self:
                if( client.bws.close_code <= 999):
                    print("Socket closed by tornado: " + str(client.bws.close_code))
                else: 
                    client.disonnectRos()
        WebSocketHandler.browser_clients.remove(self)
        



 