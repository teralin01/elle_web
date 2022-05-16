    // Connecting to ROS
    // -----------------
    var rosBridgePath = '10.1.30.172:9090';  // TODO: query path from backend
    var ros = new ROSLIB.Ros();
    
    // If there is an error on the backend, an 'error' emit will be emitted.
    ros.on('error', function(error) {
      console.log('Web Socket Connection error: '+error);
    });
    
    // Find out exactly when we made a connection.
    ros.on('connection', function() {
      console.log('Web Socket Connection made!');
    });
    
    ros.on('close', function() {
      console.log('Web Socket Connection closed.');
    });
    
    // Create a connection to the rosbridge WebSocket server.
    ros.connect('ws://'+rosBridgePath);
    var windowWidth = window.innerWidth;
    var windowHeight = window.innerHeight;
    var panOn = false; 
    var zoomStatus = false;
    $(window).resize(function() {
        clearTimeout(window.resizedFinished);
        window.resizedFinished = setTimeout(function(){
            windowWidth = window.innerWidth;
            windowHeight = window.innerHeight;
            console.log("Resized finished: width:"+windowWidth+"  height:"+windowHeight )
            window.location.reload();    
        }, 250);
    });