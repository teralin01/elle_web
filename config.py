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
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url":"/login"
}