import os
BASE_DIRS = os.path.dirname(__file__)

# http port
options = {
    "port":9000
}

settings = {
    "static_path": os.path.join(BASE_DIRS,"static"),
    "template_path":os.path.join(BASE_DIRS,"view"),
    "debug":True,
    "cookie_secret":"ElleCookie",
    "login_url":"/login"
}