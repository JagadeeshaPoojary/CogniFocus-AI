import React, { useEffect, useState } from 'react';
import { Sliders, Save, CheckCircle2, AlertCircle, RefreshCw, Cpu, Mail, Phone, Send, Bell } from 'lucide-react';
import { configAPI, notificationsAPI } from '../services/api';

export const ConfigurationPage = () => {
  const [config, setConfig] = useState({
    camera_id: 'CAM001',
    camera_source: '0',
    confidence: 0.5,
    alert_time: 10,
    alert_cooldown: 30,
    dashboard_width: 400,
    beep_frequency: 1000,
    beep_duration: 500,
    model_type: 'yolov8n-pose.pt',
    simulation_mode: false,
  });

  const [prefs, setPrefs] = useState({
    notification_email: 'teacher@classroom.com',
    notification_phone: '+919876543210',
    email_notifications_enabled: true,
    sms_notifications_enabled: true,
    email_configured: false,
    sms_configured: false
  });

  const [saving, setSaving] = useState(false);
  const [testEmailSending, setTestEmailSending] = useState(false);
  const [testSmsSending, setTestSmsSending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchConfig = async () => {
    try {
      const [cRes, nRes] = await Promise.all([
        configAPI.getConfig(),
        notificationsAPI.getPreferences()
      ]);
      if (cRes.data?.success) setConfig(cRes.data.data);
      if (nRes.data?.success) setPrefs(nRes.data.preferences);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    setError('');

    try {
      const [cRes, nRes] = await Promise.all([
        configAPI.updateConfig(config),
        notificationsAPI.updatePreferences(prefs)
      ]);
      if (cRes.data?.success && nRes.data?.success) {
        setMessage('System configuration and notification preferences saved successfully!');
        setTimeout(() => setMessage(''), 4000);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    setTestEmailSending(true);
    setMessage('');
    setError('');
    try {
      const res = await notificationsAPI.sendTestEmail(prefs.notification_email);
      if (res.data.success) {
        setMessage(res.data.message || 'Test email sent successfully!');
      }
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || 'Email could not be sent.');
    } finally {
      setTestEmailSending(false);
    }
  };

  const handleTestSMS = async () => {
    setTestSmsSending(true);
    setMessage('');
    setError('');
    try {
      const res = await notificationsAPI.sendTestSMS(prefs.notification_phone);
      if (res.data.success) {
        setMessage(res.data.message || 'Test SMS sent successfully!');
      }
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || 'SMS could not be sent.');
    } finally {
      setTestSmsSending(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl border border-brand-500/30">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">System Configuration & Notifications</h3>
            <p className="text-xs text-slate-400">Modify AI thresholds, alert durations, model parameters, and Real-Time Email/SMS settings</p>
          </div>
        </div>

        <button
          onClick={fetchConfig}
          className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition self-start sm:self-auto"
          title="Reload Settings"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        {message && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            {message}
          </div>
        )}

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {/* NOTIFICATION SETTINGS SECTION (Section 22) */}
        <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-5">
          <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-3">
            <Bell className="w-4 h-4 text-brand-400" />
            NOTIFICATION SETTINGS
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Email Notifications */}
            <div className="space-y-3 p-4 bg-slate-900/60 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-200">
                  <input
                    type="checkbox"
                    checked={prefs.email_notifications_enabled}
                    onChange={(e) => setPrefs({ ...prefs, email_notifications_enabled: e.target.checked })}
                    className="rounded border-slate-800 bg-slate-900 text-brand-500 focus:ring-0"
                  />
                  <Mail className="w-4 h-4 text-blue-400" />
                  Enable Email Alerts
                </label>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${prefs.email_configured ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border-amber-500/30'}`}>
                  {prefs.email_configured ? 'SMTP Configured' : 'Local / SMTP Idle'}
                </span>
              </div>

              <div>
                <label className="block font-semibold text-slate-400 mb-1">Email Address</label>
                <input
                  type="email"
                  value={prefs.notification_email}
                  onChange={(e) => setPrefs({ ...prefs, notification_email: e.target.value })}
                  placeholder="teacher@example.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
                />
              </div>

              <button
                type="button"
                onClick={handleTestEmail}
                disabled={testEmailSending || !prefs.notification_email}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 flex items-center justify-center gap-2 transition disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                {testEmailSending ? 'Sending Test Email...' : 'Send Test Email'}
              </button>
            </div>

            {/* SMS Notifications */}
            <div className="space-y-3 p-4 bg-slate-900/60 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-200">
                  <input
                    type="checkbox"
                    checked={prefs.sms_notifications_enabled}
                    onChange={(e) => setPrefs({ ...prefs, sms_notifications_enabled: e.target.checked })}
                    className="rounded border-slate-800 bg-slate-900 text-brand-500 focus:ring-0"
                  />
                  <Phone className="w-4 h-4 text-emerald-400" />
                  Enable SMS Alerts
                </label>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${prefs.sms_configured ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                  {prefs.sms_configured ? 'SMS Provider Ready' : 'Local / SMS Idle'}
                </span>
              </div>

              <div>
                <label className="block font-semibold text-slate-400 mb-1">Mobile Number</label>
                <input
                  type="text"
                  value={prefs.notification_phone}
                  onChange={(e) => setPrefs({ ...prefs, notification_phone: e.target.value })}
                  placeholder="+91XXXXXXXXXX"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
                />
              </div>

              <button
                type="button"
                onClick={handleTestSMS}
                disabled={testSmsSending || !prefs.notification_phone}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 flex items-center justify-center gap-2 transition disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                {testSmsSending ? 'Sending Test SMS...' : 'Send Test SMS'}
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* AI Inference & Model Parameters */}
          <div className="space-y-4 bg-slate-950 p-5 rounded-xl border border-slate-800">
            <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-3">
              <Cpu className="w-4 h-4 text-brand-400" />
              AI & Detection Engine Thresholds
            </h4>

            <div>
              <label className="block font-semibold text-slate-400 mb-1">Inference Model</label>
              <select
                value={config.model_type}
                onChange={(e) => setConfig({ ...config, model_type: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
              >
                <option value="yolov8n-pose.pt">yolov8n-pose.pt (Pose Model - Fast)</option>
                <option value="yolov8m-pose.pt">yolov8m-pose.pt (Pose Model - Medium Accuracy)</option>
                <option value="yolov8n.pt">yolov8n.pt (Standard Object Model)</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-400 mb-1">
                Detection Confidence Threshold: <strong className="text-brand-400">{config.confidence}</strong>
              </label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={config.confidence}
                onChange={(e) => setConfig({ ...config, confidence: parseFloat(e.target.value) })}
                className="w-full accent-brand-500 cursor-pointer"
              />
            </div>

            <div className="pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-slate-300 font-semibold">
                <input
                  type="checkbox"
                  checked={config.simulation_mode}
                  onChange={(e) => setConfig({ ...config, simulation_mode: e.target.checked })}
                  className="rounded border-slate-800 bg-slate-900 text-brand-600 focus:ring-0"
                />
                Enable Demo / Simulation Mode Fallback
              </label>
            </div>
          </div>

          {/* Alert Timers & Cooldowns */}
          <div className="space-y-4 bg-slate-950 p-5 rounded-xl border border-slate-800">
            <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-amber-400" />
              Alert Timers & Sound Settings
            </h4>

            <div>
              <label className="block font-semibold text-slate-400 mb-1">Mobile Usage Alert Threshold (seconds)</label>
              <input
                type="number"
                value={config.alert_time}
                onChange={(e) => setConfig({ ...config, alert_time: parseInt(e.target.value) || 10 })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
                min="1"
                max="60"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-400 mb-1">Alert Cooldown Window (seconds)</label>
              <input
                type="number"
                value={config.alert_cooldown}
                onChange={(e) => setConfig({ ...config, alert_cooldown: parseInt(e.target.value) || 30 })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
                min="5"
                max="300"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-400 mb-1">Beep Frequency (Hz)</label>
                <input
                  type="number"
                  value={config.beep_frequency}
                  onChange={(e) => setConfig({ ...config, beep_frequency: parseInt(e.target.value) || 1000 })}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-400 mb-1">Beep Duration (ms)</label>
                <input
                  type="number"
                  value={config.beep_duration}
                  onChange={(e) => setConfig({ ...config, beep_duration: parseInt(e.target.value) || 500 })}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-brand-600/30 flex items-center gap-2 transition disabled:opacity-50 cursor-pointer"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ConfigurationPage;

