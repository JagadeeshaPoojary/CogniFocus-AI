import React, { useEffect, useState } from 'react';
import { Download, BarChart3, PieChart as PieIcon, Flame, Filter, Calendar } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend,
} from 'recharts';
import { reportsAPI } from '../services/api';

export const ReportsPage = () => {
  const [range, setRange] = useState('weekly');
  const [analytics, setAnalytics] = useState({
    total_alerts: 25,
    avg_duration: 38.2,
    alerts_over_time: [],
    alert_types: [],
  });
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [anaRes, heatRes] = await Promise.all([
        reportsAPI.getAnalytics({ range }),
        reportsAPI.getHeatmap(),
      ]);

      if (anaRes.data.success) setAnalytics(anaRes.data.analytics);
      if (heatRes.data.success) setHeatmap(heatRes.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [range]);

  const COLORS = ['#f43f5e', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Header & Export controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl border border-brand-500/30">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">Historical Monitoring Reports</h3>
            <p className="text-xs text-slate-400">Classroom analytics, alert frequencies, and seat intensity heatmaps</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={range}
              onChange={(e) => setRange(e.target.value)}
              className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer"
            >
              <option value="daily" className="bg-slate-900">Daily View</option>
              <option value="weekly" className="bg-slate-900">Weekly View</option>
              <option value="monthly" className="bg-slate-900">Monthly View</option>
            </select>
          </div>

          <a
            href={reportsAPI.getExportUrl()}
            download="cognifocus_monitoring_report.csv"
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-600/30 flex items-center gap-2 transition"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </a>
        </div>
      </div>

      {/* Analytics Charts (2 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Line Chart: Alerts Over Time (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h4 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-400" />
            Alerts Over Time
          </h4>
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.alerts_over_time}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                />
                <Line
                  type="monotone"
                  dataKey="alerts"
                  stroke="#0284c7"
                  strokeWidth={3}
                  dot={{ r: 5, fill: '#0284c7' }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Donut Chart: Alert Types (1 col) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h4 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <PieIcon className="w-5 h-5 text-amber-400" />
            Alert Type Breakdown
          </h4>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={analytics.alert_types}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {analytics.alert_types.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                />
                <Legend formatter={(value) => <span className="text-xs text-slate-300 font-medium">{value}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Classroom Seat Heatmap */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-rose-500/20 text-rose-400 rounded-xl border border-rose-500/30">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-base font-bold text-slate-100">Classroom Seat Alert Heatmap</h4>
              <p className="text-xs text-slate-400">Visual bench frequency map for suspicious activity triggers</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {heatmap.map((seat) => {
            const count = seat.alert_count || 0;
            let bgClass = 'bg-slate-950 border-slate-800 text-slate-400';
            let badgeText = '0 Alerts';

            if (count >= 3) {
              bgClass = 'bg-rose-950/60 border-rose-500/60 text-rose-200 shadow-lg shadow-rose-500/10';
              badgeText = `${count} Alerts (High)`;
            } else if (count >= 1) {
              bgClass = 'bg-amber-950/40 border-amber-500/50 text-amber-200';
              badgeText = `${count} Alert`;
            }

            return (
              <div key={seat.seat} className={`p-4 rounded-xl border transition ${bgClass}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-base text-slate-100">Seat {seat.seat}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-current">
                    {badgeText}
                  </span>
                </div>
                <p className="text-xs text-slate-400">Bench Row {seat.row}, Col {seat.col}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
