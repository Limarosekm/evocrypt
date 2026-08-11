(() => {

    // ============================================================
    // BEHAVIOR VARIABLES
    // ============================================================

    let keyPressCount = 0;

    let totalKeyHold = 0;

    const keyDownTimes = {};


    let mouseDistance = 0;

    let mouseSpeed = 0;

    let lastMouseX = null;

    let lastMouseY = null;

    let lastMouseTime =
        Date.now();


    let clickCount = 0;

    let scrollDistance = 0;

    let idleTime = 0;

    let lastActivity =
        Date.now();


    const labels = {

        keystroke:
            "collecting",

        pointer:
            "collecting"
    };


    // ============================================================
    // KEYBOARD COLLECTION
    // ============================================================

    document.addEventListener(
        "keydown",
        (event) => {

            keyPressCount++;

            keyDownTimes[
                event.code
            ] = performance.now();

            lastActivity =
                Date.now();

            labels.keystroke =
                "active";
        }
    );


    document.addEventListener(
        "keyup",
        (event) => {

            const start =
                keyDownTimes[
                    event.code
                ];


            if (start !== undefined) {

                totalKeyHold +=
                    performance.now() -
                    start;


                delete keyDownTimes[
                    event.code
                ];
            }
        }
    );


    // ============================================================
    // MOUSE COLLECTION
    // ============================================================

    document.addEventListener(
        "mousemove",
        (event) => {

            if (
                lastMouseX !== null &&
                lastMouseY !== null
            ) {

                const dx =
                    event.clientX -
                    lastMouseX;

                const dy =
                    event.clientY -
                    lastMouseY;


                const distance =
                    Math.hypot(
                        dx,
                        dy
                    );


                mouseDistance +=
                    distance;


                const now =
                    Date.now();


                const deltaTime =
                    (
                        now -
                        lastMouseTime
                    ) / 1000;


                if (deltaTime > 0) {

                    mouseSpeed =
                        distance /
                        deltaTime;
                }


                labels.pointer =
                    "active";


                lastMouseTime =
                    now;
            }


            lastMouseX =
                event.clientX;

            lastMouseY =
                event.clientY;

            lastActivity =
                Date.now();
        }
    );


    // ============================================================
    // CLICK COLLECTION
    // ============================================================

    document.addEventListener(
        "click",
        () => {

            clickCount++;

            lastActivity =
                Date.now();
        }
    );


    // ============================================================
    // SCROLL COLLECTION
    // ============================================================

    window.addEventListener(
        "scroll",
        () => {

            scrollDistance +=
                Math.abs(
                    window.scrollY
                );

            lastActivity =
                Date.now();
        }
    );


    // ============================================================
    // IDLE TIME
    // ============================================================

    setInterval(
        () => {

            idleTime =
                (
                    Date.now() -
                    lastActivity
                ) / 1000;

        },
        1000
    );


    // ============================================================
    // BROWSER DETECTION
    // ============================================================

    function getBrowser() {

        const userAgent =
            navigator.userAgent;


        if (
            userAgent.includes("Edg")
        ) {

            return "Microsoft Edge";
        }


        if (
            userAgent.includes("Chrome")
        ) {

            return "Chrome";
        }


        if (
            userAgent.includes("Firefox")
        ) {

            return "Firefox";
        }


        if (
            userAgent.includes("Safari") &&
            !userAgent.includes("Chrome")
        ) {

            return "Safari";
        }


        return "Unknown";
    }


    // ============================================================
    // OPERATING SYSTEM
    // ============================================================

    function getOperatingSystem() {

        const platform =
            navigator.platform;


        if (
            platform.startsWith("Win")
        ) {

            return "Windows";
        }


        if (
            platform.startsWith("Mac")
        ) {

            return "macOS";
        }


        if (
            platform.startsWith("Linux")
        ) {

            return "Linux";
        }


        return "Unknown";
    }


    // ============================================================
    // SEND BEHAVIOR TO SERVER
    // ============================================================

    async function sendBehavior() {

        const averageKeyHold =
            keyPressCount > 0

                ? totalKeyHold /
                  keyPressCount

                : 0;


        const payload = {

            typing_speed:
                keyPressCount / 5,

            avg_key_hold:
                averageKeyHold,

            mouse_speed:
                mouseSpeed,

            mouse_distance:
                mouseDistance,

            click_count:
                clickCount,

            scroll_distance:
                scrollDistance,

            idle_time:
                idleTime,

            screen_width:
                screen.width,

            screen_height:
                screen.height,

            browser:
                getBrowser(),

            operating_system:
                getOperatingSystem()
        };


        try {

            const response =
                await fetch(
                    "/api/behavior",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                payload
                            )
                    }
                );


            if (
                response.status === 401
            ) {

                window.location.href =
                    "/";

                return;
            }


            const result =
                await response.json();


            if (
                result.security &&
                window.onSecurityUpdate
            ) {

                window.onSecurityUpdate(
                    result.security
                );
            }


        } catch (error) {

            console.warn(
                "Behavior delivery failed:",
                error
            );
        }


        // Reset interval measurements

        keyPressCount = 0;

        totalKeyHold = 0;

        mouseDistance = 0;

        mouseSpeed = 0;

        clickCount = 0;

        scrollDistance = 0;
    }


    // ============================================================
    // PUBLIC BEHAVIOR STATE
    // ============================================================

    window.EvoBehavior = {

        get keystrokeLabel() {
            return labels.keystroke;
        },

        get pointerLabel() {
            return labels.pointer;
        }
    };


    // ============================================================
    // SEND EVERY 5 SECONDS
    // ============================================================

    setInterval(
        sendBehavior,
        5000
    );

})();