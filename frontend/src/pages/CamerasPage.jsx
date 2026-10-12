import React, { useEffect, useState } from 'react';
import { Camera, Play, Square, Activity, CheckCircle2, AlertCircle, Plus, Trash2, RefreshCw } from 'lucide-react';
import { camerasAPI, monitorAPI } from '../services/api';

export const CamerasPage = () => {
  const [cameras, setCameras] = useState([]);
  const [testResult, setTestResult] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCameras = async () => {
    try {
      const res = await camerasAPI.getCameras();
      if (res.data.success) {
        setCameras(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleTestCamera = async (camId) => {
    setTestResult({ camId, testing: true });
    try {
      const res = await camerasAPI.testCamera(camId);
      setTestResult({
        camId,
        testing: false,
        success: res.data.success,
        message: res.data.message,
      });
      fetchCameras();
    } catch (err) {
      setTestResult({
        camId,
        testing: false,
        success: false,
        message: err.response?.data?.message || 'Camera test failed',
      });
    }
  };

  const handleStartCamera = async (source) => {
    try {
      await monitorAPI.start(source);
      fetchCameras();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStopCamera = async () => {
    try {
      await monitorAPI.stop();
      fetchCameras();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-brand-500/20 text-brand-400 rounded-xl border border-brand-500/30">
            <Camera className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">Camera Infrastructure</h3>
            <p className="text-xs text-slate-400">Classroom video capture sources & hardware status</p>
          </div>
        </div>

        <button
          onClick={fetchCameras}
          className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition self-start sm:self-auto"
          title="Refresh Cameras"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cameras.map((cam) => {
          const isTesting = testResult?.camId === cam.id && testResult?.testing;
          const isOnline = cam.status === 'Online';

          return (
            <div
              key={cam.id}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-brand-400 uppercase tracking-widest">{cam.id}</span>
                  <h4 className="text-lg font-bold text-slate-100 mt-0.5">{cam.name}</h4>
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                    isOnline
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'}`} />
                  {cam.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Classroom</span>
                  <span className="font-bold text-slate-200">{cam.classroom_id || 'CSE-301'}</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Source Index</span>
                  <span className="font-mono font-bold text-slate-200">Camera {cam.source}</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">FPS</span>
                  <span className="font-bold text-emerald-400">{cam.fps || 28} FPS</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Last Active</span>
                  <span className="font-mono text-slate-400 text-[11px]">19:35:42</span>
                </div>
              </div>

              {testResult?.camId === cam.id && !testResult.testing && (
                <div
                  className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                    testResult.success
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                  }`}
                >
                  {testResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                  {testResult.message}
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80">
                <button
                  onClick={() => handleTestCamera(cam.id)}
                  disabled={isTesting}
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
                >
                  {isTesting ? 'Testing Hardware...' : 'Test Camera'}
                </button>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleStartCamera(cam.source)}
                    className="px-3.5 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold rounded-xl flex items-center gap-1.5 transition"
                  >
                    <Play className="w-3.5 h-3.5 fill-emerald-300" />
                    Start
                  </button>
                  <button
                    onClick={handleStopCamera}
                    className="px-3.5 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 text-xs font-bold rounded-xl flex items-center gap-1.5 transition"
                  >
                    <Square className="w-3.5 h-3.5 fill-rose-300" />
                    Stop
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CamerasPage;
