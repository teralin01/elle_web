from control.EventController import SSEHandler as EventHandler
from control.system.CacheData import cacheSubscribeData as cacheSub
from control.system.CacheData import scheduler as TornadoScheduler
from dataModel import eventModel
from datetime import datetime
from time import time 
import config
import asyncio
import math
import json
import copy
import nest_asyncio
import logging

NOTIFY_CLIENT_DURATION = 15
AMR_SPEED = 0.2
WAIT_ETA = 0
DEFAULT_AMCL = {"position":{"x": 0, "y": 0, "z": 0}}
EVENT_TIMTOUT = 2
preMissionTimestampSec = 0 
preMissionTimestampNanoSec = 0 

class MissionHandler:
    def __init__(self):     

        self.mission = {
            "op": "publish", "topic": "mission_control/states","backendMsg":"No cache found","msg":{
            "stamp":{"sec":int(time()),"nanosec":0},
            "state":0,    
            "mission_state":0,    
            "missions":[]} }

        eventModel.InitCollection()
        TornadoScheduler.add_job(self.ActiveSendETA, 'interval', seconds = NOTIFY_CLIENT_DURATION)
        logging.debug("Start Mission ActiveSendETA")
        logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

        TornadoScheduler.start()                
        
        
        # task = AsyncIOScheduler()
        # task.add_job(self.ActiveSendETA, 'interval', seconds = NOTIFY_CLIENT_DURATION)
        # logging.debug("Start Mission ActiveSendETA")
        # task.start()        

    def SetMission():
        # publish mission 
        # receive mission update
        # start mission 
        # receive mission update
        # callback to mission assigner 
        
        
        # add req into await queue
        
        # if timeout, callback and handle next task if exist
        pass
            
    async def ActiveSendETA(self):
        subdata = cacheSub.get('mission_control/states')
        new_mission = self.mission
        if subdata != None:
            if subdata['data'] != None:
                new_mission = self.EstimateArrivalTimeCaculator(subdata['data'],False)
            else:
                new_mission = self.EstimateArrivalTimeCaculator(self.mission,False)
        else:
            new_mission = self.EstimateArrivalTimeCaculator(self.mission,False)        
        
        new_mission['msg']['stamp']['sec'] = int(time())
        self.mission = new_mission
        nest_asyncio.apply()
        await asyncio.wait_for(self.SendMissionToClient(),EVENT_TIMTOUT)
        
    def ParseMission(self, rawMission,AMCLPose):       
        subdata = cacheSub.get('mission_control/states')
        rawMission['msg']['mission_state'] = 0 #Init mision_state 
        if subdata == None:
            return rawMission
        elif subdata['data'] == None:
            return rawMission

        missionList = rawMission
        Total_ETA = 0         
        curPose = AMCLPose['position']        
        missionList['AMCLPose'] = { 'x': round(AMCLPose['position']['x'],2),'y':round(AMCLPose['position']['y'],2),'z':round(AMCLPose['position']['z'],2)}
        missionList['msg']['mission_state'] = missionList['msg']['state']        
        for iterator in missionList['msg']['missions']:
            for act in iterator['actions']:
                if act['type'] == 0:
                    act['coordinate']['x'] = round( act['coordinate']['x'],3)
                    act['coordinate']['y'] = round( act['coordinate']['y'],3)
                    act['coordinate']['z'] = round( act['coordinate']['z'],3)
                    if 'docking_info' in act:
                        del act['docking_info']
                    if 'pose_cmd' in act:    
                        del act['pose_cmd']
                    if 'station' in act:
                        del act['station']                   
                    
                    time = round( math.sqrt(((curPose['x']-act['coordinate']['x'])**2)+((curPose['y']-act['coordinate']['y'])**2) ) / AMR_SPEED)
                    if act['action_state'] <= 1:
                        Total_ETA = Total_ETA + time
                        act['ActETA'] = Total_ETA 
                        curPose = act['coordinate'] # shift current position to new location            
                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else: # Abort
                        Total_ETA = Total_ETA + time
                        act['ActETA'] = Total_ETA 
                        missionList['msg']['mission_state'] = -1

                if act['type'] == 5:
                    if 'coordinate' in act:
                        del act['coordinate']
                    if 'docking_info' in act:
                        del act['docking_info']
                    if 'pose_cmd' in act:
                        del act['pose_cmd']
                    if 'station' in act:
                        del act['station']

                    if act['action_state'] <= 1:
                        Total_ETA = Total_ETA + WAIT_ETA
                        act['ActETA'] = Total_ETA
                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else:    # ERROR or abort
                        Total_ETA = Total_ETA + WAIT_ETA
                        act['ActETA'] = Total_ETA
                        missionList['msg']['mission_state'] = -1  
            iterator['Total_ETA'] = round(Total_ETA)
        print( "AMR pose"+ str(missionList['AMCLPose']) + " Total time: " +  str(Total_ETA))
        return missionList
        
    def EstimateArrivalTimeCaculator(self, mission, CallByEvent):
        AMCLPose = DEFAULT_AMCL
        AMCLPoseStr = cacheSub.get('amcl_pose')
        if AMCLPoseStr != None:
            if AMCLPoseStr["data"] != None:
                AMCLPoseData = json.loads( (AMCLPoseStr["data"]))
                AMCLPose = AMCLPoseData['msg']['pose']['pose']

        if CallByEvent:  
            return self.ParseMission(self,mission, AMCLPose)    
        else:  # call by periodic task, it use static object. No need "self" parameter
            return self.ParseMission(mission, AMCLPose)

    async def SendMissionToClient(self):
        #Notify Browser client
        if not EventHandler.clientIsEmpty():
            try:
                await EventHandler.eventUpdate(EventHandler,"mission",None,self.mission)
            except Exception as err:
                print(" Update status err: "+ str(err))
                
                        
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
        ret = eventModel.SaveBasicMissionLog(mission)
        if not ret:
            print("## save db fail")
    
    # advanced logger with roles
    def StatisticLogger():
        pass
    
    async def UpdateMissionStatus(self, mission):
        try:
            if cacheSub.get('mission_control/states')['data'] == None:
                cacheSub.update({"mission_control/states":{"data":json.loads(mission),"lastUpdateTime":datetime.now()}})
            extMission = self.EstimateArrivalTimeCaculator(self, json.loads(mission), True)
            print(extMission)
        except  Exception as err:
            print(" Parse Server Side Event err: "+ str(err))
        # Check previous and current mission is the same or not. If it is the same, then stop handle this update

        else:
            # Check previous and current mission is the same or not. If it is the same, then stop handle this update
            global preMissionTimestampSec
            global preMissionTimestampNanoSec
            if preMissionTimestampSec == extMission['msg']['stamp']['sec'] and preMissionTimestampNanoSec == extMission['msg']['stamp']['nanosec']:
                print("The timestamp is the same as previous one, skip update")
            else:            
                preMissionTimestampSec = extMission['msg']['stamp']['sec'] 
                preMissionTimestampNanoSec = extMission['msg']['stamp']['nanosec']
            
                self.mission = extMission
                cacheSub.update({"mission_control/states":{"data":extMission,"lastUpdateTime":datetime.now()}})
                    
                await asyncio.wait_for(self.SendMissionToClient(self),EVENT_TIMTOUT)

                # self.CallbackMissionSender(mission)
                
                dbmission = copy.deepcopy(extMission)
                dbmission['msg']['timstamp'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                self.EventLogger(dbmission['msg'])
            



                

