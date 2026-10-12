import React from 'react';
import { X, ShieldAlert, User, Camera, Clock, Activity, AlertTriangle } from 'lucide-react';
import AlertBadge from './AlertBadge';

export const StudentDetailModal = ({ seat, onClose }) => {
  if (!seat) return null;

  const isAlert = seat.status === 'alert' || seat.status === 'suspicious';
  const isMonitoring = seat.status === 'monitoring';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 bg-slate-800/60 p-2 rounded-xl"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className={`p-3 rounded-xl ${isAlert ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'}`}>
            {isAlert ? <AlertTriangle className="w-6 h-6" /> : <User className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-100">Student Monitoring Details</h3>
            <p className="text-xs text-slate-400">Seat {seat.label || seat.id} &bull; {seat.student_id || `STU-${seat.id}`}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block mb-1">Current Status</span>
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${isAlert ? 'bg-rose-500 animate-ping' : isMonitoring ? 'bg-amber-400' : 'bg-emerald-400'}`} />
              <span className="text-sm font-semibold text-slate-200 capitalize">
                {isAlert ? 'Possible Mobile Usage' : isMonitoring ? 'Monitoring' : 'Normal'}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block mb-1">Usage Duration</span>
            <div className="flex items-center gap-1.5 text-sm font-bold text-slate-100">
              <Clock className="w-4 h-4 text-slate-400" />
              {seat.duration || 0} seconds
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block mb-1">Detection Confidence</span>
            <div className="flex items-center gap-1.5 text-sm font-bold text-emerald-400">
              <Activity className="w-4 h-4 text-emerald-500" />
              {Math.round((seat.confidence || 0.87) * 100)}%
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block mb-1">Camera ID</span>
            <div className="flex items-center gap-1.5 text-sm font-bold text-slate-100">
              <Camera className="w-4 h-4 text-slate-400" />
              CAM001
            </div>
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 mb-6 text-xs space-y-2 text-slate-300">
          <div className="flex justify-between">
            <span className="text-slate-500">First Detected:</span>
            <span className="font-mono">Today 19:31:42</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Last Active Scan:</span>
            <span className="font-mono">Just Now</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Classroom:</span>
            <span className="font-semibold text-slate-200">CSE-301</span>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default StudentDetailModal;
