import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import StatusIndicator from './StatusIndicator';
import { monitorAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export const Navbar = () => {
  const location = useLocation();
  const { user, isTeacher, isTeacherMonitoringActive, teacherClassroom } = useAuth();
  const [status, setStatus] = useState({ monitoring_active: false, last_updated: '', fps: 0 });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await monitorAPI.getStatus();
        if (res.data.success) {
          setStatus(res.data.data);
        }
      } catch (err) {
        setStatus((prev) => ({ ...prev, monitoring_active: false }));
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const pageTitles = {
    '/dashboard': 'Dashboard',
    '/live-monitoring': 'Live Monitoring Feed',
    '/seat-map': 'Classroom Seat Map',
    '/alerts': 'Alert System Management',
    '/students': 'Student Roster & Monitoring',
    '/classrooms': 'Classroom Management',
    '/cameras': 'Camera Infrastructure',
    '/reports': 'Monitoring Analytics & Reports',
    '/configuration': 'System Configuration',
  };

  const currentTitle = pageTitles[location.pathname] || 'CogniFocus-AI';

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h2 className="text-base font-bold text-slate-100">{currentTitle}</h2>
        <p className="text-[11px] text-slate-400">
          {isTeacher && teacherClassroom
            ? `Classroom ${teacherClassroom.id} (${teacherClassroom.code}) • Teacher Active Session`
            : isTeacher && !isTeacherMonitoringActive
            ? 'No Active Classroom • Enter Code to Start'
            : 'Classroom CSE-301 • Global Camera Infrastructure'}
        </p>
      </div>

      <div className="flex items-center gap-4">
        {isTeacher && teacherClassroom && (
          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 bg-brand-500/10 text-brand-400 border border-brand-500/30 rounded-xl text-xs font-bold font-mono">
            {teacherClassroom.id} ({teacherClassroom.code})
          </span>
        )}
        <StatusIndicator
          active={isTeacher ? isTeacherMonitoringActive : status.monitoring_active}
          lastUpdated={status.last_updated}
          fps={status.fps}
        />
      </div>
    </header>
  );
};

export default Navbar;
