
import React, { useState, useEffect } from 'react';
import { X, Scan, Activity } from 'lucide-react';

const API_BASE = `http://${window.location.hostname || '127.0.0.1'}:8000`;

export default function CameraView({ onClose }) {
    const [mode, setMode] = useState('raw'); // raw, detection, pose
    const [loading, setLoading] = useState(true);

    const startStream = async (targetMode) => {
        try {
            // Fire and forget control request, the image stream will just update content
            await fetch(`${API_BASE}/cv/control`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'start', mode: targetMode })
            });
            setMode(targetMode);
        } catch (e) {
            console.error("Failed to set mode", e);
        }
    };

    const stopStream = async () => {
        try {
            await fetch(`${API_BASE}/cv/control`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'stop' }) // 'mode' is optional/irrelevant for stop
            });
        } catch (e) {
            console.error("Failed to stop", e);
        }
    };

    // On mount, start raw stream
    useEffect(() => {
        startStream('raw');
        return () => {
            stopStream();
        };
    }, []);

    return (
        <div className="absolute inset-0 z-50 bg-black/90 flex flex-col animate-in fade-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between p-4 bg-black/50 backdrop-blur-sm absolute top-0 w-full z-10">
                <div className="text-white font-medium flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${mode !== 'raw' ? 'bg-blue-500' : 'bg-green-500'} animate-pulse`} />
                    Camera Feed
                </div>
                <button
                    onClick={onClose}
                    className="p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
                >
                    <X size={24} />
                </button>
            </div>

            {/* Main Video Area */}
            <div className="flex-1 relative flex items-center justify-center overflow-hidden">
                {/* We use a timestamp to force refresh if needed, but streaming response usually handles it. */}
                <img
                    src={`${API_BASE}/video_feed`}
                    alt="Live Stream"
                    className="max-w-full max-h-full object-contain"
                    onError={(e) => {
                        e.target.style.display = 'none';
                        console.error("Stream error");
                    }}
                />
            </div>

            {/* Controls */}
            <div className="p-6 bg-black/50 backdrop-blur-md flex items-center justify-center gap-4 absolute bottom-0 w-full">

                <button
                    onClick={() => startStream(mode === 'detection' ? 'raw' : 'detection')}
                    className={`flex flex-col items-center gap-1 p-3 min-w-[80px] rounded-xl transition-all ${mode === 'detection'
                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                            : 'bg-white/10 text-zinc-300 hover:bg-white/20'
                        }`}
                >
                    <Scan size={24} />
                    <span className="text-xs font-medium">Detect</span>
                </button>

                <button
                    onClick={() => startStream(mode === 'pose' ? 'raw' : 'pose')}
                    className={`flex flex-col items-center gap-1 p-3 min-w-[80px] rounded-xl transition-all ${mode === 'pose'
                            ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30'
                            : 'bg-white/10 text-zinc-300 hover:bg-white/20'
                        }`}
                >
                    <Activity size={24} />
                    <span className="text-xs font-medium">Pose</span>
                </button>

            </div>
        </div>
    );
}
