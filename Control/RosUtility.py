from types import coroutine
import pandas as pd
# from control.RosConn import ROSWebSocketConn

"""
Advertise example: 
    id: "advertise:/mission_control/mission:2"
    latch: false
    op: "advertise"
    queue_size: 100
    topic: "/mission_control/mission"
    type: "elle_interfaces/msg/MissionControlMission"

Publish example:
    id: "publish:/mission_control/mission:3"
    latch: false
    msg: {execution_mode: 1, start_from: 0,…}
    execution_mode: 1
    mission: [{type: 0, action_state: 1, coordinate: {x: 0.2, y: 2, z: 0.2}},…]
    0: {type: 0, action_state: 1, coordinate: {x: 0.2, y: 2, z: 0.2}}
    1: {type: 0, action_state: 1, coordinate: {x: 0.6, y: 4, z: 0.1}}
    start_from: 0
    op: "publish"
    topic: "/mission_control/mission"
"""

class RESTPublish():
    pass


"""
service request example: 
    id: "call_service:/mission_control/command:1"
    op: "call_service"
    service: "/mission_control/command"
    type: "elle_interfaces/srv/MissionControlCmd"

service response example
    service response
    id: "call_service:/mission_control/command:1"
    op: "service_response"
    result: true
    service: "/mission_control/command"
    values: {state: false}
    state: false
"""
class RESTServiceCall():    
    @classmethod
    def __init__(self) -> None:
        self.dicts = {}    

    @coroutine
    def addRosCmd(self,URI,restCB,type,service):
        print("RESTService call addRosCmd")
        #Generate unique ROS ID
        id = URI
        
        #Format ROS string
        serviceCall = {'id':id, 'op':"call_service",'type':type,'service':service}
        
        # self.addOne(id,restCB)
        global ROSWebSocketConn
        yield ROSWebSocketConn.write(serviceCall)
        return serviceCall
    
    #query callback deference by id
    def callback(self,data):
        print(data['service'] + " " + "id" + data['id'] + " result" + str(data['result']))
        
        cbList = self.getList(data['id'])
        for cb in cbList:
            cb.rosCallback(data) #REST write back
        
        # self.remove( data['id'] )

    def addOne(self,key,value):
        prev = self.dicts.get(key)
        if prev == None:
            self.dicts.update({key:{value}})
        else: 
            prev.add(value)
            self.dicts.update({key:prev})

    def removeKey(self,key):
        del self.dicts[key]

    def getList(self,key):
        values = self.dicts.get(key)
        if values == None:
            return None
        retList = []
        for item in values:
            retList.append( item)    
        return retList
    
    def removeDickItem(self,target):
        for key in self.dicts:
            list = self.dicts[key]
            if target in list:
                list.remove(target)
        return True

    def print(self):
        for key in self.dicts:
            print(self.dicts[key])


class Store():
    def __init__(self, columndata) -> None:
        self.store = pd.DataFrame(columns = columndata)
        
    def insert(self,data):
        self.store = self.store.append(data,ignore_index=True)
        
    def update(self,title,titleValue,col,value):
        self.store.loc[self.store[title] == titleValue, col] = value
        
    def getRow(self,title,key):
        return self.store.loc[self.store[title].isin(key)]
    
    def getField(self,title,key,col):
        row = self.store.loc[self.store[title].isin(key)] 
        return row[col].tolist()
    
    def find(self,title,key):
        return self.store[title].isin(key)
    
    def deleteByIndex(self,indexArray):
            self.store = self.store.drop(indexArray, axis=0)             

    def delete(self,title,key):
        condition = self.store[(self.store[title] == key)].index
        #self.store = self.store.drop(condition,inplace = True)
        self.store = self.store.drop(condition)
        
    def print(self):
        print(self.store)

# Example data
#  OP1:{browser A, browser B}
#  OP2:{browser A, browser B}
class ROSCommands():
    # add new item when new op come from browser
    @classmethod
    def __init__(self) -> None:
        self.ros_Commands = {}    

    def set(self,opID,browserClient):
        browserList = self.ros_Commands.get(opID)
        if browserList == None:
            self.ros_Commands.update({opID:{browserClient}})
        else: 
            browserList.add(browserClient)
            self.ros_Commands.update({opID:browserList})

    def remove(self,OPID):
        del self.ros_Commands[OPID]
    # get items when receive rosbridge response 
    def get(self,opID):
        browserList = self.ros_Commands.get(opID)
        if browserList == None:
            return None
        browsers = []
        for browser in browserList:
            browsers.append( browser)    
        return browsers
    
    # reomve item by browser client 
    def removeBrowser(self,target):
        for key in self.ros_Commands:
            blist = self.ros_Commands[key]
            if target in blist:
                blist.remove(target)
        return True

    def print(self):
        for key in self.ros_Commands:
            print(self.ros_Commands[key])
            
            
class SubscribeCommands():
    @classmethod
    def __init__(self) -> None:
        self.ros_Sub_Commands = {}    
        # ros_Sub_command structure:  OP1:{ [browser A:id1], [browser B:id2]}
    def set(self,opID,browserClient,id):
        browserList = self.ros_Sub_Commands.get(opID)
        if browserList == None:
            self.ros_Sub_Commands.update({opID:[ {browserClient:id} ] })
        else: 
            browserList.append( {browserClient:id})
            self.ros_Sub_Commands.update({opID:browserList})

    # get items when receive rosbridge response 
    def get(self,opID):
        browserList = self.ros_Sub_Commands.get(opID)
        if browserList == None:
            return None
        browsers = []
        for browser in browserList:
            browsers.append(browser)    
        return browsers

    def removeBrowser(self,target):
        for key in self.ros_Sub_Commands:
            blist = self.ros_Sub_Commands[key]
            if target in blist:
                blist.remove(target)            
        return True
                
    def deleteOP(self,target):
        del self.ros_Sub_Commands[target]
                    
    def print(self):
        for key in self.ros_Sub_Commands:
            print(self.ros_Sub_Commands[key])    
