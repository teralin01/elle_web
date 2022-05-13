import tornado.web
from tornado.web import RequestHandler
import time
import json
import psutil


class HWInfoHandler (RequestHandler):
    def get(self,*args,**kwargs):
        memStatus =  psutil.virtual_memory() 
        cpuStatus = psutil.cpu_times()
        cpuPersent = psutil.cpu_percent()
        # [scputimes(user=11684.17, nice=57.93, system=148683.01, idle=2168982.08, iowait=260833.18, irq=7882.35, softirq=0.0, steal=3697.3, guest=0.0, guest_nice=0.0)]
        Info = { "memTotal":memStatus.total,"memUsed":memStatus.used,"CPU":cpuStatus,"CPU_Persent":cpuPersent }
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write( json.dumps(Info))

class InitHandler (RequestHandler):
    def get(self,*args,**kwargs):
        self.render('../view/dashboard/status.html')
        