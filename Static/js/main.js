function openPage(pageName, elmnt, color) {
    // Hide all elements with class="tabcontent" by default */
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
  
    // Remove the background color of all tablinks/buttons
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].style.backgroundColor = "";
    }
  
    // Show the specific tab content
    document.getElementById(pageName).style.display = "block";
  
    // Add the specific color to the button used to open the tab content
    elmnt.style.backgroundColor = color;
    if (pageName == "Dashboard")
      document.getElementById(pageName).innerHTML = '<object type="text/html" data="../view/Dashboard.html" width="100%" height="800px"></object>';
    else  if (pageName == "Setup")
      document.getElementById(pageName).innerHTML = '<object type="text/html" data="../view/Setup.html" width="100%" height="800px"></object>';
    else  if (pageName == "System")
      document.getElementById(pageName).innerHTML = '<object type="text/html" data="../view/System.html" width="100%" height="800px"></object>';
    else  if (pageName == "Log")
      document.getElementById(pageName).innerHTML = '<object type="text/html" data="../view/Log.html" width="100%" height="800px"></object>';
  }
  
  function deleteAllCookies() {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        var eqPos = cookie.indexOf("=");
        var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
  }
  
  function Logout(){
    console.log("Clear all cookies");
    deleteAllCookies();
    // TODO: call backend to clear cookie
    $.ajax({
      type: "get",
      //data: {start},
      url: "/logout",
      success: function (result){
        location.href = '/login';
      }
    });
  }
  
    
  function init(){
      // Get the element with id="defaultOpen" and click on it
      document.getElementById("defaultOpen").click();
  };    