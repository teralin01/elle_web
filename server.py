import tornado.ioloop
import tornado.web
import tornado.httpserver
import debugpy
import config
from application import Application


if __name__ == "__main__":
     #debugpy.listen(5678)
     debugpy.listen(("0.0.0.0", 5678))
     
     #debugpy.breakpoint()
     app = Application()
     httpServer = tornado.httpserver.HTTPServer(app)
     httpServer.bind(config.options['port'])
     httpServer.start()

     tornado.ioloop.IOLoop.instance().start()
