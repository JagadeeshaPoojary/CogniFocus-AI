import React, { useState } from 'react';
import { KeyRound, Video, RefreshCw, ShieldAlert, Square, AlertTriangle, X } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const ClassroomAccessCard = ({ onClassroomChange }) => {
  const { teacherClassroom, isTeacherMonitoringActive, enterTeacherClassroom, stopTeacherMonitoring } = useAuth();
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const [stopping, setStopping] = useState(false);

  const [notifPermission, setNotifPermission] = useState(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      return Notification.permission;
    }
    return 'default';
  });
  const [notifStatusMsg, setNotifStatusMsg] = useState('');

  React.useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setNotifPermission(Notification.permission);
      if (typeof navigator !== 'undefined' && navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({ name: 'notifications' }).then((status) => {
          status.onchange = () => {
            if (typeof window !== 'undefined' && 'Notification' in window) {
              setNotifPermission(Notification.permission);
            }
          };
        }).catch(() => {});
      }
    }
  }, []);

  const handleEnableNotifications = () => {
    const isSupported = typeof window !== 'undefined' && 'Notification' in window;
    const isSecure = typeof window !== 'undefined' && window.isSecureContext;
    const initialPerm = isSupported ? Notification.permission : 'unsupported';
    const origin = typeof window !== 'undefined' ? window.location.origin : 'unknown';

    console.log('[ENABLE NOTIFICATIONS CLICKED]', {
      notification_api_supported: isSupported,
      origin: origin,
      secure_context: isSecure,
      notification_permission_before: initialPerm
    });

    if (!isSupported) {
      setNotifStatusMsg('Browser does not support desktop notifications.');
      console.error('[Notification Error] Notification API unsupported in this environment.');
      return;
    }

    if (!isSecure) {
      const msg = `⚠️ Notification API blocked: Origin '${origin}' is insecure (isSecureContext=false). Access https://${window.location.hostname}:5173 or http://localhost:5173 to enable notifications.`;
      setNotifStatusMsg(msg);
      console.warn('[Notification Warning] Insecure HTTP origin prevents notification permission prompt.');
      return;
    }

    if (initialPerm === 'denied') {
      setNotifStatusMsg('⚠️ Permission is blocked in browser settings. To enable: Click lock/tune icon near URL bar -> Site settings -> Notifications -> Allow, then reload the page.');
      console.warn('[Notification Warning] Notification permission is already denied in browser settings.');
      return;
    }

    setNotifStatusMsg('Requesting notification permission...');

    const processPermissionResult = (perm) => {
      console.log('[Permission Request Result]', {
        permission_result: perm,
        secure_context: window.isSecureContext,
        origin: window.location.origin
      });

      setNotifPermission(perm);
      if (perm === 'granted') {
        setNotifStatusMsg('✓ Notifications enabled for real-time teacher alerts.');
      } else if (perm === 'denied') {
        setNotifStatusMsg('⚠️ Notification permission denied in browser. Click lock icon near URL bar -> Site settings -> Notifications -> Allow.');
      } else {
        setNotifStatusMsg('Notification permission request dismissed.');
      }
    };

    try {
      // Call requestPermission directly inside click handler synchronously
      const promise = Notification.requestPermission((perm) => {
        processPermissionResult(perm);
      });

      if (promise && typeof promise.then === 'function') {
        promise.then((perm) => {
          processPermissionResult(perm);
        }).catch((err) => {
          console.error('[Notification Permission Exception]', err);
          setNotifStatusMsg(`Error: ${err.message || 'Permission request failed'}`);
        });
      }
    } catch (err) {
      console.error('[Notification Permission Exception]', err);
      setNotifStatusMsg(`Error: ${err.message || 'Permission request failed'}`);
    }
  };

  const handleTestNotification = () => {
    const isSupported = typeof window !== 'undefined' && 'Notification' in window;
    const isSecure = typeof window !== 'undefined' && window.isSecureContext;
    const perm = isSupported ? Notification.permission : 'unsupported';
    const origin = typeof window !== 'undefined' ? window.location.origin : 'unknown';

    console.log('[TEST NOTIFICATION CLICKED]', {
      notification_api_supported: isSupported,
      origin: origin,
      secure_context: isSecure,
      notification_permission: perm
    });

    if (!isSupported) {
      setNotifStatusMsg('Browser does not support desktop notifications.');
      console.error('[Test Notification Error] Notification API unsupported.');
      return;
    }
    if (!isSecure) {
      setNotifStatusMsg(`⚠️ Notifications require a secure context. Open https://${window.location.hostname}:5173 or http://localhost:5173.`);
      console.warn('[Test Notification Warning] Insecure context prevents system notifications.');
      return;
    }
    if (perm !== 'granted') {
      setNotifStatusMsg(`⚠️ Notification permission is '${perm}'. Grant permission first.`);
      console.warn(`[Test Notification Warning] Permission is '${perm}'.`);
      return;
    }

    try {
      const notif = new Notification("CogniFocus-AI Test", {
        body: "System notifications are working.",
        icon: "/favicon.ico",
        requireInteraction: true
      });
      notif.onclick = () => {
        try { window.focus(); } catch (e) {}
        notif.close();
      };
      console.log('[Test Notification Success] Real system notification created: CogniFocus-AI Test');
      setNotifStatusMsg('✓ System popup displayed: CogniFocus-AI Test');
    } catch (err) {
      console.error('[Test Notification Exception] Direct Notification failed, attempting SW fallback:', err);
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then((reg) => {
          if (reg && reg.showNotification) {
            reg.showNotification("CogniFocus-AI Test", {
              body: "System notifications are working.",
              icon: '/favicon.ico',
              badge: '/favicon.ico',
              requireInteraction: true
            }).then(() => {
              console.log('[Test Notification Success] SW notification created: CogniFocus-AI Test');
              setNotifStatusMsg('✓ Sent test notification to OS desktop via Service Worker!');
            }).catch((swErr) => {
              console.error('[Test Notification Exception] SW showNotification failed:', swErr);
              setNotifStatusMsg(`Error: ${swErr.message}`);
            });
          }
        }).catch((swErr) => {
          console.error('[Test Notification Exception] SW ready failed:', swErr);
          setNotifStatusMsg(`Error: ${err.message}`);
        });
      } else {
        setNotifStatusMsg(`Error sending notification: ${err.message}`);
      }
    }
  };


  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!code.trim()) {
      setError('❌ Invalid classroom code');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await enterTeacherClassroom(code.trim());
      setCode('');
      if (onClassroomChange) onClassroomChange();
    } catch (err) {
      setError(err.message || '❌ Invalid classroom code');
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmStop = async () => {
    setStopping(true);
    try {
      await stopTeacherMonitoring();
      setShowStopConfirm(false);
      if (onClassroomChange) onClassroomChange();
    } catch (err) {
      console.error("[Stop Monitoring Error]", err);
    } finally {
      setStopping(false);
    }
  };

  // State: MONITORING ACTIVE (Requirements 2 & 3)
  if (isTeacherMonitoringActive && teacherClassroom) {
    const cameras = teacherClassroom.cameras || (teacherClassroom.id === 'CSE-302' ? ['CAM003', 'CAM004'] : ['CAM001', 'CAM002']);
    return (
      <>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
                <Video className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-100 uppercase tracking-wide">CURRENT CLASSROOM</h3>
                <p className="text-xs text-slate-400">Classroom: <span className="text-slate-200 font-mono font-bold">{teacherClassroom.name || teacherClassroom.id}</span></p>
              </div>
            </div>
            <button
              onClick={() => setShowStopConfirm(true)}
              className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-rose-600/30 flex items-center justify-center gap-2 transition cursor-pointer uppercase tracking-wider"
            >
              <Square className="w-4 h-4 fill-white" />
              <span>STOP MONITORING</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-2 text-xs">
            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
              <div className="text-slate-400 font-semibold uppercase text-[10px]">Classroom Code</div>
              <div className="text-slate-100 font-mono font-bold text-base text-brand-400">{teacherClassroom.code}</div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
              <div className="text-slate-400 font-semibold uppercase text-[10px]">Status</div>
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                ● AI Monitoring Active
              </div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
              <div className="text-slate-400 font-semibold uppercase text-[10px]">Cameras Monitoring</div>
              <div className="text-slate-100 font-mono font-bold text-sm">{cameras.length} ({cameras.join(', ')})</div>
            </div>
          </div>

          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 text-xs font-semibold text-center">
            Monitoring is running in the background.
          </div>

          {('Notification' in window) && (
            <div className={`p-3 rounded-xl text-xs flex flex-col sm:flex-row items-center justify-between gap-3 border ${
              notifPermission === 'granted'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : notifPermission === 'denied'
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            }`}>
              <div className="flex flex-col">
                <span className="font-semibold">
                  {notifPermission === 'granted'
                    ? '✓ Notifications Enabled: Real-time alerts will pop up while using PowerPoint or other tabs.'
                    : notifPermission === 'denied'
                    ? '⚠️ Notifications Blocked in Browser Settings.'
                    : 'Enable notifications to receive classroom alerts while using other tabs.'}
                </span>
                {notifStatusMsg && <span className="text-[11px] opacity-80 mt-0.5">{notifStatusMsg}</span>}
              </div>
              {notifPermission !== 'granted' ? (
                <button
                  type="button"
                  onClick={handleEnableNotifications}
                  className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-lg shadow transition whitespace-nowrap cursor-pointer shrink-0"
                >
                  Enable Notifications
                </button>
              ) : (
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={handleTestNotification}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-lg border border-slate-700 shadow-sm transition cursor-pointer whitespace-nowrap"
                  >
                    🔔 Test Notification
                  </button>
                  <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 font-bold text-xs rounded-lg border border-emerald-500/30 whitespace-nowrap">
                    ✓ Notifications Enabled
                  </span>
                </div>
              )}

            </div>
          )}
        </div>

        {/* STOP MONITORING CONFIRMATION MODAL (Requirement 6) */}
        {showStopConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fade-in">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 relative">
              <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
                <div className="p-3 bg-rose-500/20 text-rose-400 rounded-xl border border-rose-500/30">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-100">Stop Classroom Monitoring?</h3>
                  <p className="text-xs text-slate-400">Confirm monitoring session shutdown.</p>
                </div>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                <p><strong className="text-slate-300">Classroom:</strong> <span className="font-mono text-brand-400 font-bold">{teacherClassroom.name || teacherClassroom.id} ({teacherClassroom.code})</span></p>
                <p><strong className="text-slate-300">Cameras:</strong> <span className="font-mono text-slate-200">{cameras.join(', ')}</span></p>
                <p className="text-slate-400 pt-2 border-t border-slate-800/80">
                  Monitoring will stop in the background. No new alerts will be generated by this monitoring session after it stops. Existing historical alerts remain safe.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowStopConfirm(false)}
                  disabled={stopping}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded-xl border border-slate-700 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmStop}
                  disabled={stopping}
                  className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-rose-600/30 flex items-center gap-2 transition cursor-pointer"
                >
                  {stopping ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Stopping...</span>
                    </>
                  ) : (
                    <span>Stop Monitoring</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // State: MONITORING INACTIVE / STOPPED (Requirements 7, 32, 33)
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl border border-brand-500/30">
            <KeyRound className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100 uppercase tracking-wide">
              {teacherClassroom ? 'CURRENT MONITORING' : 'START CLASSROOM MONITORING'}
            </h3>
            <p className="text-xs text-slate-400">
              {teacherClassroom ? `Classroom: ${teacherClassroom.id} • Status: Monitoring Stopped` : 'Enter Classroom Code to start backend AI monitoring.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-rose-400 font-bold text-xs bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
          <span className="w-2 h-2 rounded-full bg-rose-500" />
          <span>● Monitoring Inactive</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Enter Classroom Code
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="CSE301"
              className="flex-1 bg-slate-950 border border-slate-800 focus:border-brand-500 text-slate-100 text-sm font-mono font-bold px-4 py-3 rounded-xl focus:outline-none transition uppercase tracking-wider placeholder:text-slate-600"
              autoFocus
            />
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-600/30 transition flex items-center justify-center gap-2 cursor-pointer uppercase tracking-wider whitespace-nowrap"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Validating...</span>
                </>
              ) : (
                <span>{teacherClassroom ? 'ENTER CLASSROOM CODE' : 'START MONITORING'}</span>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-bold flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {('Notification' in window) && (
          <div className={`p-3 rounded-xl text-xs flex flex-col sm:flex-row items-center justify-between gap-3 border ${
            notifPermission === 'granted'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : notifPermission === 'denied'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            <div className="flex flex-col">
              <span className="font-semibold">
                {notifPermission === 'granted'
                  ? '✓ Notifications Enabled: Real-time alerts will pop up while using PowerPoint or other tabs.'
                  : notifPermission === 'denied'
                  ? '⚠️ Notifications Blocked in Browser Settings.'
                  : 'Enable notifications to receive classroom alerts while using other tabs.'}
              </span>
              {notifStatusMsg && <span className="text-[11px] opacity-80 mt-0.5">{notifStatusMsg}</span>}
            </div>
            {notifPermission !== 'granted' ? (
              <button
                type="button"
                onClick={handleEnableNotifications}
                className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-lg shadow transition whitespace-nowrap cursor-pointer shrink-0"
              >
                Enable Notifications
              </button>
            ) : (
              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={handleTestNotification}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-lg border border-slate-700 shadow-sm transition cursor-pointer whitespace-nowrap"
                >
                  🔔 Test Notification
                </button>
                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 font-bold text-xs rounded-lg border border-emerald-500/30 whitespace-nowrap">
                  ✓ Notifications Enabled
                </span>
              </div>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
          <span className="text-slate-400">Historical alerts remain accessible in alert history.</span>
          <div className="text-[11px] text-slate-500 font-mono">
            Valid Codes: <strong className="text-slate-300">CSE301</strong> (CSE-301) &bull; <strong className="text-slate-300">CSE302</strong> (CSE-302)
          </div>
        </div>
      </form>
    </div>
  );
};

export default ClassroomAccessCard;
