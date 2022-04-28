import os
BASE_DIRS = os.path.dirname(__file__)

# http port
options = {
    "port":9002
}

settings = {
    "static_path": os.path.join(BASE_DIRS,"static"),
    "template_path":os.path.join(BASE_DIRS,"templates"),
    "debug":True,
    "cookie_secret":"ElleCookie",
    "login_url":"/login"
}