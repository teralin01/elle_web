import os
import json
import asyncio
import logging
import tornado.web
from tornado_swagger.setup import setup_swagger
from tornado_swagger.setup import export_swagger
import config
from control import controller_main, controller_rest, controller_system,controller_websocket
from control.system.ros_connection import ROSWebSocketConn as ROSConn
from control.system.mission_handler import MissionHandler as missionHandler
from control import controller_event
from control.system.logger import Logger
logger_init = Logger()

NEED_EXPORT_SWAGGER = False

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
    _handlers = [
        tornado.web.url(r"/ws", controller_websocket.RosWebSocketHandler),
        tornado.web.url(r"/1.0/missions",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/missions/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/maps",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/maps/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/map/(.*)",controller_system.RESTHandler),
        tornado.web.url(r"/1.0/nav",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/nav/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/network",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/network/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/status/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/config/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/ros/(.*)",controller_rest.RESTHandler),
        tornado.web.url(r"/1.0/event",controller_event.SSEHandler),
        tornado.web.url(r'/login',controller_main.LoginHandler),
        tornado.web.url(r'/logout',controller_main.LogoutHandler),
        tornado.web.url(r'/static/(.*)',NoCacheStaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}),
        tornado.web.url(r'/(.*)', DefaultFileFallbackHandler, {'path': 'vue','default_filename': 'index.html'}),
        ]

    def __init__(self):
        # Use tornado-swagger to gen docs https://github.com/mrk-andreev/tornado-swagger/wiki
        setup_swagger(self._handlers)

        if NEED_EXPORT_SWAGGER:
            swagger_specification = export_swagger(self._handlers)
            file_path = open("./doc/docs.json", "w", encoding="utf-8")
            file_path.write(json.dumps(swagger_specification))
            file_path.close()

        super(Application,self).__init__(self._handlers,**config.settings )

        logging.debug("==== Tornado Server started ====")
        try:
            asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(ROSConn.initialize(ROSConn)))
        except Exception as exception:
            logging.error("## Init rosbridge error %s", str(exception))
        missionHandler()
    