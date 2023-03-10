import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import datetime
import json
import config
from control.system.RosConn import ROSWebSocketConn as ROSConn
from control.system.RosConn import subCmds 
from control.system.RosConn import rosCmds
from control.system.RosConn import ws_browser_clients

class RosWebSocketHandler(tornado.websocket.WebSocketHandler):       
    def check_origin(self, origin):
        return True
        
    async def open(self):
        global ws_browser_clients
        ws_browser_clients.add(self)
        print("WebSocket "+str(self)+ "opened at: " + str(datetime.datetime.now()))
        if config.settings['hostIP'] == "":
            config.settings['hostIP'] = self.request.host
           
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
        elif data["op"] == "unsubscribe":
            print("unsubscribe topic:" + data["topic"]+ " ID:  "+ data["id"])
            already_subscribe = subCmds.get(data["topic"])
            if already_subscribe != None:
                #subCmds.deleteOP(data['topic'])
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
        print("Get Browser close event "+ str(datetime.datetime.now()))
        target = str(self)
        global rosCmds
        global subCmds
        subCmds.removeBrowser(target)
        rosCmds.removeBrowser(target)        
        
        global ws_browser_clients
        ws_browser_clients.remove(self)