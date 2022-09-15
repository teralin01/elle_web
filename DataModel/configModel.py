import json
from bson import json_util
from dataModel.mongoDBQuery import MongoDB

def SetViewerConfig(data):
    print(data)
    dbinstance = MongoDB("elle")
    dbinstance.upsert("config",{"Name":data["Name"]},{'$set':{"ROS2D":data["ROS2D"]}})
    return {"result":True}

def GetViewerConfig():
    dbinstance = MongoDB("elle")
    ret = dbinstance.get_data("config")
    
    print(ret)
    return json.loads(json_util.dumps(ret))

def DelViewerConfig(data):
    dbinstance = MongoDB("elle")
    ret = dbinstance.delete_data("config",data)    
