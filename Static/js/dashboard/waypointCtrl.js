var ros = new ROSLIB.Ros();
var ip = location.host.split(':')[0];
ros.connect("ws://"+ip+"/ws");

var width = 1178;
var height = 606;
var waypointArray = [];

var pickerLoc = {"x":2,"y":1}; // store location value from node-red or location picker 
var navigationImage = null; 
var ROSLoc = {'x':0,'y':0};
function init(){
const config = fetch("/1.0/config/viewer");
const waypoint = fetch("/1.0/maps/waypoints");
Promise.all([config, waypoint])
  .then(async([viewerConfig, waypointList]) => {
      const resolution = await viewerConfig.json();
      waypointArray = await waypointList.json();
      width = resolution[0].ROS2D.width;
      height = resolution[0].ROS2D.height;

      initDropdown();
      initROS2D(waypointArray);
  })
  .catch((err) => {
      console.error(err);
  });
}

function roundToTwo(num) {
    return +(Math.round(num + "e+2")  + "e-2");
}

function initROS2D(){
  window.viewer = new window.ROS2D.Viewer({
      divID : 'nav',
      width : width,
      height : height,
      background: '#c2dfc2'
    });      

    var gridClient = new window.ROS2D.OccupancyGridSrvClient({
      ros : ros,
      rootObject : viewer.scene,
      service: '/map_server/map',
    });      

    gridClient.on('change', function(){
      viewer.scaleToDimensions(gridClient.currentGrid.width, gridClient.currentGrid.height);
      viewer.shift(gridClient.currentGrid.pose.position.x, gridClient.currentGrid.pose.position.y);
    });

    // show grid
    var grid = new window.ROS2D.Grid({
      size : 50,
      cellSize :1,
      lineWidth : 0.01
    });
    viewer.scene.addChild(grid);
    curViewerSetting = {'scaleX': window.viewer.scene.scaleX,'scaleY':window.viewer.scene.scaleY,'x':window.viewer.scene.x,'y':window.viewer.scene.y }

    UpdateMapPoints();

    viewer.scene.on("stagemousedown", function (evt) {
        var rosX = roundToTwo(((evt.stageX - viewer.scene.x) / viewer.scene.scaleX));
        var rosY = - roundToTwo((viewer.scene.y - evt.stageY) / viewer.scene.scaleY);    
        
        pickerLoc = {"x":rosX,"y":rosY};
        document.getElementById("waypoints").value = "Picker";
        document.getElementById("waypoints").text = "*Customized Location";
        UpdateMapPoints();
    });
}

function initDropdown(){
  var select =   document.getElementById('waypoints');
  var option = document.createElement("option");
      option.value = "Picker" ;
      option.text = "*Customized Location" ;
      select.appendChild(option)

  waypointArray.forEach(element=>{
      var option = document.createElement("option");
      option.value = element['Name'] ;
      option.text = element['Name'] ;
      select.appendChild(option)
  })
}

function UpdateMapPoints(){
  //Get selected option
  var selected = document.getElementById("waypoints");
  var selectedValue = selected.value;
  console.log("selected value"+ selectedValue);
  if (selectedValue == "Picker"){      
    ROSLoc = pickerLoc;
    document.getElementById("coordinate").innerHtml = "X: " + pickerLoc['X'] + " Y:"+ pickerLoc['Y'] ;
  }
  else{
    waypointArray.forEach(element=>{
        if (element['Name'] == selectedValue){
            ROSLoc = {'x':element['X'],'y':element['Y']};
            document.getElementById("coordinate").innerHtml = "X: " + element['X'] + " Y:"+ element['Y'] ;
        }
    })
  }
  document.getElementById("coordinate").textContent  = "X: " + ROSLoc['x'] + " Y:"+ -ROSLoc['y'] ;

  //show slected option on map
      viewer.scene.removeChild(navigationImage);
      navigationImage = new window.ROS2D.NavigationImage({ 
        image : '/static/image/mapLocationFlag.png',
        stage: viewer.scene,
        size: 1,
        alpha:0.8,
        pulse: true
      });

      // Without setTimeout, the position of Navigation image will always being place at 0,0
      setTimeout(function () {
        viewer.scene.addChild(navigationImage);
        navigationImage.x = ROSLoc.x;
        navigationImage.y = ROSLoc.y;
    }, 10);
  
  //Optional: show rest options on map
}    

//////////////////////////////////////////////////////////////////////////////////////////////
// Show
// TODO: show all waypoints to map. => function UpdateMapPoints()
// TODO: hightlight current selected waypoints on map ( use pause )  => function UpdateMapPoints()

// Dynamic change 
// TODO: Add a new dropdowm option: location picker    不存在waypoint list的點，但儲存在mission action editor裡
// TODO: lookup and check which dropdown option should be hightlight, and show to label 
// TODO: 在地圖上點選位置後，把值存在label, 以及picker 