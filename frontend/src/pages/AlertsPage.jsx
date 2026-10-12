import React, { useEffect, useState } from 'react';
import { BellRing, Filter, Calendar, Eye, RefreshCw, ChevronLeft, ChevronRight, AlertTriangle, Trash2, School } from 'lucide-react';
import AlertBadge from '../components/AlertBadge';
import EvidenceModal from '../components/EvidenceModal';
import { alertsAPI, teacherAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { seedNotifiedAlerts } from '../utils/sound';

export const AlertsPage = () => {
  const { isTeacher } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState('All');
  const [dateFilter, setDateFilter] = useState('All');
  const [classroomFilter, setClassroomFilter] = useState('All My Classrooms');
  const [myClassrooms, setMyClassrooms] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [selectedEvidenceAlert, setSelectedEvidenceAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  // Delete Confirmation Modal State
  const [alertToDelete, setAlertToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  const limit = 20;

  const fetchMyClassrooms = async () => {
    try {
      if (isTeacher) {
        const res = await teacherAPI.getClassrooms();
        if (res.data?.success) {
          setMyClassrooms(res.data.classrooms || []);
        }
      }
    } catch (err) {
      console.error('[AlertsPage fetchMyClassrooms error]', err);
    }
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = {
        status: statusFilter,
        timeframe: dateFilter,
        classroom_id: classroomFilter === 'All My Classrooms' ? 'All' : classroomFilter,
        page,
        limit,
      };
      const res = await alertsAPI.getAlerts(params);
      if (res.data.success) {
        const fetchedList = res.data.data || res.data.alerts || [];
        seedNotifiedAlerts(fetchedList);
        setAlerts(fetchedList);
        setTotalPages(res.data.total_pages || 1);
        setTotalRecords(res.data.total || 0);
      }
    } catch (err) {
      console.error('[AlertsPage fetch error]', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyClassrooms();
  }, [isTeacher]);

  useEffect(() => {
    fetchAlerts();
  }, [statusFilter, dateFilter, classroomFilter, page]);

  const handleAcknowledge = async (id) => {
    try {
      await alertsAPI.acknowledge(id);
      fetchAlerts();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolve = async (id) => {
    try {
      await alertsAPI.resolve(id);
      fetchAlerts();
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirmDelete = async () => {
    if (!alertToDelete || isDeleting) return;
    setIsDeleting(true);
    setDeleteError('');
    try {
      const res = await alertsAPI.deleteAlert(alertToDelete.id);
      if (res.data && res.data.success) {
        const deletedId = alertToDelete.id;
        // 1. Immediately remove alert from current React state
        setAlerts((prev) => prev.filter((a) => a.id !== deletedId));
        
        // 2. Update Total Recorded Events count
        const newTotal = Math.max(0, totalRecords - 1);
        setTotalRecords(newTotal);
        
        // 3. Recalculate pagination
        const newTotalPages = Math.max(1, Math.ceil(newTotal / limit));
        setTotalPages(newTotalPages);

        if (page > newTotalPages) {
          setPage(newTotalPages);
        } else {
          fetchAlerts();
        }

        setAlertToDelete(null);
      } else {
        setDeleteError(res.data?.message || 'Failed to delete alert.');
      }
    } catch (err) {
      console.error('[Delete Alert Error]', err);
      if (err.response && err.response.status === 404) {
        setDeleteError('Alert not found.');
      } else if (err.response && err.response.status === 403) {
        setDeleteError('Forbidden: Admin access required.');
      } else {
        setDeleteError('Failed to delete alert.');
      }
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30">
            <BellRing className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">Classroom Alert History</h3>
            <p className="text-xs text-slate-400">
              Persistent SQLite alert logs ({totalRecords} Total Recorded Events)
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Classroom Filter (Section 15) */}
          {isTeacher && (
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
              <School className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-slate-400 font-semibold">Classroom:</span>
              <select
                value={classroomFilter}
                onChange={(e) => { setClassroomFilter(e.target.value); setPage(1); }}
                className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer"
              >
                <option value="All My Classrooms" className="bg-slate-900">All My Classrooms</option>
                {myClassrooms.map(c => (
                  <option key={c.id} value={c.id} className="bg-slate-900">{c.id} ({c.name || c.code})</option>
                ))}
              </select>
            </div>
          )}

          {/* Status Filter */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-400 font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer"
            >
              <option value="All" className="bg-slate-900">All Statuses</option>
              <option value="Active" className="bg-slate-900">Active</option>
              <option value="Acknowledged" className="bg-slate-900">Acknowledged</option>
              <option value="Resolved" className="bg-slate-900">Resolved</option>
            </select>
          </div>

          {/* Timeframe Date Filter */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-400 font-semibold">Timeframe:</span>
            <select
              value={dateFilter}
              onChange={(e) => { setDateFilter(e.target.value); setPage(1); }}
              className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer"
            >
              <option value="All" className="bg-slate-900">All Time</option>
              <option value="Today" className="bg-slate-900">Today</option>
              <option value="Yesterday" className="bg-slate-900">Yesterday</option>
              <option value="7days" className="bg-slate-900">Last 7 Days</option>
              <option value="30days" className="bg-slate-900">Last 30 Days</option>
            </select>
          </div>

          <button
            onClick={fetchAlerts}
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
            title="Refresh Alerts"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-4">Alert ID</th>
                <th className="px-5 py-4">Classroom</th>
                <th className="px-5 py-4">Seat / Student</th>
                <th className="px-5 py-4">Alert Description</th>
                <th className="px-5 py-4">Camera</th>
                <th className="px-5 py-4">Duration</th>
                <th className="px-5 py-4">Status</th>
                <th className="px-5 py-4">Timestamp</th>
                <th className="px-5 py-4">Evidence</th>
                <th className="px-5 py-4 text-center min-w-[280px]">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {loading ? (
                <tr>
                  <td colSpan="10" className="text-center py-12 text-slate-400 font-medium space-y-2">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-400" />
                    <span>Loading historical alerts from SQLite...</span>
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan="10" className="text-center py-12 text-slate-500 font-medium">
                    No alerts recorded for the selected criteria.
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-5 py-4 font-mono font-bold text-slate-400">#{alert.id}</td>
                    <td className="px-5 py-4 font-mono font-bold text-brand-400">{alert.classroom_id || 'CSE-301'}</td>
                    <td className="px-5 py-4">
                      <div className="font-bold text-slate-100">Seat {alert.seat_id || alert.seat}</div>
                      <div className="text-[11px] font-mono text-slate-400">{alert.student_id}</div>
                    </td>
                    <td className="px-5 py-4 font-semibold text-slate-200">{alert.alert_type}</td>
                    <td className="px-5 py-4 font-mono text-slate-400">{alert.camera_id || 'CAM001'}</td>
                    <td className="px-5 py-4 font-bold text-rose-400">{alert.duration}s</td>
                    <td className="px-5 py-4">
                      <AlertBadge status={alert.status} />
                    </td>
                    <td className="px-5 py-4 font-mono text-[11px] text-slate-400">
                      {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Recent'}
                    </td>
                    <td className="px-5 py-4">
                      <button
                        onClick={() => setSelectedEvidenceAlert(alert)}
                        className="px-2.5 py-1 bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 border border-brand-500/30 text-[11px] font-bold rounded-lg transition inline-flex items-center gap-1 cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Image
                      </button>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <div className="alert-actions">
                        {alert.status === 'Active' && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="acknowledge-btn"
                          >
                            Acknowledge
                          </button>
                        )}
                        {alert.status !== 'Resolved' && (
                          <button
                            onClick={() => handleResolve(alert.id)}
                            className="resolve-btn"
                          >
                            Resolve
                          </button>
                        )}
                        <button
                          onClick={() => { setDeleteError(''); setAlertToDelete(alert); }}
                          className="delete-btn"
                          title="Delete Alert"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="bg-slate-950 px-5 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Showing Page <strong className="text-slate-200">{page}</strong> of <strong className="text-slate-200">{totalPages}</strong> ({totalRecords} Total Records)
          </span>

          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(prev => Math.max(1, prev - 1))}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 border border-slate-800 rounded-lg transition cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono px-2">{page}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 border border-slate-800 rounded-lg transition cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {alertToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
              <div className="p-2.5 bg-rose-500/20 text-rose-400 rounded-xl border border-rose-500/30">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">Delete Alert?</h3>
                <p className="text-xs text-slate-400">Are you sure you want to permanently delete this alert?</p>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-xs space-y-1.5 font-mono text-slate-300">
              <div><span className="text-slate-500">Alert ID:</span> #{alertToDelete.id}</div>
              <div><span className="text-slate-500">Student:</span> {alertToDelete.student_id}</div>
              <div><span className="text-slate-500">Camera:</span> {alertToDelete.camera_id || 'CAM001'}</div>
              <div><span className="text-slate-500">Alert:</span> {alertToDelete.alert_type}</div>
            </div>

            <p className="text-xs text-rose-400 font-semibold">This action cannot be undone.</p>

            {deleteError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-bold">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => { setAlertToDelete(null); setDeleteError(''); }}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-bold rounded-xl border border-slate-700 transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleConfirmDelete}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-rose-600/30 transition flex items-center gap-2 cursor-pointer"
              >
                {isDeleting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <span>Delete</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Snapshot Modal */}
      <EvidenceModal
        alert={selectedEvidenceAlert}
        onClose={() => setSelectedEvidenceAlert(null)}
      />
    </div>
  );
};

export default AlertsPage;
