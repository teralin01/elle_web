from datamodel.mongoDB_query import MongoDB

MAXLOGSIZE = 5242880
MAXLOGCOUNT = 50000

def save_basic_mission_log(data):
    try: 
        dbinstance = MongoDB("elle")
        dbinstance.insert_data('missionLog',data)
        return {"result":True}
    except Exception as exception:
        return {"result": False, "reason": "save db fail","exception":str(exception)}

def save_mission_act(data):
    try:
        dbinstance = MongoDB("elle")
        dbinstance.insert_data('missionAct',data)
        return {"result":True}
    except Exception as exception:
        return {"result": False, "reason": "save db fail","exception":str(exception)}

def init_collection():
    try:
        dbinstance = MongoDB("elle")
        dbinstance.create_log_collection('missionAct',MAXLOGSIZE,MAXLOGCOUNT)
        dbinstance.create_log_collection('missionLog',MAXLOGSIZE,MAXLOGCOUNT)
        return {"result":True}
    except Exception as exception:
        return {"result": False, "reason": "Create collection fail","exception":str(exception)}
        
    
    