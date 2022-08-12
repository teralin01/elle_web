import os
BASE_DIRS = os.path.dirname(__file__)

# http port
options = {
    "port":80
}

settings = {
    "static_path": os.path.join(BASE_DIRS,"static"),
    "vue_path": os.path.join(BASE_DIRS,"vue"),
    "template_path":os.path.join(BASE_DIRS,"view"),
    "debug":True,
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url":"/login",
    "rosbridgePort":"9090",
    "hostIP":""
}