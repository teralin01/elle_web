import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import datetime
import json
from control.RosConn import ROSWebSocketConn as ROSConn
from control.RosConn import subCmds 
from control.RosConn import rosCmds
from control.RosConn import ws_browser_clients

class RosWebSocketHandler(tornado.websocket.WebSocketHandler):       
    def check_origin(self, origin):
        return True
    
    async def open(self):
        global ws_browser_clients
        ws_browser_clients.add(self)
        print("WebSocket opened at: " + str(datetime.datetime.now()))

    async def on_message(self, message):
        self.browserMsg = message
        data = json.loads(message)
        if data["op"] == "subscribe":
            global subCmds
            print("subscribe topic:" + data["topic"]+ " ID:  "+ data["id"])
            already_subscribe = subCmds.get(data["topic"])
            subCmds.set(data["topic"],str(self),data["id"])
            if not already_subscribe:
                await ROSConn.write(ROSConn,message)
        elif data["op"] == "publish" or data["op"] == "advertise"  :
            print("publish topic " + data["topic"]+ " ID: "+ data["id"])
            await ROSConn.write(ROSConn,message)
        elif data["op"] == "call_service":
            global rosCmds
            print("Call service " + data["service"]+ " ID: "+ data["id"])
            rosCmds.set( data["id"],str(self))
            await ROSConn.write(ROSConn,message)    

    def on_close(self):
        print("Get Browser close event ")
        target = str(self)
        global rosCmds
        global subCmds
        subCmds.removeBrowser(target)
        rosCmds.removeBrowser(target)        
        
        global ws_browser_clients
        ws_browser_clients.remove(self)
