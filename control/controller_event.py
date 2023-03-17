from time import time
import logging
import config
from control.system.cache_data import cache_subscribe_data as cache_subscription
from control.system.tornado_base_handler import TornadoBaseHandler
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

        if config.settings['debug'] is True:
            self.set_dev_cors_headers()

    def set_dev_cors_headers(self):
        origin = self.request.headers.get('Origin', '*') # use current requesting origin
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, \
            x-requested-with,x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
        self.set_header('Access-Control-Expose-Headers', 'content-type, location, *, set-cookie')
        self.set_header('Access-Control-Request-Headers', '*')
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def on_finish(self):
        browser_clients.remove(self)

    async def get(self,*args):
        global browser_clients
        browser_clients.add(self)
        logging.debug("RESTful Client connected => client count: %s", str(len(browser_clients)))

        #publish current mission to client
        subdata = cache_subscription.get('mission_control/states')
        if subdata is not None:
            if subdata['data'] is not None:
                #TODO NO ETA in cache
                await self.construct_server_side_event(self,"message","0",subdata['data'] )
            else:
                await self.construct_server_side_event(self,"message","0",self.dmission )
        else:
            await self.construct_server_side_event(self,"message","0",self.dmission )

    async def construct_server_side_event(self,res, event, identity, data):
        try:
            if event is not None:
                res.write('event: ' + event + '\n')
            if identity is not None:
                res.write('id: ' + identity + '\n')

            res.write("data: " + str(data).replace("'", '"').replace('False','false').\
                replace('True','true') + '\n\n')
            await res.flush()
        except Exception as err:
            if 'Stream is closed' in str(err.args) :
                browser_clients.remove(res)
                logging.error("RESTful Client resource clear")
            else:
                logging.error(" SSE error: %s", str(err.args))

    async def eventUpdate(self, identity, data):
        global browser_clients
        for client in browser_clients.copy():
            await self.construct_server_side_event(self,client,'message',identity,data)

    def client_is_empty(self):
        if len(browser_clients) == 0:
            return True
        else:
            return False

    #TODO Deal with client disconnect issue. Can we aware a client have already connected before