import json
from dataModel.mongoDBQuery import MongoDB

def SaveBasicMissionLog(act,data):
    try:
        print("####  Save Log to database")
        print(data)
        dbinstance = MongoDB("elle")
        dbinstance.insert_data("missionLog",{"act":act,"data":data})
        return {"result":True}
    except:
        return {"result": False, "reason": "query db fail"}