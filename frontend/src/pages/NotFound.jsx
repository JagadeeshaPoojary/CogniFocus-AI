import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, Home } from 'lucide-react';

export const NotFound = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
      <div className="p-4 bg-rose-500/10 text-rose-400 rounded-2xl border border-rose-500/20">
        <AlertCircle className="w-12 h-12" />
      </div>
      <h1 className="text-3xl font-extrabold text-slate-100">404 - Page Not Found</h1>
      <p className="text-sm text-slate-400 max-w-sm">
        The requested monitoring view or application page does not exist.
      </p>
      <Link
        to="/dashboard"
        className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-brand-600/30 inline-flex items-center gap-2 transition"
      >
        <Home className="w-4 h-4" />
        Return to Dashboard
      </Link>
    </div>
  );
};

export default NotFound;
