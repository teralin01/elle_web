import imp
import tornado.web
import os
import config

from control import mainController
from control import statusController
from control import mapController
from control import missionController

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", mainController.MainHandler),
            (r"/main", mainController.MainHandler),
            (r"/dashboard", mainController.DashboardHandler),
            (r"/status", statusController.InitHandler),
            (r'/setCookie',mainController.setCookieHandler),
            (r'/getCookie',mainController.getCookieHandler),
            (r'/clearCookie',mainController.ClearCookieHandler),
            (r'/login',mainController.LoginHandler),
            (r'/view/dashboard',mainController.DashboardHandler),
            
            # redirect default static content to path /static 
            (r'/static/(.*)$',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}),
            (r'/view/(.*)$',tornado.web.StaticFileHandler,{"path":"view"}),
            (r"/parseURLPath/(\w*)/(\w*)", mainController.URLPathHandler),
            (r'/(.*)$',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"Static"),"default_filename":"index.html"})
        ]
        super(Application,self).__init__(handlers,**config.settings )