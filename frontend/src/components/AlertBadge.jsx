import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, Eye } from 'lucide-react';

export const AlertBadge = ({ status, severity }) => {
  if (status) {
    const statusStyles = {
      Active: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      Acknowledged: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      Resolved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    }[status] || 'bg-slate-800 text-slate-300 border-slate-700';

    const Icon = {
      Active: AlertTriangle,
      Acknowledged: Eye,
      Resolved: CheckCircle2,
    }[status] || AlertCircle;

    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${statusStyles}`}>
        <Icon className="w-3 h-3" />
        {status}
      </span>
    );
  }

  if (severity) {
    const sevStyles = {
      High: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
      Medium: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      Low: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    }[severity] || 'bg-slate-800 text-slate-300 border-slate-700';

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${sevStyles}`}>
        {severity}
      </span>
    );
  }

  return null;
};

export default AlertBadge;
