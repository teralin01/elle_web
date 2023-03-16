from control.system.tornado_base_handler import TornadoBaseHandler
from control.system.ros_map import RosMap as ROSMAP

class RESTHandler(TornadoBaseHandler):
    def __init__(self, *args, **kwargs):
        super(TornadoBaseHandler,self).__init__(*args, **kwargs)
    
    def initialize(self):
        pass
    
    def prepare(self):
        self.URI = self.request.path
        
    def put(self,*args):
        self._status_code = 201
        if '/1.0/map/upload/layer/' in self.URI:
            if len(self.request.files) == 0:
                self.rest_response({"Result:":False,"Info":"N○ file with key \'file1\' inside html form"}) 
            ret = ROSMAP.upload_map_layer(self.URI[len('/1.0/map/upload/layer/'):],self.request.files['file1'][0])
            print(ret)
            self.rest_response(ret)
        elif '/1.0/map/upload/maps/' in self.URI:
            if len(self.request.files) == 0:
                self.rest_response({"Result:":False,"Info":"Upload file fail. N○ file with key \'file1\' inside html form"})               
            ret = ROSMAP.upload_map_static(self.request.files['file1'][0])
            print(ret)
            self.rest_response(ret)
    def post(self,*args):
        self._status_code = 201
        if '/1.0/map/upload/layer/' in self.URI:
            if len(self.request.files) == 0:
                self.rest_response({"Result:":False,"Info":"N○ file with key \'file1\' inside html form"}) 
            ret = ROSMAP.upload_map_layer(self.URI[len('/1.0/map/upload/layer/'):],self.request.files['file1'][0])
            print(ret)
            self.rest_response(ret)
        elif '/1.0/map/upload/maps/' in self.URI:
            if len(self.request.files) == 0:
                self.rest_response({"Result:":False,"Info":"Upload file fail. N○ file with key \'file1\' inside html form"})               
            ret = ROSMAP.upload_map_static(self.request.files['file1'][0])
            print(ret)
            self.rest_response(ret)                
    def rest_response(self,data):
        self.write(data)
        self.finish()           