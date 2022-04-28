import imp
import tornado.web
import os
import config
from Control import index
from Control import statusController
from Control import mapController
from Control import missionController

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", index.MainHandler),
            (r"/", index.DashboardHandler),
            (r"/", index.DashboardHandler),
            (r"/", statusController.InitHandler),
            (r'/setCookie',index.setCookieHandler),
            (r'/getCookie',index.getCookieHandler),
            (r'/clearCookie',index.ClearCookieHandler),
            (r'/login',index.LoginHandler),
            (r"/parseURLPath/(\w*)/(\w*)", index.URLPathHandler),
            #redirect default static content to path /static 
            (r'/(.*)$',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static"),"default_filename":"index.html"})
        ]
        super(Application,self).__init__(handlers,**config.settings )