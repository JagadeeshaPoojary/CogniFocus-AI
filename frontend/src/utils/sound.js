// Web Audio API Sound Utility for CogniFocus-AI Alerts

const notifiedAlertIds = new Set();

export const playAlertSound = (freq = 880, duration = 0.4) => {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + duration);

    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (err) {
    console.warn('[Audio Alert Playback Failed]', err);
  }
};

/**
 * Seed existing historical alert IDs so initial page load does NOT play sounds for historical alerts.
 */
export const seedNotifiedAlerts = (alertList = []) => {
  if (!Array.isArray(alertList)) return;
  for (const a of alertList) {
    const id = a?.id || a?.alert_id;
    if (id !== undefined && id !== null) {
      notifiedAlertIds.add(id);
    }
  }
};

/**
 * Centralized alert sound notification function.
 * ONLY plays sound if alert is a REAL alert saved in DB with a unique ID that has NOT already been notified.
 */
export const playAlertNotification = (alert, freq = 880, duration = 0.4) => {
  if (!alert) return false;
  const alertId = alert.id || alert.alert_id;
  if (alertId === undefined || alertId === null) return false;

  if (notifiedAlertIds.has(alertId)) {
    return false;
  }

  notifiedAlertIds.add(alertId);
  playAlertSound(freq, duration);
  console.log(`[ALERT NOTIFICATION SOUND] Played sound once for new Alert #${alertId}: ${alert.alert_type || 'Behavior Alert'}`);
  return true;
};

