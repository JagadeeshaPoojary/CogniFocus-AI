import React from 'react';
import { Smartphone, CheckCircle, AlertTriangle, Eye, Monitor } from 'lucide-react';

export const SeatMapGrid = ({ seats = [], onSelectSeat }) => {
  // Group seats by row
  const rowsMap = {};
  seats.forEach((seat) => {
    const r = seat.row || 1;
    if (!rowsMap[r]) rowsMap[r] = [];
    rowsMap[r].push(seat);
  });

  const sortedRows = Object.keys(rowsMap).sort((a, b) => Number(a) - Number(b));

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
      {/* Visual Smart Board Header */}
      <div className="mb-8">
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center relative shadow-inner overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500 via-brand-500 to-emerald-500" />
          <span className="text-xs font-bold uppercase tracking-widest text-slate-300 flex items-center justify-center gap-2">
            <Monitor className="w-4 h-4 text-emerald-400" />
            SMART BOARD / TEACHER DESK AREA
          </span>
        </div>
      </div>

      {/* Seating Grid */}
      <div className="space-y-4">
        {sortedRows.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            No seat configuration available.
          </div>
        ) : (
          sortedRows.map((rowIdx) => (
            <div key={rowIdx} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {rowsMap[rowIdx]
                .sort((a, b) => (a.col || 0) - (b.col || 0))
                .map((seat) => {
                  const isSuspicious = seat.status === 'suspicious' || seat.status === 'possible_mobile_usage';
                  const isAlert = seat.status === 'alert';
                  const isMonitoring = seat.status === 'monitoring';

                  let statusBg = 'bg-slate-950/80 border-slate-800 hover:border-slate-700';
                  let iconColor = 'text-emerald-400';
                  let statusText = 'Normal';
                  let badgeBg = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';

                  if (isAlert || isSuspicious) {
                    statusBg = 'bg-rose-950/40 border-rose-500/50 shadow-rose-500/10 shadow-lg animate-pulse';
                    iconColor = 'text-rose-400';
                    statusText = 'Possible Mobile Usage';
                    badgeBg = 'bg-rose-500/20 text-rose-300 border-rose-500/30';
                  } else if (isMonitoring) {
                    statusBg = 'bg-amber-950/30 border-amber-500/40';
                    iconColor = 'text-amber-400';
                    statusText = 'Monitoring';
                    badgeBg = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
                  }

                  return (
                    <button
                      key={seat.id}
                      onClick={() => onSelectSeat && onSelectSeat(seat)}
                      className={`p-4 rounded-xl border text-left transition-all duration-200 group cursor-pointer ${statusBg}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-base font-bold text-slate-100 group-hover:text-brand-400 transition">
                          Seat {seat.label || seat.id}
                        </span>
                        <div className={`p-1.5 rounded-lg border ${badgeBg}`}>
                          {isAlert || isSuspicious ? (
                            <Smartphone className="w-4 h-4 text-rose-400 animate-bounce" />
                          ) : isMonitoring ? (
                            <Eye className="w-4 h-4 text-amber-400" />
                          ) : (
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                          )}
                        </div>
                      </div>

                      <div className="text-xs text-slate-400 mb-2 font-mono">
                        Student: <span className="text-slate-200 font-semibold">{seat.student_id || `STU-${seat.id}`}</span>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px]">
                        <span className={`font-medium ${iconColor}`}>
                          {statusText}
                        </span>
                        {seat.duration > 0 && (
                          <span className="bg-rose-500/20 text-rose-300 font-bold px-2 py-0.5 rounded border border-rose-500/30">
                            {seat.duration}s
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
            </div>
          ))
        )}
      </div>

      {/* Legend Footer */}
      <div className="mt-8 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400">
        <span className="font-semibold uppercase tracking-wider text-slate-500 text-[11px]">Seat Status Legend:</span>
        <div className="flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Normal
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Monitoring
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" /> Suspicious / Alert
          </span>
        </div>
      </div>
    </div>
  );
};

export default SeatMapGrid;
