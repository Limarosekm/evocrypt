const sessionStart =
    performance.now();


let currentTrustScore =
    88;


let latestAccount =
    null;


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
// PAGE / TAB NAVIGATION
// ============================================================

const pageTitles = {
    overview: "Account Overview",
    cards: "Cards",
    statements: "Statements",
    security: "Security Center"
};


function showPage(pageName, navElement) {

    document
        .querySelectorAll(".page")
        .forEach(
            page => page.classList.remove("active")
        );

    document
        .querySelectorAll(".nav-item")
        .forEach(
            item => item.classList.remove("active")
        );


    const target =
        document.getElementById(
            "page-" + pageName
        );

    if (target) {
        target.classList.add("active");
    }

    if (navElement) {
        navElement.classList.add("active");
    } else {

        const fallbackNav =
            document.querySelector(
                `.nav-item[data-page="${pageName}"]`
            );

        if (fallbackNav) {
            fallbackNav.classList.add("active");
        }
    }


    const title =
        document.getElementById(
            "page-title"
        );

    if (title) {
        title.textContent =
            pageTitles[pageName] ||
            "Dashboard";
    }
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

    latestAccount = data;

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


    renderCards(
        data.cards || []
    );

    renderStatements(
        data.statements || []
    );
}


// ============================================================
// RENDER CARDS
// ============================================================

function renderCards(cards) {

    const grid =
        document.getElementById(
            "cards-grid"
        );

    if (!grid) {
        return;
    }

    grid.innerHTML =
        "";

    if (cards.length === 0) {

        grid.innerHTML =
            "<div class=\"empty-state\">No cards on this account.</div>";

        return;
    }

    cards.forEach(
        card => {

            const tile =
                document.createElement(
                    "div"
                );

            tile.className =
                "bank-card" +
                (
                    card.status === "frozen"
                        ? " frozen"
                        : ""
                );

            tile.innerHTML = `

                <div class="bank-card-top">

                    <span class="bank-card-network">
                        ${escapeHtml(card.network)}
                    </span>

                    <span class="bank-card-status">
                        ${
                            card.status === "frozen"
                                ? "FROZEN"
                                : "ACTIVE"
                        }
                    </span>

                </div>

                <div class="bank-card-number">
                    •••• •••• •••• ${escapeHtml(card.last4)}
                </div>

                <div class="bank-card-bottom">

                    <div>
                        <div class="bank-card-label">Card holder</div>
                        <div class="bank-card-value">${escapeHtml(card.nickname)}</div>
                    </div>

                    <div>
                        <div class="bank-card-label">Expires</div>
                        <div class="bank-card-value">${escapeHtml(card.expiry)}</div>
                    </div>

                </div>

                <button
                    class="bank-card-toggle"
                    onclick="toggleCard('${card.id}')"
                >
                    ${
                        card.status === "frozen"
                            ? "Unfreeze card"
                            : "Freeze card"
                    }
                </button>
            `;

            grid.appendChild(
                tile
            );
        }
    );
}


// ============================================================
// TOGGLE CARD FREEZE STATE
// ============================================================

async function toggleCard(cardId) {

    try {

        const response =
            await fetch(
                "/api/cards/toggle",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            card_id: cardId
                        })
                }
            );

        if (response.status === 401) {

            window.location.href = "/";

            return;
        }

        const data =
            await response.json();

        if (data.success) {
            renderAccount(
                data.account
            );
        }

    } catch (error) {

        console.warn(
            "Card toggle failed:",
            error
        );
    }
}


// ============================================================
// RENDER STATEMENTS
// ============================================================

function renderStatements(statements) {

    const list =
        document.getElementById(
            "statements-list"
        );

    if (!list) {
        return;
    }

    list.innerHTML =
        "";

    if (statements.length === 0) {

        list.innerHTML =
            "<div class=\"empty-state\">No statements available yet.</div>";

        return;
    }

    statements.forEach(
        statement => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "statement-row";

            row.innerHTML = `

                <div>

                    <div class="statement-label">
                        ${escapeHtml(statement.label)}
                    </div>

                    <div class="statement-period">
                        Period ending ${escapeHtml(statement.period_end)}
                    </div>

                </div>

                <button
                    class="statement-download"
                    onclick="downloadStatement('${statement.id}', '${escapeHtml(statement.label)}')"
                >
                    Download PDF
                </button>
            `;

            list.appendChild(
                row
            );
        }
    );
}


// ============================================================
// DOWNLOAD STATEMENT (DEMO)
// ============================================================

function downloadStatement(statementId, label) {

    const account =
        latestAccount ||
        {};

    const lines = [

        "SecureTrust Bank",
        "Account Statement — " + label,
        "Account: " + (account.account_number || ""),
        "",
        "This is a demo statement generated for " +
        "presentation purposes only."

    ];

    const blob =
        new Blob(
            [lines.join("\n")],
            { type: "text/plain" }
        );

    const url =
        URL.createObjectURL(
            blob
        );

    const link =
        document.createElement(
            "a"
        );

    link.href =
        url;

    link.download =
        `securetrust-statement-${statementId}.txt`;

    document.body.appendChild(
        link
    );

    link.click();

    document.body.removeChild(
        link
    );

    URL.revokeObjectURL(
        url
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


    const riskTier =
        currentTrustScore >= 70
            ? "high"
            : currentTrustScore >= 40
                ? "medium"
                : "low";


    scoreElement.textContent =
        Math.round(
            currentTrustScore
        );


    scoreElement.className =
        "trust-score-value " +
        riskTier;


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


    // Keep the always-visible topbar badge in sync so the
    // live trust score is visible from any page, not just
    // the Security Center.
    const topbarValue =
        document.getElementById(
            "topbar-trust-value"
        );

    const topbarDot =
        document.getElementById(
            "topbar-trust-dot"
        );

    if (topbarValue) {

        topbarValue.textContent =
            Math.round(
                currentTrustScore
            );
    }

    if (topbarDot) {

        topbarDot.className =
            "topbar-trust-dot " +
            riskTier;
    }
}


// ============================================================
// ATTACK SIMULATION
// ============================================================


async function simulateAnomaly(severity = "moderate") {

    try {

        const response =
            await fetch(
                "/api/simulate-hijack",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ severity: severity })
                }
            );

        if (response.status === 401) {

            window.location.href = "/";

            return;
        }

        const data = await response.json();

        updateTrustDisplay(data);

        if (data.active === false) {

            alert("Your session was ended — possible session hijacking detected.");

            window.location.href = "/";
        }

    } catch (error) {

        console.warn("Simulation request failed:", error);
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
        window.SessionBehavior
    ) {

        document.getElementById(
            "sig-keystroke"
        ).textContent =
            window.SessionBehavior
                .keystrokeLabel;


        document.getElementById(
            "sig-pointer"
        ).textContent =
            window.SessionBehavior
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
// ============================================================
// RL POLICY DEMONSTRATION
// ============================================================

async function runRLDemo(scenario) {

    const resultBox =
        document.getElementById(
            "rl-demo-result"
        );

    resultBox.innerHTML =
        "Running trained policy...";

    try {

        const response =
            await fetch(
                "/api/rl-demo",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            scenario:
                                scenario
                        })
                }
            );

        const data =
            await response.json();


        if (!data.success) {

            resultBox.innerHTML =
                `
                <div class="rl-error">
                    ${escapeHtml(
                        data.message ||
                        "Policy demonstration failed."
                    )}
                </div>
                `;

            return;
        }


        const inputs =
            data.inputs;

        const decision =
            data.decision;


        resultBox.innerHTML = `

            <div class="rl-result-title">
                ${formatScenario(
                    data.scenario
                )}
            </div>


            <div class="rl-section-label">
                SECURITY INPUTS
            </div>


            <div class="rl-input-grid">

                <div>
                    <span>Trust</span>
                    <strong>
                        ${inputs.trust_score}
                    </strong>
                </div>

                <div>
                    <span>Threat</span>
                    <strong>
                        ${inputs.threat_score}
                    </strong>
                </div>

                <div>
                    <span>Behavior</span>
                    <strong>
                        ${inputs.behavioral_risk}
                    </strong>
                </div>

                <div>
                    <span>Device</span>
                    <strong>
                        ${inputs.device_risk}
                    </strong>
                </div>

                <div>
                    <span>Transaction</span>
                    <strong>
                        ${inputs.transaction_risk}
                    </strong>
                </div>

                <div>
                    <span>Recovery</span>
                    <strong>
                        ${inputs.recovery_phase}
                    </strong>
                </div>

            </div>


            <div class="rl-section-label">
                POLICY STATE
            </div>


            <div class="rl-state">
                ${escapeHtml(
                    decision.state
                )}
            </div>


            <div class="rl-section-label">
                POLICY DECISION
            </div>


            <div class="rl-action">
                ${escapeHtml(
                    decision.action
                )}
            </div>


            <div class="rl-meta">

                <span>
                    Risk:
                    <strong>
                        ${escapeHtml(
                            decision.risk_level
                        )}
                    </strong>
                </span>

                <span>
                    Confidence:
                    <strong>
                        ${decision.confidence}
                    </strong>
                </span>

            </div>


            <div class="rl-section-label">
                EXPLANATION
            </div>


            <ul class="rl-reasons">

                ${
                    (decision.reasons || [])
                        .slice(0, 4)
                        .map(
                            reason =>
                                `<li>${escapeHtml(
                                    reason
                                )}</li>`
                        )
                        .join("")
                }

            </ul>

        `;

    } catch (error) {

        console.error(
            "RL demo failed:",
            error
        );

        resultBox.innerHTML =
            `
            <div class="rl-error">
                Unable to run the adaptive policy.
            </div>
            `;
    }
}


function formatScenario(value) {

    return value
        .split("_")
        .map(
            word =>
                word.charAt(0).toUpperCase() +
                word.slice(1)
        )
        .join(" ");
}