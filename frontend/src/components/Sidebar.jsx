import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Video,
  Grid3X3,
  BellRing,
  Users,
  School,
  Camera,
  BarChart3,
  Sliders,
  LogOut,
  ShieldCheck,
  Brain
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Sidebar = () => {
  const { user, logout, isAdmin } = useAuth();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Live Monitoring', path: '/live-monitoring', icon: Video },
    { name: 'Seat Map', path: '/seat-map', icon: Grid3X3 },
    { name: 'Alerts', path: '/alerts', icon: BellRing },
    { name: 'Students', path: '/students', icon: Users },
    { name: 'Classrooms', path: '/classrooms', icon: School },
    ...(isAdmin ? [{ name: 'Cameras', path: '/cameras', icon: Camera }] : []),
    { name: 'Reports', path: '/reports', icon: BarChart3 },
    ...(isAdmin ? [{ name: 'Configuration', path: '/configuration', icon: Sliders }] : []),
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 min-h-screen">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-brand-600 to-cyan-500 rounded-xl shadow-lg shadow-brand-500/20 text-white">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-base text-slate-100 tracking-tight">CogniFocus-AI</h1>
            <p className="text-[11px] font-semibold text-slate-400">Classroom Vision Engine</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-brand-600/20 text-brand-400 border border-brand-500/30 shadow-sm'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User Info & Logout */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <div className="flex items-center gap-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-brand-500/20 text-brand-400 flex items-center justify-center font-bold text-xs">
            {user?.name ? user.name[0].toUpperCase() : 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-bold text-slate-200 truncate">{user?.name || 'User'}</p>
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-brand-400">
              <ShieldCheck className="w-3 h-3" />
              {user?.role || 'TEACHER'}
            </span>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 hover:bg-rose-500/20 hover:text-rose-400 text-slate-400 text-xs font-semibold rounded-xl border border-slate-700/60 transition"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
