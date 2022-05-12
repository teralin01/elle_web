import tornado.web
from tornado.web import RequestHandler
from dataModel.AuthModel import AuthDB
import time
import json

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")     
        
# An example code to show the life time of http request in Tornado
class HeaderHandler(BaseHandler): 
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

# An example code to show http get/post in the same URL
class PostReqHandler(BaseHandler):
    def get(self,*args,**kwargs):
        self.render('postDemo.html')
    def post(self,*args,**kwargs):        
        name = self.get_body_argument("name")
        self.write("Post name"+ name)        
        self.finish()             
        
class LoginHandler(BaseHandler):
    def get(self,*args,**kwargs):
        status = self.get_argument("status","0")
        self.render("login.html",  status = status)
    def post(self,*args,**kwargs):
        account = self.get_argument("username")
        pwd = self.get_argument("password")        
        
        ret = AuthDB(account,pwd)
        if ret == 1:
            self.redirect("/login?status=1") 
        if ret == 2:
            self.redirect("/login?status=2") 
            
        self.set_secure_cookie("user", account)    
        self.redirect("/main")
            
        # default account  "admin" / "axadmin"
        #                  "user"  / "axuser"
        #                  "dev"   / "!elledev"
            

class LogoutHandler(BaseHandler):
    def get(self,*args,**kwargs):
        #TODO: clear server side resource
        self.clear_cookie("user")
        self.write("Logout success")
            
class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,*args,**kwargs):
        self.render('main.html')        