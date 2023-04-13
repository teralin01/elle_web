# Required package
- python 3.8
- Nginx
- tornado
- supervisor

# Install:
- sudo apt install python3.8
- pip3 install pip --upgrade
- pip3 install tornado==6.2
- pip3 install psutil==5.9.4
- pip3 install GPUtil==1.4.0
- pip3 install pymongo==4.3.3
- pip3 install roslibpy==1.4.2
- pip3 install jsonschema==4.17.3
- pip3 install debugpy==1.6.6
- pip3 install logger==1.4
- pip3 install asyncio==3.4.3
- pip3 install pynmcli==1.0.5
- pip3 install nest_asyncio==1.5.6
- pip3 install apscheduler==3.10.0
- pip3 install tornado-swagger==1.4.5
- pip3 install pyyaml==6.0

# How to run Elle web
## Config file path:
- review config from the path: "/document_path/config.py"
## Run Elle web command: 
- python3 /document_path/server.py

## Use supervisor to run tornado web server:
Config path
1. create new config file in path /etc/supervisor/config/tornado.conf.conf
1. add following settins (example config)

```shell
[group:tornadoes]
programs=tornado-9000
[program:tornado-9000]
command=python3 /home/tera/www/web/server.py
user=root
autorestart=true
redirect_stderr=true
stdout_logfile=/temp/supervisor.log
loglevel=info
```

### Start supervisor
- supervisorctl start all
### Stop supervisor
- supervisorctl stop all

### API document root path
http://Target_To_Elle_IP/api/doc