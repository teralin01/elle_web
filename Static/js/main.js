function openPage(pageName) {
    if (pageName == "Dashboard")
      document.getElementById("pageContent").innerHTML = '<object type="text/html" data="/view/Dashboard.html" width="100%" height="1024px"></object>';
    else  if (pageName == "Setup")
      document.getElementById("pageContent").innerHTML = '<object type="text/html" data="/view/Setup.html" width="100%" height="1024px"></object>';
    else  if (pageName == "System")
      document.getElementById("pageContent").innerHTML = '<object type="text/html" data="/view/System.html" width="100%" height="1024px"></object>';
    else  if (pageName == "Log")
      document.getElementById("pageContent").innerHTML = '<object type="text/html" data="/view/Log.html" width="100%" height="1024px"></object>';
    else if (pageName == "Logout")
      Logout();
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
      url: "/logout",
      success: function (result){
        location.href = '/login';
      }
    });
  }
  
  // Never used now. Plan to use it in the future. 
  function isMobileDevice() {
    const mobileDevice = ['Android', 'webOS', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'Windows Phone']
    let isMobileDevice = mobileDevice.some(e => navigator.userAgent.match(e))
    return isMobileDevice
 }

  $(document).ready(function(){
    document.getElementById("Dashboard").click();
    $("#collapse").click(function(){
        $("#sidebar").toggleClass("active");
        $(".fa-align-left").toggleClass("fa-chevron-circle-right");
    })
})