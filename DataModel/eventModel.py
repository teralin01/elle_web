import json
import datetime
from dataModel.mongoDBQuery import MongoDB

MAXLOGSIZE = 5242880
MAXLOGCOUNT = 50000

def SaveBasicMissionLog(data):
    try:        
        dbinstance = MongoDB("elle")
        dbinstance.insert_data('missionLog',data)
        return {"result":True}    
    except:
        return {"result": False, "reason": "save db fail"}
    
    
def SaveMissionAct(data):
    try:
        dbinstance = MongoDB("elle")
        dbinstance.insert_data('missionAct',data)
        return {"result":True}
    except:
        return {"result": False, "reason": "save db fail"}    
    
def InitCollection():
    try:
        dbinstance = MongoDB("elle")
        dbinstance.create_log_collection('missionAct',MAXLOGSIZE,MAXLOGCOUNT)
        dbinstance.create_log_collection('missionLog',MAXLOGSIZE,MAXLOGCOUNT)
        return {"result":True}
    except:
        return {"result": False, "reason": "Create collection fail"}    
    
    