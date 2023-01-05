import tornado.web
import tornado.ioloop
import logging
#import asyncio

browser_clients = set()

class SSEHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(SSEHandler, self).__init__(*args, **kwargs)
        self._status_code = 200
        self.set_header('Content-Type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.set_header('Connection', 'keep-alive')
        
    async def get(self,*args):
        global browser_clients
        logging.debug("Client connected")
        browser_clients.add(self)

    async def constructSSE(res, event, id, data):
        logging.debug(data)
        if event != None:
            res.write('event: ' + event + '\n')
        if id != None:
            res.write('id: ' + id + '\n')
        res.write("data: " + data + '\n\n')
        await res.flush()
    
    async def eventUpdate(self,event,id,data):
        global browser_clients
        for client in browser_clients:
          await self.constructSSE(client,event,id,data)      
          
    #TODO Deal with client disconnect issue. Can we aware a client have already connected before