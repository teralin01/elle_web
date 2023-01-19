import tornado.web
import tornado.ioloop
import logging
import config
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
         
    async def get(self,*args):
        global browser_clients
        logging.debug("Client connected")
        browser_clients.add(self)
        await self.constructSSE("message","0",{ "general":"SSE Connected"} )
        #TODO if mission exist, publish mission to client

    async def constructSSE(res, event, id, data):
        logging.debug(data)
        try:
            if event != None:
                res.write('event: ' + event + '\n')
            if id != None:
                res.write('id: ' + id + '\n')

            res.write("data: " + str(data) + '\n\n')
            await res.flush()
        except Exception as err:
            logging.debug(" SSE error:"+err.args)
    
    async def eventUpdate(self,event,id,data):
        global browser_clients
        for client in browser_clients:
            await self.constructSSE(client,'message',id,{ event:data})      
          
    def clientIsEmpty():
        if len(browser_clients) == 0:
            return True
        else:
            return False
          
    #TODO Deal with client disconnect issue. Can we aware a client have already connected before