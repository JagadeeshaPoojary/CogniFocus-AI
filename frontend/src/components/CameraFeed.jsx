import React, { useState, useEffect, useRef } from 'react';
import { Camera, VideoOff, RefreshCw, Maximize2, Minimize2, X, Play, Pause, Activity } from 'lucide-react';
import { camerasAPI } from '../services/api';

export const CameraFeed = ({
  camera,
  cameraId,
  classroomId = 'CSE-301',
  fps = 25,
  status = 'online',
  isExpanded: isExpandedProp,
  onExpand,
  onClose,
}) => {
  const [internalExpanded, setInternalExpanded] = useState(false);
  const [error, setError] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const overlayRef = useRef(null);

  // Determine expanded state: controlled by prop or internal state
  const isExpanded = isExpandedProp !== undefined ? isExpandedProp : internalExpanded;

  const camId = cameraId || camera?.camera_id || camera?.id || 'CAM001';
  const camClassroom = classroomId || camera?.classroom_id || 'CSE-301';
  const camFps = fps || camera?.fps || 25;
  const camStatus = status || camera?.status || 'online';

  const defaultProtocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
  const defaultHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
  const API_BASE = import.meta.env.VITE_API_URL || `${defaultProtocol}//${defaultHost}:5000`;
  const token = localStorage.getItem('cognifocus_token');
  const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';

  const [retryNonce, setRetryNonce] = useState(0);

  let streamUrl = `${API_BASE}/api/cameras/${camId}/stream${tokenQuery}`;
  if (retryNonce > 0) {
    streamUrl += `&_retry=${retryNonce}`;
  }

  useEffect(() => {
    console.log(`[STREAM URL]\n${camId} = ${streamUrl}`);
  }, [camId, streamUrl]);

  const handleRetry = (e) => {
    e?.stopPropagation();
    setError(false);
    setRetryNonce((prev) => prev + 1);
  };

  const isOnline = String(camStatus).toLowerCase() === 'online' || String(camStatus).toLowerCase() === 'live';

  const handleImgError = () => {
    if (isOnline) {
      console.warn(`[CameraFeed] ${camId} stream image error while status is LIVE. Retrying stream...`);
      setTimeout(() => {
        setRetryNonce((prev) => prev + 1);
      }, 1500);
    } else {
      setError(true);
    }
  };

  const handleContainerClick = (e) => {
    // Avoid triggering expand when clicking explicit control buttons
    if (e.target.closest('button')) return;

    if (onExpand) {
      onExpand();
    } else {
      setInternalExpanded(true);
    }
  };

  const handleContainerDoubleClick = (e) => {
    if (e.target.closest('button')) return;

    if (!isExpanded) {
      if (onExpand) onExpand();
      else setInternalExpanded(true);
    } else {
      toggleNativeFullscreen();
    }
  };

  const handleClose = (e) => {
    e?.stopPropagation();
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }
    if (onClose) {
      onClose();
    } else {
      setInternalExpanded(false);
    }
  };

  const togglePause = (e) => {
    e?.stopPropagation();
    setIsPaused((prev) => !prev);
  };

  const toggleNativeFullscreen = (e) => {
    e?.stopPropagation();
    if (!overlayRef.current) return;

    if (!document.fullscreenElement) {
      overlayRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch((err) => {
        console.error("Error attempting to enable fullscreen:", err);
      });
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch((err) => {
        console.error("Error attempting to exit fullscreen:", err);
      });
    }
  };

  // Keyboard shortcut: ESC key closes expanded camera view
  useEffect(() => {
    if (!isExpanded) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' || e.code === 'Escape') {
        handleClose();
      }
    };

    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [isExpanded]);

  // Expanded View Render (Dedicated Full-screen Overlay)
  if (isExpanded) {
    return (
      <div
        ref={overlayRef}
        className="camera-expanded-overlay fixed inset-0 z-[9999] bg-black flex flex-col justify-between p-4 overflow-hidden select-none"
        style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#000' }}
      >
        {/* Top Header Information & Controls */}
        <div className="flex items-center justify-between bg-slate-900/90 border border-slate-800 rounded-xl px-5 py-3 shadow-2xl z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-500/20 text-brand-400 rounded-lg border border-brand-500/30">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-mono font-bold text-slate-100 uppercase tracking-wider">
                  {camId} &bull; {camClassroom}
                </span>
                {isOnline ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    LIVE
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                    <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
                    OFFLINE
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                <span className="flex items-center gap-1 text-emerald-400 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  AI Monitoring Active
                </span>
                <span>&bull;</span>
                <span className="font-mono text-slate-300 font-semibold">FPS: {camFps}</span>
              </div>
            </div>
          </div>

          {/* Controls: Close, Fullscreen, Pause/Resume */}
          <div className="flex items-center gap-2">
            <button
              onClick={togglePause}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition flex items-center gap-1.5 cursor-pointer ${
                isPaused
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
              }`}
              title={isPaused ? "Resume Stream" : "Pause Stream"}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              <span>{isPaused ? "Resume" : "Pause"}</span>
            </button>

            <button
              onClick={toggleNativeFullscreen}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
              title="Toggle Browser Fullscreen"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              <span className="hidden sm:inline">{isFullscreen ? "Exit Fullscreen" : "Fullscreen"}</span>
            </button>

            <button
              onClick={handleClose}
              className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-rose-600/30 transition flex items-center gap-1.5 cursor-pointer"
              title="Close Expanded View (ESC)"
            >
              <X className="w-4 h-4" />
              <span>Close</span>
            </button>
          </div>
        </div>

        {/* Video Container (No distortion, object-fit: contain) */}
        <div
          className="flex-1 w-full relative flex items-center justify-center overflow-hidden my-2 bg-black"
          style={{ minHeight: 0 }}
        >
          {!error && !isPaused ? (
            <img
              src={streamUrl}
              alt={`${camId} Live Stream`}
              onError={handleImgError}
              className="w-full h-full block object-contain object-center max-h-full"
              style={{ width: '100%', height: '100%', display: 'block', objectFit: 'contain', objectPosition: 'center' }}
              onDoubleClick={toggleNativeFullscreen}
            />
          ) : isPaused ? (
            <div className="flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Pause className="w-12 h-12 text-amber-400 animate-pulse" />
              <p className="text-sm font-semibold">Stream Paused</p>
              <button
                onClick={togglePause}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded-xl"
              >
                Resume Stream
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-3 text-slate-400">
              <VideoOff className="w-12 h-12 text-rose-500 animate-pulse" />
              <div>
                <span className="text-sm font-bold text-rose-400">● OFFLINE</span>
                <p className="text-xs text-slate-400 mt-1">Camera connection lost ({camId}). Attempting to reconnect...</p>
              </div>
              <button
                onClick={handleRetry}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Retry Connection
              </button>
            </div>
          )}
        </div>

        {/* Expanded Bottom Telemetry Footer */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl px-5 py-2.5 flex items-center justify-between text-xs text-slate-300 shadow-xl z-10">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 font-bold text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              ● AI Monitoring Active
            </span>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="text-slate-400 hidden sm:inline">YOLOv8 Pose Engine</span>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="text-slate-400 hidden sm:inline">Press <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-200 rounded text-[10px] font-mono border border-slate-700">ESC</kbd> to return to grid</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-slate-300 font-semibold">{camFps} FPS</span>
            <span className="font-mono text-slate-500">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    );
  }

  // Normal Camera Grid Card View
  return (
    <div
      onClick={handleContainerClick}
      onDoubleClick={handleContainerDoubleClick}
      className="camera-card w-full min-w-0 bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col group hover:border-brand-500/50 cursor-pointer transition relative"
      style={{ minWidth: 0, overflow: 'hidden' }}
      title="Click or double-click to expand camera view"
    >
      {/* Camera Header */}
      <div className="camera-header bg-slate-900/90 border-b border-slate-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Camera className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-mono font-bold text-slate-100 uppercase tracking-wider">
            {camId} &bull; {camClassroom}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isOnline ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              LIVE
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              OFFLINE
            </span>
          )}
          <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
            {camFps} FPS
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (onExpand) onExpand();
              else setInternalExpanded(true);
            }}
            className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            title="Expand Camera View"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Camera Video Container (16:9 fixed ratio) */}
      <div
        className="camera-video relative w-full aspect-video bg-black flex items-center justify-center overflow-hidden"
        style={{ width: '100%', aspectRatio: '16 / 9', overflow: 'hidden', position: 'relative', background: '#000' }}
      >
        {!error ? (
          <img
            src={streamUrl}
            alt={`${camId} Live Stream`}
            onLoad={(e) => {
              console.log(`${camId} stream dimensions: ${e.target.naturalWidth} x ${e.target.naturalHeight}`);
            }}
            onError={handleImgError}
            className="w-full h-full block object-contain object-center"
            style={{ width: '100%', height: '100%', display: 'block', objectFit: 'contain', objectPosition: 'center' }}
          />
        ) : (
          <div className="absolute inset-0 bg-slate-950 flex flex-col items-center justify-center p-6 text-center space-y-3">
            <VideoOff className="w-10 h-10 text-rose-500 animate-pulse" />
            <div>
              <span className="text-sm font-bold text-rose-400">● OFFLINE</span>
              <p className="text-xs text-slate-400 mt-1">Camera connection lost ({camId}). Attempting to reconnect...</p>
            </div>
            <button
              onClick={handleRetry}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry Connection
            </button>
          </div>
        )}

        {/* Hover Hint Overlay */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
          <span className="px-3 py-1.5 bg-slate-900/90 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 backdrop-blur-sm shadow-xl flex items-center gap-1.5">
            <Maximize2 className="w-3.5 h-3.5 text-brand-400" />
            Click to Expand
          </span>
        </div>

        {/* Camera Status Overlay Footer */}
        <div className="camera-status absolute bottom-2 left-2 right-2 bg-slate-950/80 backdrop-blur-md border border-slate-800/80 px-3 py-1.5 rounded-xl flex items-center justify-between text-[11px] font-medium text-slate-300">
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            AI Monitoring Active
          </span>
          <span className="font-mono text-slate-400">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default CameraFeed;
