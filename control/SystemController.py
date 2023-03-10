from control.system.TornadoExtension import BaseHandler
from control.system.RosMap import RosMap as ROSMAP

class RESTHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(BaseHandler,self).__init__(*args, **kwargs)
    
    def initialize(self):
        pass
    
    def prepare(self):
        self.URI = self.request.path
        
    def set_default_headers(self):
        if self.application.settings.get('debug'): # debug mode is True
            self.set_dev_cors_headers()

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
        
    def put(self,*args):
        self._status_code = 201
        if '/1.0/map/upload/layer/' in self.URI:
            if len(self.request.files) == 0:
                self.REST_response({"Result:":False,"Info":"N○ file with key \'file1\' inside html form"}) 
            ret = ROSMAP.UploadMapLayer(self.URI[len('/1.0/map/upload/layer/'):],self.request.files['file1'][0])
            print(ret)
            self.REST_response(ret)
        elif '/1.0/map/upload/maps/' in self.URI:
            if len(self.request.files) == 0:
                self.REST_response({"Result:":False,"Info":"Upload file fail. N○ file with key \'file1\' inside html form"})               
            ret = ROSMAP.UploadMapStatic(self.request.files['file1'][0])
            print(ret)
            self.REST_response(ret)
    def post(self,*args):
        self._status_code = 201
        if '/1.0/map/upload/layer/' in self.URI:
            if len(self.request.files) == 0:
                self.REST_response({"Result:":False,"Info":"N○ file with key \'file1\' inside html form"}) 
            ret = ROSMAP.UploadMapLayer(self.URI[len('/1.0/map/upload/layer/'):],self.request.files['file1'][0])
            print(ret)
            self.REST_response(ret)
        elif '/1.0/map/upload/maps/' in self.URI:
            if len(self.request.files) == 0:
                self.REST_response({"Result:":False,"Info":"Upload file fail. N○ file with key \'file1\' inside html form"})               
            ret = ROSMAP.UploadMapStatic(self.request.files['file1'][0])
            print(ret)
            self.REST_response(ret)                
    def REST_response(self,data):
        self.write(data)
        self.finish()           