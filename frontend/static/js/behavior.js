let keyPresses = 0;
let totalKeyHold = 0;
let keyDownTime = {};

let mouseDistance = 0;
let mouseSpeed = 0;

let lastMouseX = null;
let lastMouseY = null;
let lastMouseTime = Date.now();

let clickCount = 0;
let scrollDistance = 0;
let idleTime = 0;

let lastActivity = Date.now();


// ------------------------------
// Keyboard
// ------------------------------

document.addEventListener("keydown", (e) => {

    keyPresses++;

    keyDownTime[e.code] = performance.now();

    lastActivity = Date.now();

});


document.addEventListener("keyup", (e) => {

    if(keyDownTime[e.code]){

        let hold = performance.now() - keyDownTime[e.code];

        totalKeyHold += hold;

        delete keyDownTime[e.code];

    }

});


// ------------------------------
// Mouse Movement
// ------------------------------

document.addEventListener("mousemove",(e)=>{

    if(lastMouseX!==null){

        let dx = e.clientX-lastMouseX;
        let dy = e.clientY-lastMouseY;

        let dist=Math.sqrt(dx*dx+dy*dy);

        mouseDistance+=dist;

        let now=Date.now();

        let dt=(now-lastMouseTime)/1000;

        if(dt>0){

            mouseSpeed=dist/dt;

        }

        lastMouseTime=now;

    }

    lastMouseX=e.clientX;
    lastMouseY=e.clientY;

    lastActivity=Date.now();

});


// ------------------------------
// Clicks
// ------------------------------

document.addEventListener("click",()=>{

    clickCount++;

    lastActivity=Date.now();

});


// ------------------------------
// Scroll
// ------------------------------

window.addEventListener("scroll",()=>{

    scrollDistance+=Math.abs(window.scrollY);

    lastActivity=Date.now();

});


// ------------------------------
// Idle Time
// ------------------------------

setInterval(()=>{

    idleTime=(Date.now()-lastActivity)/1000;

},1000);


// ------------------------------
// Browser Info
// ------------------------------

function getBrowser() {

    const ua = navigator.userAgent;

    if (ua.includes("Edg")) {
        return "Microsoft Edge";
    }

    if (ua.includes("Chrome")) {
        return "Chrome";
    }

    if (ua.includes("Firefox")) {
        return "Firefox";
    }

    if (ua.includes("Safari") && !ua.includes("Chrome")) {
        return "Safari";
    }

    return "Unknown";
}


// ------------------------------
// Operating System
// ------------------------------

function getOS() {

    const platform = navigator.platform;

    if (platform.startsWith("Win")) return "Windows";
    if (platform.startsWith("Mac")) return "macOS";
    if (platform.startsWith("Linux")) return "Linux";

    return "Unknown";
}


// ------------------------------
// Send Every 10 Seconds
// ------------------------------

setInterval(()=>{

    let avgHold=0;

    if(keyPresses>0){

        avgHold=totalKeyHold/keyPresses;

    }

    let typingSpeed=keyPresses/10;

    fetch("/api/behavior",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            typing_speed:typingSpeed,

            avg_key_hold:avgHold,

            mouse_speed:mouseSpeed,

            mouse_distance:mouseDistance,

            click_count:clickCount,

            scroll_distance:scrollDistance,

            idle_time:idleTime,

            screen_width:screen.width,

            screen_height:screen.height,

            browser:getBrowser(),

            operating_system:getOS()

        })

    });

    keyPresses=0;
    totalKeyHold=0;
    mouseDistance=0;
    clickCount=0;
    scrollDistance=0;

},10000);