# Required package
- Nginx
- tornado
- supervisor

# Install:
- apt-get install Nginx 
- pip install supervisor
- pip install tornado
- pip install psutil
- pip install gputil
- pip install websockets

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