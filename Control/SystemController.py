import tornado.web
import tornado.ioloop

from control.system.RosMap import RosMap as ROSMAP

class RESTHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass
    
    def prepare(self):
        self.URI = self.request.path
        
    def put(self,*args):
        self._status_code = 201
        if '/1.0/map/upload/layer/' in self.URI:
            if len(self.request.files) == 0:
                self.REST_response({"Result:":False,"Info":"N○ file with key \'file1\' inside html form"}) 
            ret = ROSMAP.UploadMapLayer(self.URI[len('/1.0/map/upload/layer/'):],self.request.files['file1'][0])
            print(ret)
            self.REST_response(ret)
        elif '/1.0/map/upload/static/' in self.URI:
            if len(self.request.files) == 0:
                self.REST_response({"Result:":False,"Info":"Upload file fail. N○ file with key \'file1\' inside html form"})               
            ret = ROSMAP.UploadMapStatic(self.request.files['file1'][0])
            print(ret)
            self.REST_response(ret)
        
    def REST_response(self,data):
        self.write(data)
        self.finish()           