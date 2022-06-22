

function init(){
    // RWD setting for map. the scale parameters need to adjust in the future. 
    var width = 1024;
    var height = 768;
    if ( windowWidth >= 1024){ // normal PC
      width = windowWidth *0.85;
      height = windowWidth * 0.33;
    }
    else if ( windowWidth > 768){
      width = windowWidth * 0.85;
      height = windowWidth * 0.33;
    }
    else if ( windowWidth <= 768){  // Mobile device 
      width = windowWidth *0.85;
      height = windowWidth * 0.33;
    }

    window.viewer = new window.ROS2D.Viewer({
        divID : 'mapdisplay',
        width : width,
        height : height,
        background: '#c2dfc2'
    });      
    
    var gridClient = new window.ROS2D.OccupancyGridClient({
        ros : ros,
        rootObject : viewer.scene,
        topic: '/map',
        topic: '/global_costmap/costmap',
        continuous : true,
    });

    gridClient.on('change', function(){
      if (! zoomStatus){
        viewer.scaleToDimensions(gridClient.currentGrid.width, gridClient.currentGrid.height);
        viewer.shift(gridClient.currentGrid.pose.position.x, gridClient.currentGrid.pose.position.y);
      }
    });

    // append grid
    var grid3 = new window.ROS2D.Grid({
        size : 50,
        cellSize :1,
        lineWidth : 0.01
    });
    viewer.scene.addChild(grid3);

    //  put car icon
    var navigationImage = new window.ROS2D.NavigationImage({ 
        image : '/static/image/ELLE.png',
        stage: viewer.scene,
        size: 1,
        //pulse: true
    });
    viewer.scene.addChild(navigationImage);
    // Get initial car position from ROS topic /initialpose
    var initialposeSubscriber = new window.ROSLIB.Topic({
        ros:ros,
        name: "initialpose",
        messageType: "geometry_msgs/msg/PoseWithCovarianceStamped"
    });
    initialposeSubscriber.subscribe((message) => {  
      // update initial icon location
      navigationImage.x = message.pose.pose.position.x;
      navigationImage.y = - message.pose.pose.position.y;
      console.log("Navigation pose: "+navigationImage.x+" "+navigationImage.y);
      // rotation icon
      navigationImage.rotation = new THREE.Euler().setFromQuaternion(new THREE.Quaternion(
          message.pose.pose.orientation.x,
          message.pose.pose.orientation.y,
          message.pose.pose.orientation.z,
          message.pose.pose.orientation.w
          )).z * -180 / 3.14159 ;
  });

    // update car location while odem moving 
    var poseSubscriber = new window.ROSLIB.Topic({
        ros:ros,
        name: "amcl_pose",
        messageType: "geometry_msgs/msg/PoseWithCovarianceStamped"
    });
    poseSubscriber.subscribe((message) => {  
        // update icon location
        navigationImage.x = message.pose.pose.position.x;
        navigationImage.y = - message.pose.pose.position.y;
        
        // rotation icon
        navigationImage.rotation = new THREE.Euler().setFromQuaternion(new THREE.Quaternion(
            message.pose.pose.orientation.x,
            message.pose.pose.orientation.y,
            message.pose.pose.orientation.z,
            message.pose.pose.orientation.w
            )).z * -180 / 3.14159 ;
    });

    // Show history path
    /*
      var traceShape = new window.ROS2D.TraceShape({
           strokeSize : 3,
           strokeColor : '#c2dfc2'
      });
        
      var listenerforPath = new ROSLIB.Topic ({
           ros : this.ros,
           name : '/global_plan',
           messageType : 'nav_msgs/Path'
       });

      viewer.scene.addChild(traceShape);
      listenerforPath.subscribe((message)=> {
           console.log(message)
           traceShape.addPose(message);
      });
    */

    // update global path
/*    var pathShapeGlobal = new window.ROS2D.PathShape({
      strokeSize : 5,
      strokeColor:'#0085FC'
      });
    
    var listenerforPathGlobal = new window.ROSLIB.Topic ({
      ros : this.ros,
      name : '/plan',
      messageType : 'nav_msgs/Path'
      });
    
    viewer.scene.addChild(pathShapeGlobal);
   
    var pathUpdateTime = Date.now();
    listenerforPathGlobal.subscribe((message)=> {
      
      currentTime = Date.now();
      if ( currentTime > pathUpdateTime + 2000 )
      {
        //console.log(message);
        pathShapeGlobal.setPath(message);
        pathUpdateTime = currentTime;
      }
    });
  */  
    // update local path
/*    var pathShapeLocal = new window.ROS2D.PathShape({
      strokeSize : 5,
      strokeColor: '#4CAF50'
      });
    
    var listenerforPathLocal = new window.ROSLIB.Topic ({
      ros : this.ros,
      name : '/local_plan',
      messageType : 'nav_msgs/Path'
      });
    
    viewer.scene.addChild(pathShapeLocal);
    
    listenerforPathLocal.subscribe((message)=> {
      //console.log(message)
      pathShapeLocal.setPath(message);
    });
  */  

   // update lidar info
    
  /*var pointCloud = new window.PointCloud2D({
    rootObject : viewer.scene,
    viewer : viewer,
    size : 0.5
  });*/

  /*
  var lidar  = new window.ROSLIB.Topic ({
    ros : this.ros,
    name : '/scan',
    messageType : 'sensor_msgs/LaserScan'
    });

  //pointCloud.visible({ enable: true });
  //viewer.scene.addChild(pathShapeGlobal);
  var lidarUpdateTime = Date.now();
  lidar.subscribe(function(message) {
    if (message !== 'undefined'){ 
      currentTime = Date.now();
        if ( currentTime > lidarUpdateTime + 10000 )
        {
          console.log(message);
          lidarUpdateTime = currentTime;
        }
        //pointCloud.update({ scan: message, interval: 10 });
      }
  });
  */
  


    // init zoom view
    window.zoomView = new ROS2D.ZoomView({
        rootObject : viewer.scene,
        minScale : 0.1
    });

    // init pan view
    window.panView = new ROS2D.PanView({
        rootObject : viewer.scene
    });

    window.triggerPan = function(options) {
        var viewer = window.viewer;
        var panView = window.panView;

        if(options.enable || false) {
        viewer.scene.addEventListener('stagemousedown', 
            this.panStartEventHandle = function(event) {
            if(event.nativeEvent.which === 1) 
            if (viewer.scene.mouseInBounds === true)
                panView.startPan(event.stageX, event.stageY);

            viewer.scene.addEventListener('stagemousemove', 
            this.panMoveEventHandle = function(event) {
            if(event.nativeEvent.which === 1) 
                if (viewer.scene.mouseInBounds === true) 
                panView.pan(event.stageX, event.stageY);
            });

            viewer.scene.addEventListener('stagemouseup', 
            this.panEndEventHandle = function(event) {
            if(event.nativeEvent.which === 1) 
                if (viewer.scene.mouseInBounds === true) {
                viewer.scene.removeEventListener(
                    'stagemousemove', this.panMoveEventHandle);
                viewer.scene.removeEventListener(
                    'stagemouseup', this.panEndEventHandle);
                }
            });

        });
        } else {
        viewer.scene.removeEventListener(
            'stagemousedown', this.panStartEventHandle);
        }
    };
}
   
function mapAdjust(){
console.log("Mouse enter div");
zoomStatus = true;
var viewer = window.viewer;

viewer.scene.addEventListener('wheel', 
this.zoomInEventHandle = function(event) {
    
    if (event.deltaY < 0){
    console.log("zoomin");
        zoomin();
    }
    else if (event.deltaY > 0)
    {
    console.log("zoomout");
        zoomout();
    }
});
}

function zoomin()
{
    zoomStatus = true;
    zoomView.startZoom(windowWidth/2, windowHeight/2);
    zoomView.zoom(1.5);
    
}

function zoomout()
{
    zoomStatus = true;
    zoomView.startZoom(windowWidth/2, windowHeight/2);
    zoomView.zoom(1/1.5);
    
}

function pan(btn)
{
    panOn = !panOn;
    if(panOn) {
    btn.style.backgroundColor = '#CCCC00';
    window.triggerPan({ enable: true });
    } else {
    btn.style.backgroundColor = '#DDDDDD';
    triggerPan({ enable: false });
    }
}

function touch(btn){

  viewer.scene.on("stagemousedown", function(evt) {
    //console.log("the canvas was clicked at "+evt.stageX+","+evt.stageY);
    //console.log("Scale X, Scale Y "+viewer.scene.scaleX+" "+viewer.scene.scaleY);
    //console.log("ROS zero X,Y "+viewer.scene.x+" "+viewer.scene.y); 
     
    var rosX = (evt.stageX - viewer.scene.x) / viewer.scene.scaleX;
    var rosY = (viewer.scene.y - evt.stageY) / viewer.scene.scaleY;
    console.log("ROS location (X,Y): ",rosX,rosY);
})

}
    
window.onload = function() {
    $.ajax({
        type: "get",
        //data: {start},
        url: "/control/statusController",
        success: function (result){
          $("#statusBlock").html(result);
        }
      });

      $.ajax({
        type: "get",
        //data: {start},
        url: "/control/missionController",
        success: function (result){
          $("#missionBlock").html(result);
        }
      });
  };

  document.addEventListener('DOMContentLoaded', function() {
    init();
  });
