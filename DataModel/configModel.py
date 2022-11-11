import json
from bson import json_util
from dataModel.mongoDBQuery import MongoDB

def SetUserConfig(data):
    print(data)
    dbinstance = MongoDB("elle")
    dbinstance.upsert("config",{"name":data["name"]},{'$set':{"data":data["data"]}})
    return {"result":True}

def GetViewerConfig():
    dbinstance = MongoDB("elle")
    ret = dbinstance.get_data("config")
    
    print(ret)
    return json.loads(json_util.dumps(ret))

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
def GetUserConfig(user):
    dbinstance = MongoDB("elle")
    result = json.loads( json_util.dumps(dbinstance.get_data("config")) )
    print(result)
    
    if user == None:
        return result
    else:
        for item in result:
            if item['name'] == user:
                return item
    
    return {}        


def DelUserConfig(data):
    dbinstance = MongoDB("elle")
    ret = dbinstance.delete_data("config",data)    
