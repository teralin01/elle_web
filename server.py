import tornado.ioloop
import tornado.web
import tornado.httpserver
import debugpy
import config
from application import Application


if __name__ == "__main__":
     if config.settings['debug'] is True:
          debugpy.listen(("0.0.0.0", 5678))
          debugpy.breakpoint()
     app = Application()
     app.listen(config.options['port'])
     
     tornado.ioloop.IOLoop.instance().start()
