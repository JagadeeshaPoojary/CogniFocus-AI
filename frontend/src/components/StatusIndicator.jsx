import React from 'react';
import { Activity, CameraOff, Clock } from 'lucide-react';

export const StatusIndicator = ({ active, lastUpdated, fps }) => {
  return (
    <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-medium">
      {active ? (
        <span className="flex items-center gap-1.5 text-emerald-400">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          AI Monitoring Active {fps ? `(${fps} FPS)` : ''}
        </span>
      ) : (
        <span className="flex items-center gap-1.5 text-rose-400">
          <CameraOff className="w-3.5 h-3.5" />
          Camera Offline / Idle
        </span>
      )}
      
      {lastUpdated && (
        <span className="flex items-center gap-1 text-slate-400 border-l border-slate-800 pl-3">
          <Clock className="w-3 h-3 text-slate-500" />
          Updated: {lastUpdated}
        </span>
      )}
    </div>
  );
};

export default StatusIndicator;
