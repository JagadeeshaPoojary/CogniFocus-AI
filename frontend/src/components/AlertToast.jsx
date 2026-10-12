import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { playAlertNotification } from '../utils/sound';
import { teacherAPI } from '../services/api';

const defaultProtocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
const defaultHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
const API_URL = import.meta.env.VITE_API_URL || `${defaultProtocol}//${defaultHost}:5000`;


function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const AlertToast = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentAlert, setCurrentAlert] = useState(null);

  // STRICT RULE: ADMIN MUST NOT RECEIVE TEACHER CLASSROOM NOTIFICATIONS
  const isTeacher = user && String(user.role).toUpperCase() === 'TEACHER';

  const notifyTeacher = (alertObj) => {
    const isSupported = typeof window !== 'undefined' && 'Notification' in window;
    const isSecure = typeof window !== 'undefined' && window.isSecureContext;
    const perm = isSupported ? Notification.permission : 'unsupported';
    const alertId = alertObj.id || alertObj.alert_id || Date.now();

    console.log('[NOTIFICATION DIAGNOSTIC LOG]', {
      alert_received_sse: alertObj,
      notification_api_supported: isSupported,
      notification_permission: perm,
      secure_context_status: isSecure,
      visibility_state: typeof document !== 'undefined' ? document.visibilityState : 'unknown'
    });

    if (!isSupported) {
      console.error('[Notification Error] Notification API unsupported in this browser environment.');
      return;
    }

    if (perm !== 'granted') {
      console.error('System notification unavailable:', perm);
      return;
    }

    const classroomCode = alertObj.classroom_code || alertObj.classroom_id || alertObj.classroom || 'CSE301';
    const seatId = alertObj.seat_id || alertObj.seat || 'N/A';
    const studentId = alertObj.student_id || alertObj.student || 'N/A';
    const durationSec = alertObj.duration != null ? alertObj.duration : 10;

    const title = "🚨 CogniFocus-AI Alert";
    const bodyText = `Classroom: ${classroomCode}\nSeat: ${seatId}\nStudent: ${studentId}\nDuration: ${durationSec}s`;

    try {
      const notification = new Notification(title, {
        body: bodyText,
        icon: "/favicon.ico",
        tag: `cognifocus-alert-${alertId}`,
        requireInteraction: true
      });

      notification.onclick = () => {
        try {
          window.focus();
        } catch (fErr) {
          console.warn('[Window Focus Warning]', fErr);
        }
        notification.close();
        navigate('/alerts');
      };
      console.log(`[Notification Success] System notification created for Alert #${alertId}`);
    } catch (nErr) {
      console.error('[Notification Exception] Direct Notification failed, attempting SW fallback:', nErr);
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then((reg) => {
          if (reg && reg.showNotification) {
            reg.showNotification(title, {
              body: bodyText,
              icon: "/favicon.ico",
              badge: "/favicon.ico",
              tag: `cognifocus-alert-${alertId}`,
              requireInteraction: true,
              data: alertObj
            }).then(() => {
              console.log(`[Notification Success] SW system notification created for Alert #${alertId}`);
            }).catch(swErr => {
              console.error('[Notification Exception] Service Worker showNotification failed:', swErr);
            });
          }
        }).catch(swErr => {
          console.error('[Notification Exception] SW ready failed:', swErr);
        });
      }
    }
  };

  useEffect(() => {
    if (!isTeacher) return;

    const token = localStorage.getItem('cognifocus_token');
    if (!token) return;

    // 1. Establish SSE Connection for Teacher
    const sseUrl = `${API_URL}/api/teacher/notifications/stream?token=${encodeURIComponent(token)}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        if (!event.data) return;
        const payload = JSON.parse(event.data);

        if (payload.type === 'NEW_ALERT' && payload.alert) {
          const alertObj = payload.alert;
          console.log('[Alert received through SSE]', alertObj);

          // Play sound and check duplicate alert ID protection
          const isNew = playAlertNotification(alertObj);
          if (!isNew) {
            console.log('[AlertToast] Already notified alert ID:', alertObj.id || alertObj.alert_id);
            return;
          }

          // Always set current alert for in-app toast popup
          setCurrentAlert(alertObj);

          // Display system notification using browser Notification API if permission is granted
          notifyTeacher(alertObj);
        }
      } catch (err) {
        console.error('[AlertToast Error] Error parsing SSE payload:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('[AlertToast] SSE Connection error/retry:', err);
    };

    // 2. Register Web Push Service Worker for background system notifications
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      navigator.serviceWorker.register('/sw.js')
        .then(async (registration) => {
          console.log('[AlertToast] Service worker registered:', registration.scope);

          // Listen to SW open alert messages
          navigator.serviceWorker.onmessage = (e) => {
            if (e.data && e.data.type === 'OPEN_ALERT') {
              if (e.data.alert) setCurrentAlert(e.data.alert);
              navigate('/alerts');
            }
          };

          // Try registering push subscription if permission granted
          if (Notification.permission === 'granted') {
            try {
              const res = await teacherAPI.getVapidPublicKey();
              if (res.data && res.data.publicKey) {
                const applicationServerKey = urlBase64ToUint8Array(res.data.publicKey);
                let subscription = await registration.pushManager.getSubscription();
                if (!subscription) {
                  subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey
                  });
                }
                await teacherAPI.subscribePush(subscription.toJSON());
                console.log('[AlertToast] Web Push subscription synced with backend.');
              }
            } catch (pErr) {
              console.warn('[AlertToast] Push subscription sync warning:', pErr);
            }
          }
        })
        .catch((swErr) => {
          console.warn('[AlertToast] SW registration failed:', swErr);
        });
    }

    return () => {
      eventSource.close();
    };
  }, [isTeacher, navigate]);

  if (!isTeacher || !currentAlert) return null;

  const handleViewAlert = () => {
    setCurrentAlert(null);
    navigate('/alerts');
  };

  const handleClose = () => {
    setCurrentAlert(null);
  };

  const classroomLabel = currentAlert.classroom_id || currentAlert.classroom_code || 'Classroom';
  const studentLabel = currentAlert.student_id || 'N/A';
  const seatLabel = currentAlert.seat_id || currentAlert.seat || 'N/A';
  const alertType = currentAlert.alert_type || 'Cell Phone Detected Near Body';

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-md w-full bg-slate-900 border-2 border-red-500/80 rounded-xl shadow-2xl p-4 text-slate-100 animate-bounce-short transition-all">
      <div className="flex items-start justify-between space-x-3">
        <div className="flex items-center space-x-2">
          <span className="relative flex h-3.5 w-3.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-red-500"></span>
          </span>
          <h4 className="font-bold text-red-400 text-sm tracking-wide uppercase">
            🚨 Alert: {classroomLabel}
          </h4>
        </div>
        <button
          onClick={handleClose}
          className="text-slate-400 hover:text-slate-200 text-lg leading-none p-1 focus:outline-none"
          title="Close Toast"
        >
          &times;
        </button>
      </div>

      <div className="mt-2.5 text-xs text-slate-300 space-y-1">
        <p><strong className="text-slate-100">Issue:</strong> {alertType}</p>
        <p><strong className="text-slate-100">Student:</strong> {studentLabel} &bull; <strong className="text-slate-100">Seat:</strong> {seatLabel}</p>
        {currentAlert.timestamp && (
          <p className="text-slate-400 text-[11px]">
            {new Date(currentAlert.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="mt-3.5 flex items-center justify-end space-x-2">
        <button
          onClick={handleClose}
          className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          Dismiss
        </button>
        <button
          onClick={handleViewAlert}
          className="px-4 py-1.5 text-xs font-semibold bg-red-600 hover:bg-red-500 text-white rounded-lg shadow-md transition"
        >
          VIEW ALERT
        </button>
      </div>
    </div>
  );
};

export default AlertToast;
