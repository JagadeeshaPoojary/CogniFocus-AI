import React, { useState } from 'react';
import { KeyRound, CheckCircle2, AlertCircle, Play } from 'lucide-react';
import { monitorAPI } from '../services/api';

export const ClassroomCodeModal = ({ isOpen, onSuccess, onClose }) => {
  const [code, setCode] = useState('CSE301-8291');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verified, setVerified] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await monitorAPI.verifyCode(code);
      if (res.data.success) {
        setVerified(true);
        setTimeout(() => {
          setVerified(false);
          onSuccess(res.data.classroom);
        }, 1200);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Invalid classroom code. Please contact the administrator.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-brand-500/20 text-brand-500 rounded-xl border border-brand-500/30">
            <KeyRound className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-100">Enter Classroom Access Code</h3>
            <p className="text-xs text-slate-400">Verify access code to initialize camera monitoring session.</p>
          </div>
        </div>

        {verified ? (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 my-6 text-center space-y-2 text-emerald-400">
            <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-400 animate-bounce" />
            <p className="font-bold text-sm">Classroom Verified ✓</p>
            <p className="text-xs text-emerald-300/80">Camera Connected ✓ &bull; Monitoring Starting...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            {error && (
              <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs p-3 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Classroom Code
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. CSE301-8291"
                className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl px-4 py-3 text-sm font-mono text-slate-100 uppercase tracking-widest focus:outline-none transition"
                required
              />
              <p className="text-[11px] text-slate-500 mt-1">Default Demo Code: <code className="text-slate-300">CSE301-8291</code></p>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-600/30 flex items-center gap-2 transition disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                {loading ? 'Verifying...' : 'Start Monitoring'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ClassroomCodeModal;
