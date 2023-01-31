
from control.EventController import SSEHandler as EventHandler
import config
import asyncio
import nest_asyncio

class MissionHandler:
    # Input: the ref of notify client
    def __init__(self):
        self.oldmission = None
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
        


    # Client come from REST request. 
    # issue: how to deal with mulitiple sender. 
    def CallbackMissionSender(mission):
        
        #callback and handle next task if exist
        pass


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
    
    def UpdateMissionStatus(self, mission):
        # TODO mission status parser , to aware the status change 

        # TODO Check previous and current mission is the same or not. If it is the same, the skip
        
        # self.CallbackMissionSender(mission)
        # self.EventLogger(mission)
        
        #Notify Browser client
        if not EventHandler.clientIsEmpty():
            pass
            try:
                nest_asyncio.apply()
                asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(EventHandler.eventUpdate(EventHandler,"mission",None,mission) ))
            except Exception as err:
                print(" Update status err: "+err)
                

