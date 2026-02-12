import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function CameraView() {
    const navigate = useNavigate();
    const [status, setStatus] = useState('connecting');
    const [error, setError] = useState(null);
    const imgRef = useRef(null);
    const wsRef = useRef(null);
    const objectUrlRef = useRef(null);

    useEffect(() => {
        const wsUrl = `ws://${window.location.hostname}:8000/camera`;
        console.log('Connecting to camera:', wsUrl);

        const connect = () => {
            const ws = new WebSocket(wsUrl);
            ws.binaryType = 'blob';
            wsRef.current = ws;

            ws.onopen = () => {
                setStatus('connected');
                setError(null);
                console.log('Camera connected');
            };

            ws.onmessage = (event) => {
                if (event.data instanceof Blob) {
                    const url = URL.createObjectURL(event.data);
                    if (imgRef.current) {
                        imgRef.current.src = url;
                    }

                    // Cleanup previous object URL to avoid memory leaks
                    if (objectUrlRef.current) {
                        URL.revokeObjectURL(objectUrlRef.current);
                    }
                    objectUrlRef.current = url;
                }
            };

            ws.onclose = () => {
                setStatus('disconnected');
                console.log('Camera disconnected');
            };

            ws.onerror = (err) => {
                setError('Failed to connect to camera server');
                setStatus('error');
                console.error('WebSocket error:', err);
            };
        };

        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current);
            }
        };
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="relative w-[480px] h-[800px] max-w-full max-h-screen mx-auto overflow-hidden bg-black shadow-2xl flex flex-col"
        >
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-50 p-4 flex items-center justify-between bg-gradient-to-b from-black/60 to-transparent">
                <button
                    onClick={() => navigate('/')}
                    className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white hover:bg-white/30 transition-colors"
                >
                    <ArrowLeft size={24} />
                </button>
                <div className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-white text-xs font-medium uppercase tracking-wider">
                    Live Feed
                </div>
                <div className="w-10"></div> {/* Spacer for symmetry */}
            </div>

            {/* Camera Frame Container */}
            <div className="flex-1 relative flex items-center justify-center overflow-hidden">
                {status === 'connecting' && (
                    <div className="flex flex-col items-center text-white/70">
                        <RefreshCw className="animate-spin mb-4" size={32} />
                        <p>Initializing Camera...</p>
                    </div>
                )}

                {status === 'error' && (
                    <div className="text-center p-6 bg-red-500/20 backdrop-blur-md rounded-2xl border border-red-500/50 text-white max-w-[80%]">
                        <p className="font-bold mb-2">Error</p>
                        <p className="text-sm opacity-90">{error}</p>
                        <button
                            onClick={() => window.location.reload()}
                            className="mt-4 px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors text-sm"
                        >
                            Retry
                        </button>
                    </div>
                )}

                <img
                    ref={imgRef}
                    className="w-full h-full object-cover"
                    alt="Live Camera Feed"
                    style={{ display: status === 'connected' ? 'block' : 'none' }}
                />
            </div>

            {/* Footer / Controls */}
            {status === 'connected' && (
                <div className="absolute bottom-8 left-0 right-0 z-50 flex justify-center">
                    <div className="px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white text-sm flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        480x800 • 30 FPS
                    </div>
                </div>
            )}
        </motion.div>
    );
}
