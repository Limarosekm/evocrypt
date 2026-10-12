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
    security: "Security Center",
    "security-intelligence": "Security Intelligence",
    "quantum-lab": "Quantum Security Lab"
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
    
// ============================================================
// HOME PAGE — EVOLUTIONARY SECURITY CARD
// ============================================================

const homeScore =
    document.getElementById(
        "home-trust-score"
    );

const homeRisk =
    document.getElementById(
        "home-risk-level"
    );

const homeAction =
    document.getElementById(
        "home-security-action"
    );

const homeKeyExchange =
    document.getElementById(
        "home-key-exchange"
    );

const homeCipher =
    document.getElementById(
        "home-data-cipher"
    );

const homeKeyVersion =
    document.getElementById(
        "home-key-version"
    );

const homeRotations =
    document.getElementById(
        "home-key-rotations"
    );

const protectionStatus =
    document.getElementById(
        "home-protection-status"
    );

const protectionIcon =
    document.getElementById(
        "home-protection-icon"
    );

const protectionText =
    document.getElementById(
        "home-protection-text"
    );

const protectionDot =
    document.getElementById(
        "evolutionary-status-dot"
    );


if (homeScore) {

    homeScore.textContent =
        Math.round(
            currentTrustScore
        );

    homeScore.className =
        "evolutionary-score " +
        riskTier;
}


if (homeRisk) {

    const riskLevel =
        data.risk_level ||
        "LOW";

    homeRisk.textContent =
        riskLevel;

    homeRisk.className =
        "evolutionary-risk-value " +
        riskTier;
}


if (homeAction) {

    homeAction.textContent =
        data.action ||
        "MONITOR";
}


if (homeKeyExchange) {

    homeKeyExchange.textContent =
        data.key_exchange ||
        "NONE";
}


if (homeCipher) {

    homeCipher.textContent =
        data.cipher ||
        data.crypto_mode ||
        "AES-256-GCM";
}


if (homeKeyVersion) {

    homeKeyVersion.textContent =
        data.key_version ??
        1;
}


if (homeRotations) {

    homeRotations.textContent =
        data.key_rotation_count ??
        0;
}


// ============================================================
// PROTECTION STATUS MESSAGE
// ============================================================

if (
    protectionStatus &&
    protectionIcon &&
    protectionText
) {

    protectionStatus.className =
        "evolutionary-protection";

    protectionIcon.textContent =
        "✓";


    if (
        data.crypto_mode ===
        "HYBRID_PQC"
    ) {

        protectionStatus.classList.add(
            "upgraded"
        );

        protectionIcon.textContent =
            "⚠";

        protectionText.textContent =
            "Protection upgraded — PQC hybrid active";

    } else if (
        data.crypto_mode ===
        "BLOCKED"
    ) {

        protectionStatus.classList.add(
            "critical"
        );

        protectionIcon.textContent =
            "×";

        protectionText.textContent =
            "Session protection blocked";

    } else {

        protectionText.textContent =
            "Standard protection active";
    }
}


// ============================================================
// STATUS DOT
// ============================================================

if (protectionDot) {

    protectionDot.className =
        "evolutionary-status-dot " +
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



// ============================================================
// QUANTUM SECURITY LAB — LIVE EXPERIMENT CONTROLLER
// ============================================================
let quantumPollTimer = null;
let quantumLastOutput = "";

async function analyzeQuantumRisk() {
    const algorithmElement = document.getElementById("quantum-algorithm");
    const resultBox = document.getElementById("quantum-risk-result");
    const button = document.getElementById("quantum-analyze-button");
    if (!algorithmElement || !resultBox || !button) return;

    button.disabled = true;
    resultBox.textContent = "Analyzing quantum risk...";
    try {
        const response = await fetch(
            `/api/quantum-risk?algorithm=${encodeURIComponent(algorithmElement.value)}`,
            { credentials: "same-origin" }
        );
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "Risk analysis failed.");
        resultBox.replaceChildren();
        const heading = document.createElement("h3");
        heading.textContent = `Risk: ${data.risk}`;
        const category = document.createElement("p");
        category.textContent = `Category: ${data.category}`;
        const reason = document.createElement("p");
        reason.textContent = data.quantum_reason;
        const recommendation = document.createElement("p");
        recommendation.textContent = `Recommendation: ${data.recommendation}`;
        const note = document.createElement("p");
        note.textContent = data.quantum_computer_assumption;
        resultBox.append(heading, category, reason, recommendation, note);
    } catch (error) {
        resultBox.textContent = `Unable to analyze risk: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

async function startQuantumExperiment() {
    const button = document.getElementById("qsl-run-button");
    const consoleBox = document.getElementById("qsl-console");
    if (!button || !consoleBox) return;
    button.disabled = true;
    setQuantumStatus("running", "Starting");
    consoleBox.textContent = "Requesting experiment start...\n";
    quantumLastOutput = "";

    try {
        const response = await fetch("/api/quantum-demo/start", {
            method: "POST",
            credentials: "same-origin"
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "Could not start experiment.");
        await pollQuantumExperiment();
        if (quantumPollTimer) clearInterval(quantumPollTimer);
        quantumPollTimer = setInterval(pollQuantumExperiment, 1500);
    } catch (error) {
        setQuantumStatus("failed", "Could not start");
        consoleBox.textContent += `\nERROR: ${error.message}\n`;
        button.disabled = false;
    }
}

async function pollQuantumExperiment() {
    try {
        const response = await fetch("/api/quantum-demo/status", { credentials: "same-origin" });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "Status request failed.");

        const consoleBox = document.getElementById("qsl-console");
        if (consoleBox && data.output !== quantumLastOutput) {
            quantumLastOutput = data.output || "";
            consoleBox.textContent = quantumLastOutput || "Experiment process started; waiting for output...";
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }
        document.getElementById("qsl-stage").textContent = data.stage || "Running";
        document.getElementById("qsl-time").textContent = data.started_at ? `Started ${new Date(data.started_at).toLocaleTimeString()}` : "";
        setQuantumStatus(data.status || "running", data.status === "completed" ? "COMPLETE" : data.status === "failed" ? "FAILED" : "RUNNING");
        parseQuantumConsole(data.output || "");

        if (data.status === "completed" || data.status === "failed") {
            if (quantumPollTimer) clearInterval(quantumPollTimer);
            quantumPollTimer = null;
            document.getElementById("qsl-run-button").disabled = false;
            document.getElementById("qsl-progress-bar").style.width = data.status === "completed" ? "100%" : "100%";
        } else {
            document.getElementById("qsl-progress-bar").style.width = "65%";
        }
    } catch (error) {
        document.getElementById("qsl-stage").textContent = `Status check failed: ${error.message}`;
    }
}

function setQuantumStatus(status, label) {
    const pill = document.getElementById("qsl-status-pill");
    if (!pill) return;
    pill.className = `qsl-status ${status}`;
    pill.textContent = label.toUpperCase();
    if (status === "running") document.getElementById("qsl-progress-bar").style.width = "25%";
    if (status === "idle") document.getElementById("qsl-progress-bar").style.width = "0%";
}

function parseQuantumConsole(output) {
    const lines = output.split(/\r?\n/);
    const joined = lines.join("\n");
    const jobMatch = joined.match(/job(?:\s+id)?\s*[:=]\s*([A-Za-z0-9_-]{8,})/i)
        || joined.match(/\b(db[a-z0-9]{8,})\b/i);
    if (jobMatch) document.getElementById("qsl-job-id").textContent = jobMatch[1];

    const orderMatch = joined.match(/\b(?:estimated\s+)?order\s*(?:r)?\s*[:=]\s*(\d+)/i)
        || joined.match(/\br\s*=\s*(\d+)/i);
    if (orderMatch) document.getElementById("qsl-order").textContent = `r = ${orderMatch[1]}`;

    const factorMatch = joined.match(/(?:factors?|recovered factors?)\s*[:=]\s*(\d+)\s*(?:and|,|x|×|\*)\s*(\d+)/i)
        || joined.match(/\bp\s*=\s*(\d+)[,\s]+q\s*=\s*(\d+)/i)
        || joined.match(/\b(\d+)\s*[×x*]\s*(\d+)\s*=\s*15\b/i);
    if (factorMatch) {
        document.getElementById("qsl-factors").textContent = `${factorMatch[1]} × ${factorMatch[2]}`;
        document.getElementById("qsl-factor-equation").textContent = `N = ${factorMatch[1]} × ${factorMatch[2]}`;
        document.getElementById("qsl-factor-note").textContent = "Parsed from actual experiment output";
    }

    if (/toy rsa.*verified\s*[:=]?\s*true|decryption verified|verified\s*[:=]\s*true/i.test(joined)) {
        document.getElementById("qsl-rsa-check").textContent = "PASS";
        document.getElementById("qsl-rsa-check").className = "pass";
    } else if (/toy rsa.*verified\s*[:=]?\s*false|verification failed/i.test(joined)) {
        document.getElementById("qsl-rsa-check").textContent = "FAIL";
        document.getElementById("qsl-rsa-check").className = "fail";
    }

    if (/round.?trip.{0,30}(pass|success)|encryption\/decryption.{0,30}pass|pqc.*pass/i.test(joined)) {
        document.getElementById("qsl-pqc-check").textContent = "PASS";
        document.getElementById("qsl-roundtrip").textContent = "PASS";
        document.getElementById("qsl-roundtrip").className = "pass";
    }
    if (/tamper.{0,40}(pass|detected|reject)|tampering detection.{0,30}pass/i.test(joined)) {
        document.getElementById("qsl-tamper").textContent = "PASS";
        document.getElementById("qsl-tamper").className = "pass";
        document.getElementById("qsl-pqc-note").textContent = "Round-trip and tamper test confirmed";
    }

    // Render only count-like lines actually present in stdout.
    const counts = [];
    for (const line of lines) {
        const m = line.match(/^\s*([01]{4,16})\s*[:=]\s*(\d+)\s*$/);
        if (m) counts.push({ bits: m[1], count: Number(m[2]) });
    }
    const measurementBox = document.getElementById("qsl-measurements");
    if (counts.length && measurementBox) {
        const unique = new Map();
        counts.forEach(item => unique.set(item.bits, item.count));
        const sorted = [...unique.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12);
        const max = Math.max(...sorted.map(x => x[1]), 1);
        measurementBox.replaceChildren();
        sorted.forEach(([bits, count]) => {
            const row = document.createElement("div");
            row.className = "qsl-measurement";
            const label = document.createElement("span");
            label.textContent = bits;
            const amount = document.createElement("span");
            amount.className = "qsl-count";
            amount.textContent = `${count} shots (${Math.round(count / max * 100)}% of max)`;
            row.append(label, amount);
            measurementBox.appendChild(row);
        });
    }
}

async function resetQuantumExperiment() {
    if (quantumPollTimer) clearInterval(quantumPollTimer);
    quantumPollTimer = null;
    try {
        const response = await fetch("/api/quantum-demo/reset", {
            method: "POST", credentials: "same-origin"
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "Cannot reset while running.");
        ["qsl-job-id", "qsl-factors", "qsl-rsa-check", "qsl-pqc-check"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = id === "qsl-job-id" ? "Waiting for run" : id === "qsl-factors" ? "— × —" : "NOT RUN";
        });
        ["qsl-order", "qsl-factor-equation"].forEach(id => document.getElementById(id).textContent = id === "qsl-order" ? "r = —" : "N = —");
        ["qsl-roundtrip", "qsl-tamper"].forEach(id => {
            const el = document.getElementById(id);
            el.textContent = "NOT RUN"; el.className = "";
        });
        document.getElementById("qsl-factor-note").textContent = "No results yet";
        document.getElementById("qsl-pqc-note").textContent = "ML-KEM + authenticated encryption";
        document.getElementById("qsl-measurements").innerHTML = '<div class="qsl-empty">Measurements will appear after the run starts.</div>';
        document.getElementById("qsl-console").textContent = "Ready. Click “Run IBM experiment + PQC tests” to launch the real workflow.";
        document.getElementById("qsl-stage").textContent = "Ready to run";
        document.getElementById("qsl-time").textContent = "";
        document.getElementById("qsl-progress-bar").style.width = "0%";
        document.getElementById("qsl-run-button").disabled = false;
        setQuantumStatus("idle", "READY");
    } catch (error) {
        document.getElementById("qsl-stage").textContent = error.message;
    }
}
