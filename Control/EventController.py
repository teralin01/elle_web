import tornado.web
import tornado.ioloop
import logging
import config
from control.system.CacheData import cacheSubscribeData as cacheSub
browser_clients = set()

class SSEHandler(tornado.web.RequestHandler):
    def initialize(self):
        self._status_code = 200
        self._auto_finish = False
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

    # TODO clear client if disconnected    
    def on_finish(self):
        browser_clients.remove(self)
         
    def get(self,*args):
        global browser_clients
        logging.debug("Client connected")
        browser_clients.add(self)
        # self.constructSSE("message","0",{ "general":"SSE Connected"} )
        
        subdata = cacheSub.get('/mission_control/states')
        if subdata != None:
            if subdata['data'] != None:
                self.constructSSE("message","0",{ "missions":subdata['data']} )
            else:
                self.constructSSE("message","0",{ "missions":[]} )    
            
        #TODO if mission exist, publish mission to client

    def constructSSE(res, event, id, data):
        logging.debug(data)
        try:
            if event != None:
                res.write('event: ' + event + '\n')
            if id != None:
                res.write('id: ' + id + '\n')

            res.write("data: " + str(data).replace("'", '"') + '\n\n')
            res.flush()
        except Exception as err:
            logging.debug(" SSE error:"+err.args)
    
    def eventUpdate(self,event,id,data):
        
        global browser_clients
        for client in browser_clients:
            self.constructSSE(client,'message',id,{ event:data})      
          
    def clientIsEmpty():
        if len(browser_clients) == 0:
            return True
        else:
            return False
          
    #TODO Deal with client disconnect issue. Can we aware a client have already connected before