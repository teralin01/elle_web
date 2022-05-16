

// 创建文字：canvas 2D对象，内容文字，画布X轴，Y轴，样式
function DrawCPUText(ctx, title, x, y, style) {
    ctx.save();
    ctx.beginPath();
    ctx.font = style.font + " Arial"; 
    ctx.fillStyle = style.color;
    ctx.textBaseline = 'middle';
    var tw = ctx.measureText(title).width;
    ctx.fillText(title, x - tw / 2, y);
    ctx.closePath();
    ctx.restore();
}

function UsagePie(width, height, setValueObj,usage, canvas_cpu,title){
    var total = 100; // Togal usage
    var startAngle = (Math.PI*-1/2); // 圆开始角度
    var endAngle = usage; // 圆结束角度（已用容量）
    var currValue = usage; // 已用容量
    var context = canvas_cpu.getContext("2d");
    // 设置画布宽高
    canvas_cpu.setAttribute('width', width);
    canvas_cpu.setAttribute('height', height);

    var circleX = width / 2,  
        circleY = height / 2 - setValueObj['labelWidth']; 
    //console.log("Usage loc: "+circleX+" "+circleY)
    var radius = 0;
    if( circleX <= circleY)
    {
        radius = width / 2 - setValueObj['labelWidth']*3;
    }
    else
    {
        radius = height / 2 - setValueObj['labelWidth']*3;
    }
    
    // Text in the circle：usage
    var text = currValue + "%";
    DrawCPUText(
        context, 
        text,
        circleX, 
        circleY, 
        {
            font:setValueObj["fontSize"],
            color: setValueObj["fontColor"],
        }
    );

    // Text in the bottom of chart 
    var title_text = title;
    DrawCPUText(
        context, 
        title_text,
        circleX, 
        height/2 + radius+10, 
        {
            font:"15px",
            color: setValueObj["fontColor"],
        }
    );

    // Draw background chart
    context.save();
    context.beginPath();
    context.strokeStyle = "#e7e7e7";
    context.lineWidth = setValueObj['labelWidth'];
    context.arc(circleX, circleY, radius, 0, Math.PI * 2, false);
    context.closePath();
    context.stroke();
    context.restore();


    // Draw usage chart
    context.save();
    context.beginPath();
    context.strokeStyle = setValueObj["color"];
    context.lineWidth = setValueObj['labelWidth'];
    context.arc(circleX, circleY, radius, startAngle, (Math.PI*-1/2) + endAngle/100 * (Math.PI*2), false);
    context.stroke();
    context.restore();
}

$(function(){
    window.onresize = function(){
        Width = $(window).width()/5;
        Height = $(window).height()/5;
    };
});


var initStyle = {
    labelWidth: 8,
    fontColor: "#555",
    fontSize: "20px",
    color: "#3390d7"
};

var Width = $(window).width()/5;
var Height = $(window).height()/5;

function updateUsage(){
    $.ajax({
        type: "get",
        url: "/control/HardwareStatus",
        success: function (result){
            var memUsage = parseInt(( result.memUsed / result.memTotal)*100 );
            UsagePie(Width, Height, initStyle,result.CPU_Persent, canvas_cpu,"CPU usage");
            UsagePie(Width, Height, initStyle,(result.memUsed/1024 / 1024 / 1024).toFixed(2),canvas_mem,"Mem_usage");
        }
      });

}

var canvas_cpu = document.getElementById("CPUusageChart");
var canvas_mem = document.getElementById("MemUsageChart");

updateUsage();
var timeoutID = window.setInterval((
     () => updateUsage()
), 2000);
