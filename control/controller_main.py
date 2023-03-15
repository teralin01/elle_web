import tornado.web
from datamodel.auth_model import AuthDB
import time

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")     
          
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
            
        self.set_secure_cookie("user", account, expires=time.time()+86400) #cookie timeout after 1 day
        self.redirect("/index.html")
            
        # default account  "admin" / "axadmin"
        #                  "user"  / "axuser"
        #                  "dev"   / "!elledev"
            

class LogoutHandler(BaseHandler):
    def get(self,*args,**kwargs):
        #TODO: clear server side resource
        self.clear_cookie("user")
        self.write("Logout success")
      