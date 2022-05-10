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
            (r'/setCookie',mainController.setCookieHandler),
            (r'/getCookie',mainController.getCookieHandler),
            (r'/clearCookie',mainController.ClearCookieHandler),
            (r'/login',mainController.LoginHandler),
            (r'/logout',mainController.LogoutHandler),
            (r"/parseURLPath/(\w*)/(\w*)", mainController.URLPathHandler),
            (r"/control/statusController", statusController.InitHandler),
            (r"/control/missionController", missionController.InitHandler),
            (r"/control/mapController", mapController.InitHandler),
            (r'/view/dashboard/(.*)$',tornado.web.StaticFileHandler,{"path":"view/dashboard/"}),
            (r'/view/(.*)$',tornado.web.StaticFileHandler,{"path":"view"}),
            (r'/static/(.*)$',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}),
            (r'/(.*)$',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path"),"default_filename":"default.html"})
        ]
        super(Application,self).__init__(handlers,**config.settings )