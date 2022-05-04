# Required package
- Nginx
- tornado
- supervisor

# Install:
- apt-get install Nginx
- pip install supervisor
- pip install tornado

# Config file:
- Root path/config.py
# Run : 
- python3 server.py
# Run supervisor:
Config path
- /etc/supervisor/supervisord.conf
Start
- supervisorctl start all
Stop
- supervisorctl stop all