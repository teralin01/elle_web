import imp
import tornado.web
import os
import config
import datetime
from control import RESTController, SystemController,mainController, wsController
from control import statusController
from control import mapController
from control import missionController
from control import EventController

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
            (r"/ws", wsController.RosWebSocketHandler), 
            (r"/1.0/missions",RESTController.RESTHandler),
            (r"/1.0/missions/(.*)",RESTController.RESTHandler),
            (r"/1.0/maps",RESTController.RESTHandler),
            (r"/1.0/maps/(.*)",RESTController.RESTHandler),   
            (r"/1.0/map/(.*)",SystemController.RESTHandler),
            (r"/1.0/nav",RESTController.RESTHandler),
            (r"/1.0/nav/(.*)",RESTController.RESTHandler),            
            (r"/1.0/network",RESTController.RESTHandler),
            (r"/1.0/network/(.*)",RESTController.RESTHandler),                   
            (r"/1.0/status/(.*)",RESTController.RESTHandler),                     
            (r"/1.0/config/(.*)",RESTController.RESTHandler),     
            (r"/1.0/ros/(.*)",RESTController.RESTHandler),   
            (r"/1.0/event/(.*)",EventController.SSEHandler),   
            (r'/login',mainController.LoginHandler),
            (r'/logout',mainController.LogoutHandler),
            (r"/control/HardwareStatus", statusController.HWInfoHandler),
            (r"/control/missionController", missionController.InitHandler),
            (r"/control/mapController", mapController.InitHandler),
            (r'/view/dashboard/(.*)',tornado.web.StaticFileHandler,{"path":"view/dashboard/"}),
            (r'/view/(.*)',tornado.web.StaticFileHandler,{"path":"view"}),
            #(r'/static/(.*)',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}), 
            (r'/static/(.*)',NoCacheStaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}), 
            (r'/(.*)', DefaultFileFallbackHandler, {'path': 'vue','default_filename': 'index.html'}),
        ]
        super(Application,self).__init__(handlers,**config.settings )
        
        print("Tornado Server start at " + str(datetime.datetime.now()))

     