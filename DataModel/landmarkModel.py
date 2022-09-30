import json
from bson import json_util
from dataModel.mongoDBQuery import MongoDB

def SetPoints(data):
    print(data)
    dbinstance = MongoDB("elle")
    dbinstance.upsert("waypoints",{"Name":data["Name"]},{'$set':data["Coordinate"]})
    return {"result":True}

def GetPoints():
    dbinstance = MongoDB("elle")
    ret = dbinstance.get_data("waypoints")
    
    print(ret)
    return json.loads(json_util.dumps(ret))

def DelWaypoints(data):
    dbinstance = MongoDB("elle")
    ret = dbinstance.delete_data("waypoints",{"Name":data["Name"]})    
