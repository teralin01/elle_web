
from control import EventController as ClientPool
import config

class MissionHandler:
    # Input: the ref of notify client
    def __init__(self):
        pass
    
    def SetMission():
        # publish mission 
        # receive mission update
        # start mission 
        # receive mission update
        # callback to mission assigner 
        
        
        # add req into await queue
        
        # if timeout, callback and handle next task if exist
        pass
        
    def UpdateMissionStatus(self, mission):
        
        # TODO mission status parser , to aware the status change 
        
        
        
        
        self.CallbackMissionSender(mission)
        self.EventLogger(mission)
        self.NotifyMissionReader(mission)

    # Client come from REST request. 
    # issue: how to deal with mulitiple sender. 
    def CallbackMissionSender(mission):
        
        #callback and handle next task if exist
        pass


    # Client should register server side event for callback
    def NotifyMissionReader(self,missionArray):
        ClientPool.SSEHandler.eventUpdate("mission",None,missionArray)
    
    # A general interface to ave event to database
    def BasicLogger(mission):
        pass
    
    # First level logger
    def EventLogger(mission):
        #TODO save this mission into log file 
        pass
    
    # advanced logger with roles
    def StatisticLogger():
        pass
    

