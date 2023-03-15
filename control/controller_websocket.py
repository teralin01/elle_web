import json
import datetime
import tornado.web
import tornado.websocket
import tornado.ioloop
import config
from control.system.ros_connection import ROSWebSocketConn as ROSConn
from control.system.ros_connection import subscribe_commands
from control.system.ros_connection import ros_commands
from control.system.ros_connection import ws_browser_clients
import logging

class RosWebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    async def open(self):
        global ws_browser_clients
        ws_browser_clients.add(self)
        logging.debug("WebSocket "+str(self)+ "opened at: " + str(datetime.datetime.now()))
        if config.settings['hostIP'] == "":
            config.settings['hostIP'] = self.request.host

    async def on_message(self, message):
        data = json.loads(message)
        if data["op"] == "subscribe":
            global subscribe_commands
            logging.debug("subscribe topic:" + data["topic"]+ " ID:  "+ data["id"])
            already_subscribe = subscribe_commands.get(data["topic"])
            subscribe_commands.set(data["topic"],str(self),data["id"])
            if not already_subscribe:
                await ROSConn.write(message)
        elif data["op"] == "unsubscribe":
            logging.debug("unsubscribe topic:" + data["topic"]+ " ID:  "+ data["id"])
            already_subscribe = subscribe_commands.get(data["topic"])
            if already_subscribe is not None:
                #subCmds.deleteOP(data['topic'])
                await ROSConn.write(message)

        elif data["op"] == "publish" or data["op"] == "advertise"  :
            logging.debug("publish topic " + data["topic"]+ " ID: "+ data["id"])
            await ROSConn.write(message)
        elif data["op"] == "call_service":
            global ros_commands
            logging.debug("Call service " + data["service"]+ " ID: "+ data["id"])
            ros_commands.set( data["id"],str(self))
            await ROSConn.write(message)

    def on_close(self):
        logging.debug("Get Browser close event "+ str(datetime.datetime.now()))
        target = str(self)
        global ros_commands
        global subscribe_commands
        subscribe_commands.removeBrowser(target)
        ros_commands.removeBrowser(target)

        global ws_browser_clients
        ws_browser_clients.remove(self)
