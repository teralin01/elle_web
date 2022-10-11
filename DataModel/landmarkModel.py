import json
from bson import json_util
from dataModel.mongoDBQuery import MongoDB

def SetPoints(data):
    dbinstance = MongoDB("elle")
    if "oldName" in data: 
        itemID = dbinstance.get_single_data("landmarks",{"Name":data["oldName"]})
        ret = dbinstance.update_one("landmarks",{ "_id": itemID["_id"]} ,{'$set':{"Name":data["Name"],"X":data["X"],"Y":data["Y"],"Theta":data["Theta"],"Tag":data['Tag']}})        
    else:
        itemID = dbinstance.get_single_data("landmarks",{"Name":data["Name"]})
        ret = dbinstance.update_one("landmarks",{"_id": itemID["_id"]} ,{'$set':{"Name":data["Name"],"X":data["X"],"Y":data["Y"],"Theta":data["Theta"],"Tag":data['Tag']}})        
    
    if ret.modified_count > 0 :
        response = True
    else: 
        response = False
    return {"result":response}

def UpsertPoints(data):
    dbinstance = MongoDB("elle")
    dbinstance.upsert("landmarks",{"Name":data["Name"]},{'$set':{"X":data["X"],"Y":data["Y"],"Theta":data["Theta"],"Tag":data['Tag']}})
    return {"result":True}

def GetPoints():
    dbinstance = MongoDB("elle")
    ret = dbinstance.get_data("landmarks")
    return json.loads(json_util.dumps(ret))

def InsertPoint(data):
    dbinstance = MongoDB("elle")
    # todo check the existence of data, landmark name should be unique 
    #itemID = dbinstance.get_single_data("landmarks",{"Name":data["Name"]})
    
    ret = dbinstance.insert_data("landmarks",data)
    objID = json.loads(json_util.dumps(ret.inserted_id))
    return {"result":ret.acknowledged,"id":objID["$oid"]}
    
def DelWaypoints(data):
    dbinstance = MongoDB("elle")
    ret = dbinstance.delete_data("landmarks",{"Name":data["Name"]})    
    return {"result":ret.acknowledged}
