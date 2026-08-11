const sessionStart =
    performance.now();


let currentTrustScore =
    88;


// ============================================================
// MONEY FORMATTER
// ============================================================

function money(value) {

    return "$" +
        Number(value).toLocaleString(
            "en-US",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );
}


// ============================================================
// LOAD ACCOUNT
// ============================================================

async function loadAccount() {

    const response =
        await fetch(
            "/api/accounts"
        );


    if (
        response.status === 401
    ) {

        window.location.href =
            "/";

        return;
    }


    const data =
        await response.json();


    renderAccount(
        data
    );
}


// ============================================================
// RENDER ACCOUNT
// ============================================================

function renderAccount(data) {

    document.getElementById(
        "balance-amount"
    ).textContent =
        money(
            data.balance
        );


    document.getElementById(
        "account-number"
    ).textContent =
        data.account_number;


    const list =
        document.getElementById(
            "tx-list"
        );


    list.innerHTML =
        "";


    data.transactions
        .slice(0, 8)
        .forEach(
            transaction => {

                const row =
                    document.createElement(
                        "div"
                    );


                row.className =
                    "tx-row";


                row.innerHTML = `

                    <div>

                        <div class="tx-merchant">
                            ${escapeHtml(
                                transaction.merchant
                            )}
                        </div>

                        <div class="tx-date">
                            ${escapeHtml(
                                transaction.date
                            )}
                        </div>

                    </div>

                    <div class="tx-amount ${transaction.type}">

                        ${
                            transaction.amount >= 0
                                ? "+"
                                : "-"
                        }

                        ${
                            money(
                                Math.abs(
                                    transaction.amount
                                )
                            )
                        }

                    </div>
                `;


                list.appendChild(
                    row
                );
            }
        );
}


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHtml(value) {

    const element =
        document.createElement(
            "div"
        );


    element.textContent =
        value;


    return element.innerHTML;
}


// ============================================================
// TRANSFER
// ============================================================

async function sendTransfer() {

    const recipient =
        document.getElementById(
            "recipient"
        ).value.trim()
        || "Recipient";


    const amount =
        parseFloat(
            document.getElementById(
                "amount"
            ).value
        );


    const message =
        document.getElementById(
            "transfer-msg"
        );


    if (
        !amount ||
        amount <= 0
    ) {

        message.textContent =
            "Enter an amount greater than $0.00";

        message.className =
            "error";

        return;
    }


    const response =
        await fetch(
            "/api/transfer",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        recipient:
                            recipient,

                        amount:
                            amount
                    })
            }
        );


    const data =
        await response.json();


    if (data.success) {

        message.textContent =
            `Sent ${money(amount)} to ${recipient}`;

        message.className =
            "success";


        document.getElementById(
            "amount"
        ).value = "";


        document.getElementById(
            "recipient"
        ).value = "";


        renderAccount(
            data.account
        );


        updateTrustDisplay(
            data.security
        );

    } else {

        message.textContent =
            data.message ||
            "Transfer failed";

        message.className =
            "error";
    }
}


// ============================================================
// GET TRUST STATUS
// ============================================================

async function updateTrustScore() {

    const response =
        await fetch(
            "/api/trust-score"
        );


    if (
        response.status === 401
    ) {

        window.location.href =
            "/";

        return;
    }


    const data =
        await response.json();


    updateTrustDisplay(
        data
    );
}


// ============================================================
// UPDATE SECURITY UI
// ============================================================

function updateTrustDisplay(data) {

    currentTrustScore =
        Number(
            data.trust_score ?? 88
        );


    const scoreElement =
        document.getElementById(
            "trust-score"
        );


    scoreElement.textContent =
        Math.round(
            currentTrustScore
        );


    scoreElement.className =
        "trust-score-value " +
        (
            currentTrustScore >= 70
                ? "high"
                : currentTrustScore >= 40
                    ? "medium"
                    : "low"
        );


    document.getElementById(
        "trust-status"
    ).textContent =
        "Risk level: " +
        (
            data.risk_level ||
            "LOW"
        );


    document.getElementById(
        "rl-action"
    ).textContent =
        data.action ||
        "MONITOR";


    document.getElementById(
        "crypto-mode"
    ).textContent =
        data.crypto_mode ||
        "AES-256-GCM";


    document.getElementById(
        "key-version"
    ).textContent =
        data.key_version ??
        1;


    document.getElementById(
        "key-rotations"
    ).textContent =
        data.key_rotation_count ??
        0;


    const reasons =
        document.getElementById(
            "security-reasons"
        );


    reasons.innerHTML =
        "";


    (
        data.reasons ||
        [
            "Behavior baseline initialized"
        ]
    )
    .slice(0, 5)
    .forEach(
        reason => {

            const li =
                document.createElement(
                    "li"
                );

            li.textContent =
                reason;

            reasons.appendChild(
                li
            );
        }
    );


    document.getElementById(
        "decision-time"
    ).textContent =
        new Date().toLocaleTimeString();
}


// ============================================================
// ATTACK SIMULATION
// ============================================================

async function simulateAnomaly() {

    const response =
        await fetch(
            "/api/update-behavior",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        change: -25
                    })
            }
        );


    const data =
        await response.json();


    updateTrustDisplay(
        data
    );


    if (
        data.active === false
    ) {

        alert(
            "EvoCrypt terminated the session."
        );


        window.location.href =
            "/";
    }
}


// ============================================================
// LOGOUT
// ============================================================

function logout() {

    fetch(
        "/api/logout",
        {
            method: "POST"
        }
    )
    .finally(
        () => {
            window.location.href =
                "/";
        }
    );
}


// ============================================================
// SIGNAL READOUT
// ============================================================

function updateSignalReadout() {

    if (
        window.EvoBehavior
    ) {

        document.getElementById(
            "sig-keystroke"
        ).textContent =
            window.EvoBehavior
                .keystrokeLabel;


        document.getElementById(
            "sig-pointer"
        ).textContent =
            window.EvoBehavior
                .pointerLabel;
    }


    const seconds =
        Math.floor(
            (
                performance.now() -
                sessionStart
            ) / 1000
        );


    const minutes =
        Math.floor(
            seconds / 60
        );


    const remainingSeconds =
        String(
            seconds % 60
        ).padStart(
            2,
            "0"
        );


    document.getElementById(
        "sig-session"
    ).textContent =
        `${minutes}:${remainingSeconds}`;
}


// ============================================================
// TRUST PULSE GRAPH
// ============================================================

const pulsePath =
    document.getElementById(
        "pulse-path"
    );


let pulsePhase = 0;


function drawPulse() {

    const width = 260;

    const mid = 30;


    const risk =
        (
            100 -
            currentTrustScore
        ) / 100;


    const amplitude =
        4 +
        risk * 20;


    const frequency =
        0.06 +
        risk * 0.05;


    const points = [];


    for (
        let i = 0;
        i <= 65;
        i++
    ) {

        const x =
            (
                width / 65
            ) * i;


        const spike =
            i % 11 === 0

                ? amplitude *
                  (
                      0.6 +
                      risk
                  )

                : 0;


        const y =
            mid +

            Math.sin(
                i * frequency +
                pulsePhase
            )
            *
            amplitude *
            0.4 +

            Math.sin(
                i * 0.9 +
                pulsePhase * 2
            )
            *
            spike *
            0.3;


        points.push(
            `${x.toFixed(1)},${y.toFixed(1)}`
        );
    }


    pulsePath.setAttribute(
        "d",
        "M" +
        points.join(" L")
    );


    if (
        currentTrustScore >= 70
    ) {

        pulsePath.setAttribute(
            "stroke",
            "#6ee8d8"
        );

    } else if (
        currentTrustScore >= 40
    ) {

        pulsePath.setAttribute(
            "stroke",
            "#e0bf55"
        );

    } else {

        pulsePath.setAttribute(
            "stroke",
            "#f2545b"
        );
    }


    pulsePhase +=
        0.12 +
        risk * 0.15;


    requestAnimationFrame(
        drawPulse
    );
}


// ============================================================
// CONNECT BEHAVIOR ENGINE TO DASHBOARD
// ============================================================

window.onSecurityUpdate =
    updateTrustDisplay;


// ============================================================
// INITIALIZATION
// ============================================================

loadAccount();

updateTrustScore();

requestAnimationFrame(
    drawPulse
);


setInterval(
    updateTrustScore,
    4000
);


setInterval(
    updateSignalReadout,
    1000
);