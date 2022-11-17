# import pandas as pd

# class Store():
#     def __init__(self, columndata) -> None:
#         self.store = pd.DataFrame(columns = columndata)
        
#     def insert(self,data):
#         self.store = self.store.append(data,ignore_index=True)
        
#     def update(self,title,titleValue,col,value):
#         self.store.loc[self.store[title] == titleValue, col] = value
        
#     def getRow(self,title,key):
#         return self.store.loc[self.store[title].isin(key)]
    
#     def getField(self,title,key,col):
#         row = self.store.loc[self.store[title].isin(key)] 
#         return row[col].tolist()
    
#     def find(self,title,key):
#         return self.store[title].isin(key)
    
#     def deleteByIndex(self,indexArray):
#             self.store = self.store.drop(indexArray, axis=0)             

#     def delete(self,title,key):
#         condition = self.store[(self.store[title] == key)].index
#         #self.store = self.store.drop(condition,inplace = True)
#         self.store = self.store.drop(condition)
        
#     def print(self):
#         print(self.store)

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
        ret = False
        for key in self.ros_Sub_Commands:
            blist = self.ros_Sub_Commands[key]
            #if target in blist:
            #    blist.remove(target)            
            for key,value in enumerate(blist):
                item = list(value.keys())[0]
                if target == item:
                    blist.pop(key)
                    ret = True
                    break
        return ret
                
    def deleteOP(self,target):
        del self.ros_Sub_Commands[target]
                    
    def print(self):
        for key in self.ros_Sub_Commands:
            print(self.ros_Sub_Commands[key])    
