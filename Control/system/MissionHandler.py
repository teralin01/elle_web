from apscheduler.schedulers.asyncio import AsyncIOScheduler
from control.EventController import SSEHandler as EventHandler
from control.system.CacheData import cacheSubscribeData as cacheSub
from datetime import datetime
from time import time 
import tornado.ioloop
import config
import asyncio
import math
import json

NOTIFY_CLIENT_DURATION = 15
AMR_SPEED = 0.2
WAIT_ETA = 60
DEFAULT_AMCL = {"position":{"x": 0, "y": 0, "z": 0}}

class MissionHandler:
    def __init__(self):     
        self.mission = {
            "op": "publish", "topic": "mission_control/states","backendMsg":"No cache found","msg":{
            "stamp":{"sec":int(time()),"nanosec":0},
            "state":0,    
            "missions":[]} }
        
        task = AsyncIOScheduler()
        task.add_job(self.ActiveSendETA, 'interval', seconds = 15)
        task.start()        

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
        print("@ prepare active Send")
        subdata = cacheSub.get('mission_control/states')
        if subdata != None:
            if subdata['data'] != None:
                self.mission = self.EstimateArrivalTimeCaculator(subdata['data'],False)
            else:
                self.mission = self.EstimateArrivalTimeCaculator(self.mission,False)
        else:
            self.mission = self.EstimateArrivalTimeCaculator(self.mission,False)        
        print(self.mission)
        await self.SendMissionToClient()
        
    def ParseMission(self, rawMission,AMCLPose):        
        cacheMission = cacheSub.get('mission_control/states')
        if cacheMission == None:  # mission not yet initialized
            return rawMission
        elif cacheMission['data'] == None:
            return rawMission

        missionList = rawMission
        Total_ETA = 0         
        curPose = AMCLPose['position']
        print(missionList['msg'])
        print(curPose)
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
                    if act['action_state'] <= 1:
                        time = round( math.sqrt(((curPose['x']-act['coordinate']['x'])**2)+((curPose['y']-act['coordinate']['y'])**2) ) * AMR_SPEED)
                        Total_ETA = Total_ETA + time
                        act['ActETA'] = time
                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else: 
                        act['ActETA'] = -1
                    curPose = act['coordinate']  # shift current position to new location
                if act['type'] == 5:
                    del act['coordinate']
                    del act['docking_info']
                    del act['pose_cmd']
                    del act['station']
                    
                    if act['action_state'] <= 1:
                        Total_ETA = Total_ETA + WAIT_ETA
                        act['ActETA'] = WAIT_ETA
                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else:    # ERROR or abort
                        act['ActETA'] = -1
            iterator['TotalETA'] = round(Total_ETA)       
        return missionList
        
    def EstimateArrivalTimeCaculator(self, mission, CallByEvent):
        AMCLPose = DEFAULT_AMCL
        AMCLPoseStr = cacheSub.get('amcl_pose')
        if AMCLPoseStr != None:
            if AMCLPoseStr["data"] != None:
                AMCLPoseData = json.loads( (AMCLPoseStr["data"]))
                AMCLPose = AMCLPoseData['msg']['pose']['pose']
        print(AMCLPose)        
        if CallByEvent:  
            return self.ParseMission(self,mission, AMCLPose)    
        else:  # call by periodic task, it use static object. No need "self" parameter
            return self.ParseMission(mission, AMCLPose)

    async def SendMissionToClient(self):
        print("@send")
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
        #TODO save this mission into log file 
        pass
    
    # advanced logger with roles
    def StatisticLogger():
        pass
    
    async def UpdateMissionStatus(self, mission):
        extMission = self.EstimateArrivalTimeCaculator(self, json.loads(mission), True)
        self.mission = extMission
        cacheSub.update({"mission_control/states":{"data":self.mission,"lastUpdateTime":datetime.now()}})
        await self.SendMissionToClient(self)
        # TODO mission status parser , to aware the status change 

        # TODO Check previous and current mission is the same or not. If it is the same, the skip
        
        # self.CallbackMissionSender(mission)
        # self.EventLogger(mission)
        



                

