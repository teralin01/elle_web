import json
import tornado.web
import tornado.websocket
import datetime;

rosbridgeURI = "ws://localhost:9090"    
        
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    ct = datetime.datetime.now()
    ws = None
    browserMsg = None
    def check_origin(self, origin):  #允許外網連入
        return True
    async def open(self):          
        print("WebSocket opened" + str(self.ct))
        self.ct = datetime.datetime.now()

    @tornado.gen.coroutine
    def write_ros_message(self,data):
        print("Try to write back to browser")
        self.write_message(data) 
        
    async def webSocketSubscriber(self, message):
        print("start websocket subscribe" + str(self.ct))
        
        ws = await tornado.websocket.websocket_connect(
        url=rosbridgeURI,
        # callback=self.maybe_retry_connection,
        on_message_callback=self.write_ros_message,
        #ping_interval=10,
        #ping_timeout=30,
        )
        
        print( "ROSbridge client connected " + str(self.ct))
        await ws.write_message(message)  
    
    async def on_message(self, message):  
        self.browserMsg = message
        data = json.loads(message)   
        if data["op"] == "subscribe":
            print("subscribe " + data["topic"]+ "  "+ data["id"] )
            await self.webSocketSubscriber(message)
            
    def on_close(self):  
        print("WebSocket closed")
        



 