import tornado.web
from tornado.web import RequestHandler

class InitHandler (RequestHandler):
    def get(self,*args,**kwargs):
        self.render('../view/dashboard/mission.html')