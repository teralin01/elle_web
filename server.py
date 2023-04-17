# import tornado.ioloop
import tornado.web
import tornado.httpserver
import asyncio
import debugpy
import config
from application import Application

async def main():
     if config.settings['debug'] is True:
          debugpy.listen(("0.0.0.0", 5678))
          debugpy.breakpoint()
     app = Application()
     app.listen(config.options['port'])
     await asyncio.Event().wait()
     # tornado.ioloop.IOLoop.instance().start()
     
if __name__ == "__main__":
     asyncio.run(main())

