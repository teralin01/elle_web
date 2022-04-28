from optparse import TitledHelpFormatter
import tornado.web
from tornado.web import RequestHandler
import time
import json

class MainHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs ):
        self.set_header("Content-Type","text/html;charset=UTF-8")
        self.set_status(200,"OK")
        
        print ("Root request coming",time.time())
        self.write('Hello, world')
        self.finish()

class HomeHandler(tornado.web.RequestHandler):
    # def get_current_user(self):
    #     flag = self.get_argument("flag")
    #     return flag
    
    @tornado.web.authenticated
    def get(self, *args, **kwargs ):
        vars = {"Name":"Tera", "resource":10}
        waypoints = ([{"Name":"charging","location":1},{"Name":"april tag","location":3}])
        def mySum(n1,n2):
            return n1+n2
        self.render('home.html', vars = vars, waypoints = waypoints, mySum = mySum )
        self.finish()
        

class TokenHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs ):
        print ("Token request coming",time.time())
        token = {"time":time.time()}
        self.write(token)        
        
class HeaderHandler(RequestHandler):
    def set_default_header(self):  # Step 1 function call
        self.set_header("Content-Type","text/html;charset=UTF-8")
        self.set_status(200,"OK")
        
    def initialize(self): # Step 2 function call
        pass
    def prepare(self): # Step 3 function call
        pass
    
    def write_error(self,status_code, **kwargs): ## error function call after send_error()
        self.write("Internal error")
    
    def on_finish(self): # last function call, no matter success or fail
        #write internal log
        #release resource
        pass
    
    def get(self,*args,**kwargs):
        pass

class URLPathHandler(RequestHandler):
    def get(self,h1,h2,*args,**kwargs):
        self.write(h1+"--"+h2+" --")
        
class GetReqHandler(RequestHandler):
    def get(self,*args,**kwargs):
        flag = self.get_query_argument("Flag",default="None", strip=True)   
        print ("Home request coming",time.time(),"   ",flag)
        self.write("Query string: "+flag)

class PostReqHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.render('postDemo.html')
    def post(self,*args,**kwargs):        
        name = self.get_body_argument("name")
        self.write("Post name"+ name)        
        self.finish()
        
class ReqHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.render('postDemo.html')
    def post(self,*args,**kwargs):        
        name = self.get_argument("name")   # retrieve param from both Get & Post request
        self.write("Post name"+ name)                
    
class DataBaseHandler(RequestHandler):
    def get(self,*args,**kwargs):
        pass
    
class setCookieHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.set_cookie("Elle","beta")
        #self.set_secure_cookie("SecureElle","sCookie")
        self.write("ok")
        
class getCookieHandler(RequestHandler):
    def get(self,*args,**kwargs):
        cookie = self.get_cookie("Elle",default=None)            
        #cookie = self.secure_get_cookie("SecureElle")        
        print ("cookie: ",cookie)
        self.write("ok")

class ClearCookieHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.clear_cookie()
        self.write("ok")        
        
class LoginHandler(RequestHandler):
    def get(self,*args,**kwargs):
        next = self.get_argument("next","/")
        url = 'login?next='+next
        self.render("login.html", url = url)
    def post(self,*args,**kwargs):
        account = self.get_argument("username")
        pwd = self.get_argument("password")        
        if account == "admin" and pwd == "admin":
            next = self.get_argument("next","/")
            self.redirect(next+"?flag=logined")
        else:
            next = self.get_argument("next","/")
            self.redirect("/login?next="+next)

    
class DashboardHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.render('Dashboard.html')