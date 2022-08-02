import imp
import tornado.web
import os
import config
import datetime
from control import RESTController, mainController, wsController
from control import statusController
from control import mapController
from control import missionController
from control.RosUtility import Store


RESTUniqueCommands = Store(['requestURI','requestProtocol', 'executor','lastRequestTime'])
#RESTClientRequests = Store(['requestURI','id' ,'callback','parameter', 'issueTime'])


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
            (r"/1.0/missions",RESTController.rMissionHandler,dict(UniqueCommand=RESTUniqueCommands)),
            (r"/1.0/missions/(.*)",RESTController.rMissionHandler,dict(UniqueCommand=RESTUniqueCommands)),
            (r'/login',mainController.LoginHandler),
            (r'/logout',mainController.LogoutHandler),
            (r"/control/HardwareStatus", statusController.HWInfoHandler),
            (r"/control/missionController", missionController.InitHandler),
            (r"/control/mapController", mapController.InitHandler),
            (r'/view/dashboard/(.*)',tornado.web.StaticFileHandler,{"path":"view/dashboard/"}),
            (r'/view/(.*)',tornado.web.StaticFileHandler,{"path":"view"}),
            (r'/static/(.*)',tornado.web.StaticFileHandler,{"path":os.path.join(config.BASE_DIRS,"static_path")}), 
            (r'/(.*)', DefaultFileFallbackHandler, {'path': 'vue','default_filename': 'index.html'}),
        ]
        super(Application,self).__init__(handlers,**config.settings )
        
        print("Tornado Server start at " + str(datetime.datetime.now()))

     