# Required package
- python 3.9
- Nginx
- tornado
- supervisor

# Install:
- sudo apt install python3.9
- pip3 install pip --upgrade
- pip3 install tornado
- pip3 install psutil
- pip3 install GPUtil
- pip3 install pymongo
- pip3 install pymysql
- pip3 install roslibpy
- pip3 install jsonschema
- pip3 install debugpy
- pip3 install logger
- pip3 install asyncio
- pip3 install config
- pip3 install pynmcli
- pip3 install nest_asyncio
- pip3 install apscheduler


# Required pip version
APScheduler==3.10.0
asyncio==3.4.3
attrs==22.2.0
autobahn==23.1.2
Automat==22.10.0
cffi==1.15.1
config==0.5.1
constantly==15.1.0
cryptography==39.0.1
debugpy==1.6.6
dnspython==2.3.0
GPUtil==1.4.0
hyperlink==21.0.0
idna==3.4
incremental==22.10.0
jsonschema==4.17.3
logger==1.4
nest-asyncio==1.5.6
psutil==5.9.4
pycparser==2.21
pymongo==4.3.3
pynmcli==1.0.5
pyrsistent==0.19.3
pytz==2022.7.1
pytz-deprecation-shim==0.1.0.post0
roslibpy==1.4.1
six==1.16.0
tornado==6.2
Twisted==22.10.0
txaio==23.1.1
typing_extensions==4.4.0
tzdata==2022.7
tzlocal==4.2
zope.interface==5.5.2



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
Stop
- supervisorctl stop all