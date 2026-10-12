import React, { useEffect, useState } from 'react';
import { Users, AlertTriangle, ShieldCheck, Clock, Search } from 'lucide-react';
import StudentDetailModal from '../components/StudentDetailModal';
import { studentsAPI } from '../services/api';

export const StudentsPage = () => {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStudents = async () => {
    try {
      const res = await studentsAPI.getStudents();
      if (res.data.success) {
        setStudents(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const filteredStudents = students.filter(
    (s) =>
      s.student_id.toLowerCase().includes(search.toLowerCase()) ||
      s.seat.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl border border-brand-500/30">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">Student Monitoring Roster</h3>
            <p className="text-xs text-slate-400">Classroom CSE-301 Tracked Student Profiles</p>
          </div>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search student or seat..."
            className="bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none transition w-64"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStudents.map((stu) => (
          <div
            key={stu.student_id}
            className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-lg space-y-4 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-base font-bold text-slate-100">{stu.student_id}</h4>
                <span className="text-xs font-mono text-slate-400">Seat {stu.seat} &bull; CSE-301</span>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                  stu.risk_level === 'High'
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                    : stu.risk_level === 'Medium'
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                }`}
              >
                {stu.risk_level} Risk
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-[10px] text-slate-500 uppercase block font-semibold">Total Alerts</span>
                <span className="text-sm font-bold text-slate-200">{stu.total_alerts}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-[10px] text-slate-500 uppercase block font-semibold">Duration</span>
                <span className="text-sm font-bold text-slate-200">{stu.total_suspicious_duration}s</span>
              </div>
            </div>

            <button
              onClick={() => setSelectedSeat({ id: stu.seat, label: stu.seat, student_id: stu.student_id })}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
            >
              View Detailed History
            </button>
          </div>
        ))}
      </div>

      <StudentDetailModal seat={selectedSeat} onClose={() => setSelectedSeat(null)} />
    </div>
  );
};

export default StudentsPage;
