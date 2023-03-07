from control.EventController import SSEHandler as EventHandler
from control.system.CacheData import cacheSubscribeData as cacheSub
from control.system.CacheData import scheduler as TornadoScheduler
from control.system.CacheData import cacheMission as CacheMission
from dataModel import eventModel
from datetime import datetime
from time import time 
import config
import asyncio
import math
import json
import copy
import nest_asyncio
from control.system.logger import Logger
logging = Logger()

NOTIFY_CLIENT_DURATION = 15
AMR_SPEED = 0.2
WAIT_ETA = 0
DEFAULT_AMCL = {"position":{"x": 0, "y": 0, "z": 0}}
EVENT_TIMTOUT = 2
preMissionTimestampSec = 0 
preMissionTimestampNanoSec = 0 
DEFAULT_MISSION = {
            "op": "publish", "topic": "mission_control/states","backendMsg":"No cache found",
            "isReset":False,
            "msg":{
            "stamp":{"sec":int(time()),"nanosec":0},
            "state":0,    
            "mission_state":0,
            "actionPtr":-1,
            "action_state":-1,
            "missions":[]} }

ResendMission = None
SKIP_DEFAULT_MISSION = True

BEITOU_2F = True
Beitou_2F_Btn_State = {
"remote1":{"icon_can_trigger":True, "ETA":0},
"remote2":{"icon_can_trigger":True, "ETA":0},
"remote3":{"icon_can_trigger":True, "ETA":0},
"remote4":{"icon_can_trigger":True, "ETA":0},
"elle":{"icon_can_trigger":False,"ETA":0},
}

class MissionHandler:
    def __init__(self):     
        self.mission = DEFAULT_MISSION
        eventModel.InitCollection()
        TornadoScheduler.add_job(self.ActiveSendETA, 'interval', seconds = NOTIFY_CLIENT_DURATION)
        logging.debug("Start Mission ActiveSendETA")
        # logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
        TornadoScheduler.start()                

    def GetMission(self):
        if hasattr(self,'mission'):
            return self.mission
        else:
            return DEFAULT_MISSION

    def IsMissionDuplication(self,missiontag):
        targetMissionName = "remote"+str(missiontag)
        subdata = cacheSub.get('mission_control/states')
        if subdata != None and subdata['data'] != None:
            missionList = subdata['data']
        else:
            logging.debug("### mission is empty")
            return False # mission is empty
        
        for iterator in missionList['msg']['missions']: 
            if iterator['name'] == targetMissionName:                
                if "has_completed_wait_action" in iterator and iterator['has_completed_wait_action'] == 1 and targetMissionName == missionList['msg']['missions'][0]['name']:
                    logging.debug("## Skip Name: "+ iterator['name'] )
                    continue
                else:
                    logging.debug("## Duplicate: "+ iterator['name'] )
                    return True        
        
        return False
        
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
        missionList['msg']['actionPtr'] = -1
        missionList['msg']['action_state'] = -1       
        
        if SKIP_DEFAULT_MISSION:
            IsDefault = False

        if BEITOU_2F:
            missionList['msg']['mission_state_icon'] = copy.deepcopy(Beitou_2F_Btn_State)

        for iterator in missionList['msg']['missions']:
            if SKIP_DEFAULT_MISSION and iterator['name'] == 'default':
                IsDefault = True
                logging.debug("Default mission exist: ===>")
                logging.debug(iterator)
                break
            
            if BEITOU_2F:
                missionList['msg']['mission_state_icon'][iterator['name']]['icon_can_trigger'] = False
                
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
                        
                        if BEITOU_2F:
                            missionList['msg']['mission_state_icon'][iterator['name']]['ETA'] = Total_ETA
                            
                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else: # Abort
                        Total_ETA = Total_ETA + time
                        act['ActETA'] = Total_ETA 
                        missionList['msg']['mission_state'] = -1

                    if act['action_state'] == 1:
                        missionList['msg']['actionPtr'] = act['type']
                        missionList['msg']['action_state'] = 1                    
                    
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

                    if act['action_state'] == 0:
                        if BEITOU_2F:
                            pass
                                
                    if act['action_state'] == 1:
                        missionList['msg']['actionPtr'] = act['type']
                        missionList['msg']['action_state'] = 1   
                        
                        if BEITOU_2F:
                            missionList['msg']['mission_state_icon']['elle']['icon_can_trigger'] = True

                    #Check duplicate mission, if the wait action state becomes 2 more then one time, then enable
                    if act['action_state'] > 1:
                        iterator['has_completed_wait_action'] = 1  
                        
                        if BEITOU_2F:
                            missionList['msg']['mission_state_icon'][iterator['name']]['icon_can_trigger'] = True

                        
            iterator['Total_ETA'] = round(Total_ETA)
        print( "AMR pose"+ str(missionList['AMCLPose']) + " Total time: " +  str(Total_ETA))
       
        if SKIP_DEFAULT_MISSION and IsDefault:
            missionstr = DEFAULT_MISSION
            missionstr['isReset'] = True
            missionstr['backendMsg'] = "Default Mission exist, skip content"
            return missionstr

        return missionList
        
    def EstimateArrivalTimeCaculator(self, mission, CallByEvent):
        AMCLPose = DEFAULT_AMCL
        AMCLPoseStr = cacheSub.get('amcl_pose')
        if AMCLPoseStr != None:
            if AMCLPoseStr["data"] != None:
                AMCLPoseData = json.loads( (AMCLPoseStr["data"]))
                AMCLPose = AMCLPoseData['msg']['pose']['pose']

        try:
            if CallByEvent:  
                return self.ParseMission(self,mission, AMCLPose)    
            else:  # call by periodic task, it use static object. No need "self" parameter
                return self.ParseMission(mission, AMCLPose)
        except Exception as err:
            logging.DEBUG("Caculate ETA error "+ str(err))

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
    
    def ResendPreiousMissions():
        # ToDo 
        # Get previouse mission from cache
        
        # Publish mission 
        
        # Check mission update 
        
        # If disconnect is due to abort, the pending and wait for start
        # If diconnect is due to other rosbridge issue, the start mission directlly. 
        
        
        pass
    
    async def ResetMissionStatus():
        global ResendMission
        ResendMission = cacheSub.get('mission_control/states')
        logging.debug("Reset Cached mission to default")
        mission = DEFAULT_MISSION
        mission['reason']= "Reset mission due to Rosbridge connection reset"
        
        cacheSub.update({"mission_control/states":{"data":mission,"lastUpdateTime":datetime.now()}})
        logging.debug(MissionHandler.mission)
        
        MissionHandler.mission = DEFAULT_MISSION
        MissionHandler.mission['isReset'] = True
        await MissionHandler.SendMissionToClient(MissionHandler)
        
        
        MissionHandler.ResendPreiousMissions()
    
    async def UpdateMissionStatus():
        logging.debug("===> Start update mission")
        global CacheMission
        mission = CacheMission.get("mission")
        self = MissionHandler
        
        try:
            if cacheSub.get('mission_control/states')['data'] == None:
                cacheSub.update({"mission_control/states":{"data":json.loads(mission),"lastUpdateTime":datetime.now()}})
            extMission = self.EstimateArrivalTimeCaculator(self, json.loads(mission), True)
            print(extMission)
        except  Exception as err:
            print(" Parse Server Side Event err: "+ str(err))
        
        else:
            # Check previous and current mission is the same or not. If it is the same, then stop handle this update
            global preMissionTimestampSec
            global preMissionTimestampNanoSec
            if preMissionTimestampSec == extMission['msg']['stamp']['sec'] and preMissionTimestampNanoSec == extMission['msg']['stamp']['nanosec']:
                print("The timestamp is the same as previous one, skip update")
            else:            
                preMissionTimestampSec = extMission['msg']['stamp']['sec'] 
                preMissionTimestampNanoSec = extMission['msg']['stamp']['nanosec']
                extMission['isReset'] = False
                self.mission = extMission
                cacheSub.update({"mission_control/states":{"data":extMission,"lastUpdateTime":datetime.now()}})
                    
                await asyncio.wait_for(self.SendMissionToClient(self),EVENT_TIMTOUT)

                # self.CallbackMissionSender(mission)
                
                dbmission = copy.deepcopy(extMission)
                dbmission['msg']['timstamp'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                self.EventLogger(dbmission['msg'])
        



                

