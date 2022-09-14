import tornado.web
import json
from bson import json_util
from dataModel.mongoDBQuery import MongoDB

def SetWaypoints(data):
    print(data)
    dbinstance = MongoDB("elle")
    dbinstance.upsert("waypoints",{"Name":data["Name"]},{'$set':data["Coordinate"]})
    return {"result":True}

def GetWaypoints():
    dbinstance = MongoDB("elle")
    ret = dbinstance.get_data("waypoints")
    
    print(ret)
    return json.loads(json_util.dumps(ret))

def DelWaypoints(data):
    dbinstance = MongoDB("elle")
    ret = dbinstance.delete_data("waypoints",data)    

# def AuthDB(account, password):
#     dbinstance = MongoDB("elle")
#     query = {"username": account}

#     ret = dbinstance.get_single_data("account",query)
    
#     if(ret == None):
#         return 1  # user not found
#     if(ret.get('password') != password):
#         return 2  # password not match
#     return 0 #success