from http import HTTPStatus   #Refer to https://docs.python.org/3/library/http.html
from datetime import datetime
import tornado.web
import tornado.ioloop
import logging

class TornadoBaseHandler(tornado.web.RequestHandler):
    def __init__(self,*args, **kwargs):
        super(TornadoBaseHandler,self).__init__(*args, **kwargs)
        self.set_default_headers()
        self._status_code = HTTPStatus.OK.value
        self.timeout_string = {"result":False}
        self.rest_timeout_period = 10
        self.cache_hit = False
        self.uri = self.request.path
        self.cache_rest_data = dict()

    def set_default_headers(self):
        if self.application.settings.get('debug'): # debug mode is True then support CORS
            self.set_dev_cors_headers()

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def set_dev_cors_headers(self):
        # For development only
        # Not safe for production
        origin = self.request.headers.get('Origin', '*') # use current requesting origin
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, x-requested-with, x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
        self.set_header('Access-Control-Expose-Headers', 'content-type, location, *, set-cookie')
        self.set_header('Access-Control-Request-Headers', '*')
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def rest_response(self,data):
        # Todo add log if necessary
        if self._status_code == HTTPStatus.OK.value:
            if data is not None and not self.cache_hit:
                self.cache_rest_data.update({self.uri:{'cacheData':data,'lastUpdateTime':datetime.now()}})
        try:
            self.write(data)
            self.finish()
        except Exception as exception:
            logging.info("REST Response Error %s",str(exception))
            
    #TODO Add default user authenication method