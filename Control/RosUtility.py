class ROSCommands():
    # add new item when new op come from browser
    @classmethod
    def __init__(self) -> None:
        self.ros_Commands = {}    

    def add(self,opID,browserClient):
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

    def add(self,opID,browserClient):
        browserList = self.ros_Sub_Commands.get(opID)
        if browserList == None:
            self.ros_Sub_Commands.update({opID:{browserClient}})
        else: 
            browserList.add(browserClient)
            self.ros_Sub_Commands.update({opID:browserList})

    # get items when receive rosbridge response 
    def get(self,opID):
        browserList = self.ros_Sub_Commands.get(opID)
        if browserList == None:
            return None
        browsers = []
        for browser in browserList:
            browsers.append( str( browser))    
        return browsers

    def removeBrowser(self,target):
        for key in self.ros_Sub_Commands:
            blist = self.ros_Sub_Commands[key]
            if target in blist:
                blist.remove(target)            
        return True
                
    def print(self):
        for key in self.ros_Sub_Commands:
            print(self.ros_Sub_Commands[key])    
