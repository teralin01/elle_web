import json
from bson import json_util
from dataModel.mongoDBQuery import MongoDB

def SetUserConfig(data):
    try:
        print(data)
        dbinstance = MongoDB("elle")
        dbinstance.upsert("config",{"name":data["name"]},{'$set':{"data":data["data"]}})
        return {"result":True}
    except:
        return {"result": False, "reason": "query db fail"}

def GetViewerConfig():
    try:
        dbinstance = MongoDB("elle")
        ret = dbinstance.get_data("config")
        print(ret)
        if ret == None:
            return {"result": False, "reason": "no data found"}
        return json.loads(json_util.dumps(ret))
    except:
        return {"result": False, "reason": "query db fail"}
'''
Config example:
{"name":"admin","data":{
  "setting": {
     "initpose":{"display":true,"color":""},
     "goalpose":{"display":true,"color":""},
     "lidar":{"display":true,"color":""},
     "globalpath":{"display":true,"color":""},
     "localpath":{"display":true,"color":""},
     "joystick":{"display":false,"color":""}
   },
   "map":{
	  "mapratio":1.65,
      "layers":["map","speedlimit","keepout"]}   
   }
}
'''
    
    
def GetSingleUserConfig(user):
    try:
        dbinstance = MongoDB("elle")
        result = json.loads( json_util.dumps(dbinstance.get_single_data("config",{'name':user})) )
        print(result)
        if result == None:
            return {"result": False, "reason": "no data found"}
        elif user != None:
            return result

    except:
        return {"result": False, "reason": "query db fail"}

def DelUserConfig(data):
    try:
        dbinstance = MongoDB("elle")
        ret = dbinstance.delete_data("config",data)    
        return {"result": True}
    except:
        return {"result": False, "reason": "query db fail"}
