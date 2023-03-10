import config
from time import time 
from control.system.CacheData import cacheSubscribeData as cacheSub
from control.system.TornadoBaseHandler import TornadoBaseHandler
from control.system.logger import Logger
logging = Logger()
browser_clients = set()

class SSEHandler(TornadoBaseHandler):   
    def __init__(self, *args, **kwargs):
        super(TornadoBaseHandler,self).__init__(*args, **kwargs)
    
    def initialize(self):
        self._status_code = 200
        self._auto_finish = False
        self.dmission = {
            "op": "publish", "topic": "mission_control/states","backendMsg":"initMission",
            "isReset":False,
            "msg":{
            "stamp":{"sec":int(time()),"nanosec":0},
            "state":0,    
            "mission_state":0,   
            "actionPtr":-1,
            "action_state":-1,
            "missions":[]} }
        self.set_header('Content-Type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.set_header('Connection', 'keep-alive')

        if config.settings['debug'] == True:
            self.set_dev_cors_headers()
        
    def set_dev_cors_headers(self):
        origin = self.request.headers.get('Origin', '*') # use current requesting origin
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, x-requested-with, x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
        self.set_header('Access-Control-Expose-Headers', 'content-type, location, *, set-cookie')
        self.set_header('Access-Control-Request-Headers', '*')
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def on_finish(self):
        print("#### RESTful Client disconnected at " + str(time())+ " => "+ str(self)+ " " + self.request.path + " client count:"+ str(len(browser_clients)) )
        browser_clients.remove(self)
    
    async def get(self,*args):
        global browser_clients
        browser_clients.add(self)
        print("### RESTful Client connected at " + str(time()) + " => " + str(self) + " " + self.request.path + " client count:"+ str(len(browser_clients)))
        logging.debug("RESTful Client connected at" + str(time()) + " => " + str(self) + " " + self.request.path + " client count:"+ str(len(browser_clients)))
        
        #publish current mission to client
        subdata = cacheSub.get('mission_control/states')
        if subdata != None:
            if subdata['data'] != None:
                #TODO NO ETA in cache
                await self.constructSSE("message","0",subdata['data'] )
            else:
                await self.constructSSE("message","0",self.dmission )    
        else:
            await self.constructSSE("message","0",self.dmission )    
            
    async def constructSSE(res, event, id, data):
        try:
            if event != None:
                res.write('event: ' + event + '\n')
            if id != None:
                res.write('id: ' + id + '\n')
            
            res.write("data: " + str(data).replace("'", '"').replace('False','false').replace('True','true') + '\n\n')
            await res.flush()
        except Exception as err:
            if 'Stream is closed' in str(err.args) :
                browser_clients.remove(res)
                logging.debug("RESTful Client resource clear at" + str(time()) )
            else:
                print("SSE error"+ str(err.args))
                logging.debug(" SSE error:"+ str(err.args))
    
    async def eventUpdate(self,event,id,data):
        global browser_clients
        for client in browser_clients.copy():
            await self.constructSSE(client,'message',id,data)      
          
    def clientIsEmpty():
        if len(browser_clients) == 0:
            return True
        else:
            return False
          
    #TODO Deal with client disconnect issue. Can we aware a client have already connected before