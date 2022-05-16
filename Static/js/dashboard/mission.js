function MissionStatus(){
    console.log("init mission");
    var missionStatus = new window.ROSLIB.Topic({
        ros : ros,
        name : '/mission_control/state',
        messageType : 'elle_interfaces/msg/MissionControlState'
      }); 
      var request = new ROSLIB.ServiceRequest({
      });
      missionStatus.subscribe((message)=> {
        console.log(message)
        var state = "STOPPING";
        if (JSON.stringify(message.executor_state) == 1)  
            state = "RUNNING"
        document.getElementById("missionState").innerHTML =  "Mission state: "+state;
        //document.getElementById("missionList").innerHTML =  "Mission List"+JSON.stringify(message.mission_state);
      });
  }
  MissionStatus();  