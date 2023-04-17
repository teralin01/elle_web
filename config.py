import os
BASE_DIRS = os.path.dirname(__file__)

# http port
options = {
    "port":8080
}

settings = {
    "websocket_ping_interval": 20,
    "static_path": os.path.join(BASE_DIRS,"static"),
    "vue_path": os.path.join(BASE_DIRS,"vue"),
    "template_path":os.path.join(BASE_DIRS,"view"),
    "debug":True,
    "cookie_secret": "Elle_web_secret",
    "login_url":"/login",
    "rosbridgePort":"9090",
    "hostIP":"127.0.0.1",
    "rosbridgeMsgSize":"20000000",
    "web_version":"0.1.15",
    "amr_version":"1.0",    
    "db_admin_username":"admin",
    "db_admin_password":"axadmin",
    "mappath":"/maps/"
}