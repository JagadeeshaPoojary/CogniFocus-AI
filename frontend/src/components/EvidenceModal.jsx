import React, { useState, useEffect } from 'react';
import { X, ShieldAlert, Camera, User, Clock, Activity, AlertTriangle } from 'lucide-react';
import { notificationsAPI } from '../services/api';

export const EvidenceModal = ({ alert, onClose }) => {
  const [imgError, setImgError] = useState(false);
  const [notifLogs, setNotifLogs] = useState({ email: 'QUEUED', sms: 'QUEUED', emailErr: null, smsErr: null });

  useEffect(() => {
    setImgError(false);
    if (!alert || !alert.id) return;

    setNotifLogs({ email: 'QUEUED', sms: 'QUEUED', emailErr: null, smsErr: null });
    notificationsAPI.getLogs(alert.id)
      .then((res) => {
        if (res.data && res.data.logs) {
          const logs = res.data.logs;
          const emailLog = logs.find(l => String(l.channel).toUpperCase() === 'EMAIL');
          const smsLog = logs.find(l => String(l.channel).toUpperCase() === 'SMS');
          setNotifLogs({
            email: emailLog ? emailLog.status : 'QUEUED',
            sms: smsLog ? smsLog.status : 'QUEUED',
            emailErr: emailLog ? emailLog.error_message : null,
            smsErr: smsLog ? smsLog.error_message : null,
          });
        }
      })
      .catch((err) => {
        console.warn('Failed to fetch notification logs for alert', alert.id, err);
      });
  }, [alert]);

  if (!alert) return null;

  const defaultProtocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
  const defaultHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
  const API_URL = import.meta.env.VITE_API_URL || `${defaultProtocol}//${defaultHost}:5000`;

  let evidenceUrl = null;
  if (alert.evidence_image) {
    if (alert.evidence_image.startsWith('http://') || alert.evidence_image.startsWith('https://')) {
      evidenceUrl = alert.evidence_image;
    } else {
      evidenceUrl = `${API_URL}${alert.evidence_image.startsWith('/') ? '' : '/'}${alert.evidence_image}`;
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 bg-slate-800/80 p-2 rounded-xl"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-rose-500/20 text-rose-400 rounded-xl border border-rose-500/30">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-100">Mobile Usage Evidence Image</h3>
            <p className="text-xs text-slate-400">Cropped Student Detection Capture &bull; {alert.seat_id || alert.seat}</p>
          </div>
        </div>

        {/* Evidence Image Container */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden mb-6 relative aspect-video flex items-center justify-center">
          {evidenceUrl && !imgError ? (
            <img
              src={evidenceUrl}
              alt="Student Mobile Usage Evidence"
              onError={() => setImgError(true)}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="text-center p-6 space-y-2 text-rose-400">
              <AlertTriangle className="w-8 h-8 mx-auto text-rose-400" />
              <p className="text-xs font-bold">⚠ Evidence Unavailable</p>
              <p className="text-[11px] text-slate-500">Evidence not available for this historical alert.</p>
            </div>
          )}
        </div>

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4 text-xs">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Student ID</span>
            <span className="font-mono font-bold text-slate-100">{alert.student_id}</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Seat Location</span>
            <span className="font-bold text-slate-100">Seat {alert.seat_id || alert.seat}</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Camera ID</span>
            <span className="font-mono font-bold text-brand-400">{alert.camera_id || 'CAM001'}</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Usage Duration</span>
            <span className="font-bold text-rose-400">{alert.duration} seconds</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Detection Confidence</span>
            <span className="font-bold text-emerald-400">{Math.round((alert.confidence || 0.87) * 100)}%</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Detected Time</span>
            <span className="font-mono text-slate-300 text-[11px]">
              {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'Just Now'}
            </span>
          </div>
        </div>

        {/* Real-time Notification Status Badges */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 mb-6 text-xs flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="text-slate-400 font-bold uppercase text-[10px]">Real-Time Notifications:</span>
          <div className="flex flex-wrap items-center gap-2">
            {notifLogs.email === 'SENT' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                ✓ Email Delivered
              </span>
            ) : notifLogs.email === 'FAILED' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1" title={notifLogs.emailErr}>
                ❌ Email Failed
              </span>
            ) : notifLogs.email === 'NOT CONFIGURED' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                ⚠️ Email Not Configured
              </span>
            ) : notifLogs.email === 'SKIPPED' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                ⏸ Email Skipped
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1">
                ⏳ Email Dispatch Queued
              </span>
            )}

            {notifLogs.sms === 'SENT' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                ✓ SMS Delivered
              </span>
            ) : notifLogs.sms === 'FAILED' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1" title={notifLogs.smsErr}>
                ❌ SMS Failed
              </span>
            ) : notifLogs.sms === 'NOT CONFIGURED' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                ⚠️ SMS Not Configured
              </span>
            ) : notifLogs.sms === 'SKIPPED' ? (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                ⏸ SMS Skipped
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1">
                ⏳ SMS Dispatch Queued
              </span>
            )}
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
};

export default EvidenceModal;
