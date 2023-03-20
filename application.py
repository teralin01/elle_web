import os
import asyncio
import logging
import tornado.web
import config
from control import controller_main, controller_rest, controller_system,controller_websocket
from control.system.ros_connection import ROSWebSocketConn as ROSConn
from control.system.mission_handler import MissionHandler as missionHandler
from control import controller_event
from control.system.logger import Logger
logger_init = Logger()

class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")
class DefaultFileFallbackHandler(tornado.web.StaticFileHandler):

    def validate_absolute_path(self, root, absolute_path):
        try:
            absolute_path = super().validate_absolute_path(root, absolute_path)
        except tornado.web.HTTPError:
            root = os.path.abspath(root)
            absolute_path = os.path.join(root, self.default_filename)
        return absolute_path
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/ws", controller_websocket.RosWebSocketHandler),
            (r"/1.0/missions",controller_rest.RESTHandler),
            (r"/1.0/missions/(.*)",controller_rest.RESTHandler),
            (r"/1.0/maps",controller_rest.RESTHandler),
            (r"/1.0/maps/(.*)",controller_rest.RESTHandler),
            (r"/1.0/map/(.*)",controller_system.RESTHandler),
            (r"/1.0/nav",controller_rest.RESTHandler),
            (r"/1.0/nav/(.*)",controller_rest.RESTHandler),
            (r"/1.0/network",controller_rest.RESTHandler),
            (r"/1.0/network/(.*)",controller_rest.RESTHandler),
            (r"/1.0/status/(.*)",controller_rest.RESTHandler),
            (r"/1.0/config/(.*)",controller_rest.RESTHandler),
            (r"/1.0/ros/(.*)",controller_rest.RESTHandler),
            (r"/1.0/event",controller_event.SSEHandler),
            (r'/login',controller_main.LoginHandler),
            (r'/logout',controller_main.LogoutHandler),
            (r'/static/(.*)',NoCacheStaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}),
            (r'/(.*)', DefaultFileFallbackHandler, {'path': 'vue','default_filename': 'index.html'}),
        ]
        super(Application,self).__init__(handlers,**config.settings )

        logging.debug("==== Tornado Server started ====")
        try:
            asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(ROSConn.initialize(ROSConn)))
        except Exception as exception:
            logging.error("## Init rosbridge error %s", str(exception))
        missionHandler()
    