import math
import json
import copy
import logging
from time import time
from datetime import datetime
import asyncio
import nest_asyncio
from control.system.cache_data import cache_subscribe_data as cacheSub
from control.system.cache_data import scheduler as TornadoScheduler
from control.system.cache_data import cacheMission as CacheMission
from control.controller_event import SSEHandler as EventHandler
from datamodel import event_model

NOTIFY_CLIENT_DURATION = 15
AMR_SPEED = 0.2
WAIT_ETA = 0
DEFAULT_AMCL = {"position":{"x": 0, "y": 0, "z": 0}}
EVENT_TIMTOUT = 2
DEFAULT_MISSSION_TIMESTAMP_SECOND = 0
DEFAULT_MISSION_TIMESTAMP_NANOSECONE = 0
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

RESEND_MISSION = None
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
        event_model.init_collection()
        TornadoScheduler.add_job(self.active_send_eta, 'interval', seconds = NOTIFY_CLIENT_DURATION)
        logging.debug("Start Mission ActiveSendETA")
        TornadoScheduler.start()

    def get_mission(self):
        if hasattr(self,'mission'):
            return self.mission
        else:
            return DEFAULT_MISSION

    def is_mission_duplication(self,missiontag):
        target_mission_name = "remote"+str(missiontag)
        subdata = cacheSub.get('mission_control/states')
        if subdata is not None and subdata['data'] is not None:
            mission_list = subdata['data']
        else:
            logging.debug("### mission is empty")
            return False # mission is empty

        for iterator in mission_list['msg']['missions']:
            if iterator['name'] == str(target_mission_name):
                if "has_completed_wait_action" in iterator and iterator['has_completed_wait_action'] == 1 and target_mission_name == mission_list['msg']['missions'][0]['name']:
                    logging.debug("## Skip Name: %s", iterator['name'] )
                    continue
                else:
                    logging.debug("## Duplicate: %s", iterator['name'] )
                    return True

        return False

    def set_mission(self):
        # publish mission
        # receive mission update
        # start mission
        # receive mission update
        # callback to mission assigner


        # add req into await queue

        # if timeout, callback and handle next task if exist
        pass

    async def active_send_eta(self):
        subscribe_data = cacheSub.get('mission_control/states')
        new_mission = self.mission
        if subscribe_data is not None:
            if subscribe_data['data'] is not None:
                new_mission = self.estimate_arrival_time_caculator(subscribe_data['data'],False)
            else:
                new_mission = self.estimate_arrival_time_caculator(self.mission,False)
        else:
            new_mission = self.estimate_arrival_time_caculator(self.mission,False)

        new_mission['msg']['stamp']['sec'] = int(time())
        self.mission = new_mission
        nest_asyncio.apply()
        await asyncio.wait_for(self.SendMissionToClient(),EVENT_TIMTOUT)

    def parse_mission(self, raw_mission, amcl_pose):
        subscribe_data = cacheSub.get('mission_control/states')
        raw_mission['msg']['mission_state'] = 0 #Init mision_state
        if subscribe_data is None:
            return raw_mission
        elif subscribe_data['data'] is None:
            return raw_mission

        mission_list = raw_mission
        total_eta = 0
        current_position = amcl_pose['position']
        mission_list['AMCLPose'] = { 'x': round(amcl_pose['position']['x'],2),'y':round(amcl_pose['position']['y'],2),'z':round(amcl_pose['position']['z'],2)}
        mission_list['msg']['mission_state'] = mission_list['msg']['state']
        mission_list['msg']['actionPtr'] = -1
        mission_list['msg']['action_state'] = -1

        if SKIP_DEFAULT_MISSION:
            is_default = False

        if BEITOU_2F:
            mission_list['msg']['mission_state_icon'] = copy.deepcopy(Beitou_2F_Btn_State)

        for iterator in mission_list['msg']['missions']:
            if SKIP_DEFAULT_MISSION and iterator['name'] == 'default':
                is_default = True
                logging.debug("Default mission exist: ===>")
                logging.debug(iterator)
                break

            if BEITOU_2F:
                mission_list['msg']['mission_state_icon'][iterator['name']]['icon_can_trigger'] = False

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

                    caculated_time = round( math.sqrt(((current_position['x']-act['coordinate']['x'])**2)+((current_position['y']-act['coordinate']['y'])**2) ) / AMR_SPEED)

                    if act['action_state'] <= 1:
                        total_eta = total_eta + caculated_time
                        act['ActETA'] = total_eta
                        current_position = act['coordinate'] # shift current position to new location

                        if BEITOU_2F:
                            mission_list['msg']['mission_state_icon'][iterator['name']]['ETA'] = total_eta

                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else: # Abort
                        total_eta = total_eta + caculated_time
                        act['ActETA'] = total_eta
                        mission_list['msg']['mission_state'] = -1

                    if act['action_state'] == 1:
                        mission_list['msg']['actionPtr'] = act['type']
                        mission_list['msg']['action_state'] = 1

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
                        total_eta = total_eta + WAIT_ETA
                        act['ActETA'] = total_eta

                    elif act['action_state'] == 2:
                        act['ActETA'] = 0
                    else:    # ERROR or abort
                        total_eta = total_eta + WAIT_ETA
                        act['ActETA'] = total_eta
                        mission_list['msg']['mission_state'] = -1

                    if act['action_state'] == 0:
                        if BEITOU_2F:
                            pass

                    if act['action_state'] == 1:
                        mission_list['msg']['actionPtr'] = act['type']
                        mission_list['msg']['action_state'] = 1

                        if BEITOU_2F:
                            mission_list['msg']['mission_state_icon']['elle']['icon_can_trigger'] = True

                    #Check duplicate mission, if the wait action state becomes 2 more then one time, then enable
                    if act['action_state'] > 1:
                        iterator['has_completed_wait_action'] = 1

                        if BEITOU_2F:
                            mission_list['msg']['mission_state_icon'][iterator['name']]['icon_can_trigger'] = True


            iterator['Total_ETA'] = round(total_eta)
        logging.debug( "AMR pose"+ str(mission_list['AMCLPose']) + " Total time: " +  str(total_eta))

        if SKIP_DEFAULT_MISSION and is_default:
            missionstr = DEFAULT_MISSION
            missionstr['isReset'] = True
            missionstr['backendMsg'] = "Default Mission exist, skip content"
            return missionstr

        return mission_list

    def estimate_arrival_time_caculator(self, mission, call_by_event):
        amcl_pose = DEFAULT_AMCL
        amcl_pose_string = cacheSub.get('amcl_pose')
        if amcl_pose_string is not None:
            if amcl_pose_string["data"] is not None:
                amcl_pose_data = json.loads( (amcl_pose_string["data"]))
                amcl_pose = amcl_pose_data['msg']['pose']['pose']

        try:
            if call_by_event:
                return self.parse_mission(self,mission, amcl_pose)
            else:  # call by periodic task, it use static object. No need "self" parameter
                return self.parse_mission(mission, amcl_pose)
        except Exception as err:
            logging.error("Caculate ETA error %s", str(err))

    async def SendMissionToClient(self):
        #Notify Browser client
        if not EventHandler.client_is_empty(self):
            try:
                await EventHandler.eventUpdate(EventHandler,None,self.mission)
            except Exception as err:
                logging.error(" Update status err: %s", str(err))

    # Client come from REST request.
    # issue: how to deal with mulitiple sender.
    def callback_mission_sender(self):

        #callback and handle next task if exist
        pass


    # A general interface to ave event to database
    def basic_logger(self):
        pass

    # First level logger
    def event_logger(self, mission):
        ret = event_model.save_basic_mission_log(mission)
        if not ret:
            logging.debug("## save db fail")

    # advanced logger with roles
    def statistic_logger(self):
        pass

    def resend_preious_missions(self):
        # ToDo
        # Get previouse mission from cache

        # Publish mission

        # Check mission update
        # If disconnect is due to abort, the pending and wait for start
        # If diconnect is due to other rosbridge issue, the start mission directlly. 


        pass

    async def reset_mission_status(self):
        global RESEND_MISSION
        RESEND_MISSION = cacheSub.get('mission_control/states')
        logging.debug("Reset Cached mission to default")
        mission = DEFAULT_MISSION
        mission['reason']= "Reset mission due to Rosbridge connection reset"

        cacheSub.update({"mission_control/states":{"data":mission,"lastUpdateTime":datetime.now()}})
        logging.debug(self.mission)

        self.mission = DEFAULT_MISSION
        MissionHandler.mission['isReset'] = True
        await self.SendMissionToClient()

        self.resend_preious_missions()

    async def update_mission_status():
        logging.debug("===> Start update mission")
        global CacheMission
        mission = CacheMission.get("mission")
        self = MissionHandler

        try:
            if cacheSub.get('mission_control/states')['data'] is None:
                cacheSub.update({"mission_control/states":{"data":json.loads(mission),"lastUpdateTime":datetime.now()}})
            extMission = self.estimate_arrival_time_caculator(self, json.loads(mission), True)
            logging.debug(extMission)
        except  Exception as err:
            logging.debug(" Parse Server Side Event err: %s", str(err))

        else:
            # Check previous and current mission is the same or not. If it is the same, then stop handle this update
            global DEFAULT_MISSSION_TIMESTAMP_SECOND
            global DEFAULT_MISSION_TIMESTAMP_NANOSECONE
            if DEFAULT_MISSSION_TIMESTAMP_SECOND == extMission['msg']['stamp']['sec'] and DEFAULT_MISSION_TIMESTAMP_NANOSECONE == extMission['msg']['stamp']['nanosec']:
                logging.debug("The timestamp is the same as previous one, skip update")
            else:
                DEFAULT_MISSSION_TIMESTAMP_SECOND = extMission['msg']['stamp']['sec']
                DEFAULT_MISSION_TIMESTAMP_NANOSECONE = extMission['msg']['stamp']['nanosec']
                extMission['isReset'] = False
                self.mission = extMission
                cacheSub.update({"mission_control/states":{"data":extMission,"lastUpdateTime":datetime.now()}})

                await asyncio.wait_for(self.SendMissionToClient(self),EVENT_TIMTOUT)

                # self.CallbackMissionSender(mission)

                dbmission = copy.deepcopy(extMission)
                dbmission['msg']['timstamp'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                self.event_logger(self,dbmission['msg'])
