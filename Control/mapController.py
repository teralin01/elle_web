import tornado.web
from tornado.web import RequestHandler
import time
import json

class InitHandler (RequestHandler):
    def get(self,*args,**kwargs):
        self.render('../view/dashboard/map.html')