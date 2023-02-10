import json
import datetime
from dataModel.mongoDBQuery import MongoDB

def SaveBasicMissionLog(data):
    try:        
        dbinstance = MongoDB("elle")
        dbinstance.insert_data('missionLog',{"data":data})
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