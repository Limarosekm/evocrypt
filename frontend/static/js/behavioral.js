// Lightweight behavioral biometrics: watches typing cadence and pointer
// motion in the browser, then periodically reports a small trust-score
// adjustment to the backend. This is a simplified simulation of continuous
// authentication, not a production-grade model.

window.EvoBehavior = {
  keystrokeLabel: 'nominal',
  pointerLabel: 'nominal'
};

(function () {
  let lastKeyTime = null;
  const keyIntervals = [];

  let lastMouse = null;
  const mouseSpeeds = [];

  document.addEventListener('keydown', () => {
    const now = performance.now();
    if (lastKeyTime !== null) {
      keyIntervals.push(now - lastKeyTime);
      if (keyIntervals.length > 20) keyIntervals.shift();
    }
    lastKeyTime = now;
  });

  document.addEventListener('mousemove', (e) => {
    const now = performance.now();
    if (lastMouse) {
      const dt = now - lastMouse.t || 1;
      const dist = Math.hypot(e.clientX - lastMouse.x, e.clientY - lastMouse.y);
      mouseSpeeds.push(dist / dt);
      if (mouseSpeeds.length > 30) mouseSpeeds.shift();
    }
    lastMouse = { x: e.clientX, y: e.clientY, t: now };
  });

  function variance(arr) {
    if (arr.length < 3) return 0;
    const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
    return arr.reduce((sum, v) => sum + (v - mean) ** 2, 0) / arr.length;
  }

  function classifySignals() {
    const keyVar = variance(keyIntervals);
    const mouseVar = variance(mouseSpeeds);

    // Very high variance in typing rhythm or pointer speed reads as
    // "irregular" - closer to bot-like or unfamiliar-user behavior.
    const keystrokeLabel = keyVar > 45000 ? 'irregular' : keyIntervals.length ? 'nominal' : 'idle';
    const pointerLabel = mouseVar > 8 ? 'irregular' : mouseSpeeds.length ? 'nominal' : 'idle';

    window.EvoBehavior.keystrokeLabel = keystrokeLabel;
    window.EvoBehavior.pointerLabel = pointerLabel;

    let change = 0;
    if (keystrokeLabel === 'irregular') change -= 4;
    if (pointerLabel === 'irregular') change -= 4;
    if (keystrokeLabel === 'nominal' && pointerLabel === 'nominal') change += 1;

    return change;
  }

  async function reportBehavior() {
    const change = classifySignals();
    try {
      await fetch('/api/update-behavior', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ change })
      });
    } catch (e) {
      // Session likely ended - silently skip.
    }
    if (typeof window.onTrustScoreChanged === 'function') {
      window.onTrustScoreChanged();
    }
  }

  setInterval(reportBehavior, 6000);
})();
