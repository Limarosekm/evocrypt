const sessionStart = performance.now();
let currentTrustScore = 88;

function fmtMoney(n) {
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function loadAccount() {
  const res = await fetch('/api/accounts');
  if (res.status === 401) { window.location.href = '/'; return; }
  const data = await res.json();
  renderAccount(data);
}

function renderAccount(data) {
  document.getElementById('balance-amount').textContent = fmtMoney(data.balance);
  document.getElementById('account-number').textContent = data.account_number;

  const list = document.getElementById('tx-list');
  list.innerHTML = '';
  data.transactions.slice(0, 8).forEach(tx => {
    const row = document.createElement('div');
    row.className = 'tx-row';
    const sign = tx.amount >= 0 ? '+' : '-';
    row.innerHTML = `
      <div>
        <div class="tx-merchant">${escapeHtml(tx.merchant)}</div>
        <div class="tx-date">${escapeHtml(tx.date)}</div>
      </div>
      <div class="tx-amount ${tx.type}">${sign}${fmtMoney(Math.abs(tx.amount))}</div>
    `;
    list.appendChild(row);
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function sendTransfer() {
  const recipient = document.getElementById('recipient').value.trim() || 'Recipient';
  const amount = parseFloat(document.getElementById('amount').value);
  const msg = document.getElementById('transfer-msg');

  if (!amount || amount <= 0) {
    msg.textContent = 'Enter an amount greater than $0.00';
    msg.className = 'error';
    return;
  }

  const res = await fetch('/api/transfer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipient, amount })
  });
  const data = await res.json();

  if (data.success) {
    msg.textContent = `Sent ${fmtMoney(amount)} to ${recipient}`;
    msg.className = 'success';
    document.getElementById('amount').value = '';
    document.getElementById('recipient').value = '';
    renderAccount(data.account);
    updateTrustDisplay(data.trust_score);
  } else {
    msg.textContent = data.message || 'Transfer failed';
    msg.className = 'error';
  }
}

async function updateTrustScore() {
  const res = await fetch('/api/trust-score');
  if (res.status === 401) { window.location.href = '/'; return; }
  const data = await res.json();
  updateTrustDisplay(data.trust_score, data.status);
}

function updateTrustDisplay(score, status) {
  currentTrustScore = score;
  status = status || (score >= 70 ? 'High' : score >= 40 ? 'Medium' : 'Low');

  const el = document.getElementById('trust-score');
  el.textContent = score;
  el.className = 'trust-score-value ' + (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');

  document.getElementById('trust-status').textContent = 'Trust level: ' + status;
}

async function simulateAnomaly() {
  await fetch('/api/update-behavior', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ change: -25 })
  });
  updateTrustScore();
}

function logout() {
  fetch('/api/logout', { method: 'POST' }).finally(() => {
    window.location.href = '/';
  });
}

window.onTrustScoreChanged = updateTrustScore;

// --- Signal readout (from behavioral.js) ---
function updateSignalReadout() {
  if (window.EvoBehavior) {
    document.getElementById('sig-keystroke').textContent = window.EvoBehavior.keystrokeLabel;
    document.getElementById('sig-pointer').textContent = window.EvoBehavior.pointerLabel;
  }
  const elapsed = Math.floor((performance.now() - sessionStart) / 1000);
  const mins = Math.floor(elapsed / 60);
  const secs = (elapsed % 60).toString().padStart(2, '0');
  document.getElementById('sig-session').textContent = `${mins}:${secs}`;
}

// --- Animated security pulse waveform ---
const pulsePath = document.getElementById('pulse-path');
let pulsePhase = 0;

function drawPulse() {
  const width = 260, height = 60, mid = height / 2;
  // Higher trust -> calmer wave. Lower trust -> spikier, faster wave.
  const risk = (100 - currentTrustScore) / 100; // 0 = calm, 1 = agitated
  const amplitude = 4 + risk * 20;
  const frequency = 0.06 + risk * 0.05;
  const points = [];
  const steps = 65;
  for (let i = 0; i <= steps; i++) {
    const x = (width / steps) * i;
    const spike = (i % 11 === 0) ? amplitude * (0.6 + risk) : 0;
    const y = mid + Math.sin(i * frequency + pulsePhase) * amplitude * 0.4 + Math.sin(i * 0.9 + pulsePhase * 2) * spike * 0.3;
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  pulsePath.setAttribute('d', 'M' + points.join(' L'));

  const color = currentTrustScore >= 70 ? '#6ee8d8' : currentTrustScore >= 40 ? '#e0bf55' : '#f2545b';
  pulsePath.setAttribute('stroke', color);

  pulsePhase += 0.12 + risk * 0.15;
  requestAnimationFrame(drawPulse);
}

// --- Init ---
loadAccount();
updateTrustScore();
requestAnimationFrame(drawPulse);
setInterval(updateTrustScore, 4000);
setInterval(updateSignalReadout, 1000);
