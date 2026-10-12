import React, { useEffect, useState } from 'react';
import { School, Plus, Edit2, Trash2, KeyRound, Camera, Grid, Check, X } from 'lucide-react';
import { classroomsAPI } from '../services/api';

export const ClassroomsPage = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    code: '',
    rows: 4,
    columns: 3,
    camera_id: 'CAM001',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchClassrooms = async () => {
    try {
      const res = await classroomsAPI.getClassrooms();
      if (res.data.success) {
        setClassrooms(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await classroomsAPI.createClassroom(formData);
      setIsModalOpen(false);
      setFormData({ id: '', name: '', code: '', rows: 4, columns: 3, camera_id: 'CAM001' });
      fetchClassrooms();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create classroom');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm(`Are you sure you want to delete classroom ${id}?`)) {
      try {
        await classroomsAPI.deleteClassroom(id);
        fetchClassrooms();
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl border border-brand-500/30">
            <School className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">Classroom Management</h3>
            <p className="text-xs text-slate-400">Configure classrooms, access codes, seating layouts, and assigned cameras</p>
          </div>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-600/30 flex items-center gap-2 transition"
        >
          <Plus className="w-4 h-4" />
          Add Classroom
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {classrooms.map((cls) => (
          <div
            key={cls.id}
            className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold font-mono text-brand-400 uppercase tracking-widest">{cls.id}</span>
                <h4 className="text-lg font-bold text-slate-100 mt-0.5">{cls.name}</h4>
              </div>
              <button
                onClick={() => handleDelete(cls.id)}
                className="p-2 text-rose-400 hover:bg-rose-500/10 rounded-xl transition"
                title="Delete Classroom"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Access Code</span>
                <div className="flex items-center gap-1.5 font-mono font-bold text-emerald-400">
                  <KeyRound className="w-3.5 h-3.5 text-emerald-500" />
                  {cls.code}
                </div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Grid Dimension</span>
                <div className="flex items-center gap-1.5 font-bold text-slate-200">
                  <Grid className="w-3.5 h-3.5 text-slate-400" />
                  {cls.rows} Rows &times; {cls.columns} Cols ({cls.rows * cls.columns} Seats)
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Camera className="w-3.5 h-3.5 text-slate-500" /> Assigned: <strong className="text-slate-200">{cls.camera_id || 'CAM001'}</strong>
              </span>
              <span>Status: <strong className="text-emerald-400">Active</strong></span>
            </div>
          </div>
        ))}
      </div>

      {/* Create Classroom Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold text-slate-100 mb-4">Create New Classroom</h3>

            {error && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs rounded-xl">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Classroom ID</label>
                <input
                  type="text"
                  value={formData.id}
                  onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                  placeholder="e.g. CSE-302"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none uppercase font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Classroom Full Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Computer Science Hall 302"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Access Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="e.g. CSE302-9901"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none font-mono uppercase"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Rows</label>
                  <input
                    type="number"
                    value={formData.rows}
                    onChange={(e) => setFormData({ ...formData, rows: Number(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
                    min="1"
                    max="10"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Columns</label>
                  <input
                    type="number"
                    value={formData.columns}
                    onChange={(e) => setFormData({ ...formData, columns: Number(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
                    min="1"
                    max="10"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded-xl shadow-lg"
                >
                  Create Classroom
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClassroomsPage;
