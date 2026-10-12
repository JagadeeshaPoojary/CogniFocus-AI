import React, { useEffect, useState } from 'react';
import SeatMapGrid from '../components/SeatMapGrid';
import StudentDetailModal from '../components/StudentDetailModal';
import { monitorAPI } from '../services/api';

export const SeatMapPage = () => {
  const [seats, setSeats] = useState([]);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSeats = async () => {
    try {
      const res = await monitorAPI.getSeats();
      if (res.data.success) {
        setSeats(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSeats();
    const interval = setInterval(fetchSeats, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div>
          <h3 className="text-lg font-bold text-slate-100">Visual Seating Grid & Bench Mapping</h3>
          <p className="text-xs text-slate-400">Classroom CSE-301 &bull; 4 Rows x 3 Columns Layout (B1 .. B12)</p>
        </div>
      </div>

      <SeatMapGrid seats={seats} onSelectSeat={(seat) => setSelectedSeat(seat)} />

      <StudentDetailModal seat={selectedSeat} onClose={() => setSelectedSeat(null)} />
    </div>
  );
};

export default SeatMapPage;
