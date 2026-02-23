import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';

const WebSocketContext = createContext(null);

const WS_URL = `ws://${window.location.hostname || '127.0.0.1'}:8000/ws`;

export function WebSocketProvider({ children }) {
    const [connStatus, setConnStatus] = useState('connecting'); // connected | disconnected | connecting
    const [messages, setMessages] = useState([]); // Chat messages
    const [streamText, setStreamText] = useState('');
    const [streaming, setStreaming] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [isVoskRecording, setIsVoskRecording] = useState(false);
    const [voiceStatus, setVoiceStatus] = useState('idle'); // idle | listening | thinking | speaking
    const [voskText, setVoskText] = useState('');

    // Generic event listeners for other components
    const eventListeners = useRef({});

    const wsRef = useRef(null);
    const reconnectTimer = useRef(null);

    const addEventListener = useCallback((type, callback) => {
        if (!eventListeners.current[type]) {
            eventListeners.current[type] = [];
        }
        eventListeners.current[type].push(callback);

        // Return unsubscribe function
        return () => {
            eventListeners.current[type] = eventListeners.current[type].filter(cb => cb !== callback);
        };
    }, []);

    const handleServerMessage = useCallback((data) => {
        // 1. Dispatch to generic listeners first
        if (eventListeners.current[data.type]) {
            eventListeners.current[data.type].forEach(cb => cb(data));
        }

        // 2. Handle core chat messages locally (or we could move this out too, but keeping it here for simplicity of migration)
        switch (data.type) {
            case 'history': {
                const history = (data.messages || []).map((m) => ({
                    role: m.role,
                    text: m.text,
                }));
                setMessages(history);
                break;
            }
            case 'stream_start':
                setStreaming(true);
                setStreamText('');
                break;
            case 'stream_delta':
                setStreamText(data.text || '');
                break;
            case 'stream_final':
                setStreaming(false);
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', text: data.text || '' },
                ]);
                setStreamText('');
                break;
            case 'stream_error':
                setStreaming(false);
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', text: `⚠ Error: ${data.error || 'Unknown error'}` },
                ]);
                setStreamText('');
                break;
            case 'stream_aborted':
                setStreaming(false);
                setStreamText((prevStreamText) => {
                    if (prevStreamText) {
                        setMessages((prev) => [
                            ...prev,
                            { role: 'assistant', text: prevStreamText + '\n[aborted]' },
                        ]);
                    }
                    return '';
                });
                break;
            case 'session_reset':
                setMessages([]);
                setStreamText('');
                setStreaming(false);
                break;
            case 'voice_status':
                setVoiceStatus(data.status);
                setIsRecording(data.status === 'listening');
                break;
            case 'voice_transcription':
                // Whisper transcription (final)
                setMessages((prev) => [...prev, { role: 'user', text: data.text }]);
                setVoskText('');
                break;
            case 'vosk_partial':
                setVoskText(data.text || '');
                break;
            case 'vosk_final':
                // Final Vosk result
                setMessages((prev) => [...prev, { role: 'user', text: data.text }]);
                setVoskText('');
                break;
            default:
                break;
        }
    }, []);

    const connect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.onclose = null;
            wsRef.current.close();
        }

        setConnStatus('connecting');
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            setConnStatus('connected');
            clearTimeout(reconnectTimer.current);
        };

        ws.onclose = () => {
            setConnStatus('disconnected');
            wsRef.current = null;
            reconnectTimer.current = setTimeout(connect, 3000);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleServerMessage(data);
            } catch (e) {
                console.error("WS Parse error", e);
            }
        };
    }, [handleServerMessage]);

    useEffect(() => {
        connect();
        return () => {
            clearTimeout(reconnectTimer.current);
            if (wsRef.current) {
                wsRef.current.onclose = null;
                wsRef.current.close();
            }
        };
    }, [connect]);

    const sendMessage = useCallback((type, payload = {}) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type, ...payload }));
        } else {
            console.warn("WS not connected, cannot send", type);
        }
    }, []);
    const toggleVoice = useCallback(() => {
        sendMessage('toggle_voice');
    }, [sendMessage]);

    const startVosk = useCallback(() => {
        setIsVoskRecording(true);
        setVoskText('');
        sendMessage('vosk_start');
    }, [sendMessage]);

    const stopVosk = useCallback(() => {
        setIsVoskRecording(false);
        sendMessage('vosk_stop');
    }, [sendMessage]);

    const value = {
        connStatus,
        messages,
        setMessages,
        streamText,
        streaming,
        isRecording: isRecording || isVoskRecording,
        isVoskRecording,
        voiceStatus,
        voskText,
        sendMessage,
        toggleVoice,
        startVosk,
        stopVosk,
        addEventListener
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWebSocket() {
    return useContext(WebSocketContext);
}
