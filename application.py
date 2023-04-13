import os
import importlib.util
import json
import asyncio
import logging
import tornado.web
# from tornado_swagger.const import API_OPENAPI_3
# from tornado_swagger.setup import setup_swagger
# from tornado_swagger.setup import export_swagger
from packages.tornado_swagger.const import API_OPENAPI_3
from packages.tornado_swagger.setup import setup_swagger
from packages.tornado_swagger.setup import export_swagger
import config
from control import controller_main,controller_websocket
from control.system.ros_connection import ROSWebSocketConn as ROSConn
from control.system.mission_handler import MissionHandler as missionHandler
from control.system.json_validator import JsonValidator
from control.system.logger import Logger
logger_init = Logger()

NEED_EXPORT_SWAGGER = True
CONTROLLER_FILE_PATH = r'/root/elle/control/'

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
    _default_handler = [
        tornado.web.url(r"/ws", controller_websocket.RosWebSocketHandler), #bypass data to rosbridge
        tornado.web.url(r'/login',controller_main.LoginHandler),
        tornado.web.url(r'/logout',controller_main.LogoutHandler),
        tornado.web.url(r'/static/(.*)',NoCacheStaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")})
    ]
    _routes = []

    def __init__(self):
        self.dynamic_load_controller("1.0/") #load Rest API in /1.0 subfolder, and save to _handlers
        self._routes.extend(self._default_handler)
        logging.info(self._routes)
        # Use tornado-swagger to gen docs https://github.com/mrk-andreev/tornado-swagger/wiki
        setup_swagger(self._routes,
                        swagger_url="/api/doc",
                        description="This document focuses on standalone Elle environment",
                        api_version="1.0.0",
                        title="Elle REST API",
                        contact="tera.lin@axiomtek.com.tw",
                        api_definition_version=API_OPENAPI_3,
                    )
        try:
            self.json_validator = JsonValidator(export_swagger(self._routes, api_definition_version = API_OPENAPI_3)) # export openAPI obj to JSON validator
        except Exception as exception:
            logging.error(exception)
        
        if NEED_EXPORT_SWAGGER:
            swagger_specification = export_swagger(self._routes)
            file_path = open("./doc/docs.json", "w", encoding="utf-8")
            file_path.write(json.dumps(swagger_specification))
            file_path.close()

        super(Application,self).__init__(self._routes,**config.settings )

        logging.debug("==== Tornado Server started ====")
        try:
            asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(ROSConn.initialize(ROSConn)))
        except Exception as exception:
            logging.error("## Init rosbridge error %s", str(exception))
        missionHandler()



    def dynamic_load_controller(self,version):
        """
        Dynamic load file as tornado controller handler. 
        
        Step1: list file from folder
        Step2: dynamic load module according to file list
        Step3: append these module as tornado request handler and save to class variable: _routes
        
        :param self: the reference of current class
        :param version: the REST API version and folder name 
        :return: None
        """
        controller_folder = CONTROLLER_FILE_PATH + version
        for path in os.listdir(controller_folder):
            if os.path.isfile(os.path.join(controller_folder, path)) and not path.startswith('_') and path.endswith(".py"):
                file_name = path.strip('.py')
                try:
                    contrller_module = importlib.util.spec_from_file_location(  
                        file_name,controller_folder + path).loader.load_module()
                except AttributeError:
                    logging.error("Skip loading module %s due to attribute error ",file_name)
                    logging.debug(controller_folder + path)
                else:
                    self._routes.append(
                        tornado.web.url(r"/"+version+file_name.replace('_','/'),contrller_module.RequestHandler))
            else:
                logging.debug("Skip import controller module with filename %s: ",path)

