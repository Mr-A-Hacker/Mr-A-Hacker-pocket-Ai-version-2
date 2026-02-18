import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, RefreshCw, ExternalLink, MessageSquare, Play, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MiniChat from './MiniChat';

const API_URL = 'http://localhost:8000';

export default function AgenticCoding() {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [iframeKey, setIframeKey] = useState(0);
    const [isChatOpen, setIsChatOpen] = useState(false);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const response = await fetch(`${API_URL}/workspace/projects`);
            const data = await response.json();
            if (data.status === 'success') {
                setProjects(data.projects);
                if (data.projects.length > 0 && !selectedProject) {
                    setSelectedProject(data.projects[0]);
                }
            }
        } catch (error) {
            console.error('Error fetching projects:', error);
        }
    };

    const handleRefreshPreview = () => {
        setIframeKey(prev => prev + 1);
    };

    const handleOpenInNewTab = () => {
        if (selectedProject) {
            window.open(`${API_URL}/apps/${selectedProject}/index.html`, '_blank');
        }
    };

    const previewUrl = selectedProject
        ? `${API_URL}/apps/${selectedProject}/index.html`
        : 'about:blank';

    return (
        <div className="relative w-full h-full bg-black text-[var(--pixel-text)] overflow-hidden font-['VT323']">

            {/* Fullscreen Preview Layer */}
            <div className="absolute inset-0 z-0 bg-[var(--pixel-bg)]">
                {selectedProject ? (
                    <iframe
                        key={iframeKey}
                        src={previewUrl}
                        className="w-full h-full border-0 block"
                        title="App Preview"
                        sandbox="allow-scripts allow-same-origin allow-forms"
                    />
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-[var(--pixel-secondary)] opacity-50">
                        <div className="text-6xl mb-4 font-['Press_Start_2P']">?</div>
                        <p className="text-xl tracking-widest uppercase">SELECT PROJECT_CARTRIDGE</p>
                    </div>
                )}
            </div>

            {/* Overlay Scanlines (optional, might interfere with preview visibility, keeping it subtle or off for the preview area) */}
            <div className="absolute inset-0 z-10 pointer-events-none opacity-10 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))]" style={{ backgroundSize: "100% 2px, 3px 100%" }} />

            {/* Top Toolbar */}
            <div className="absolute top-0 left-0 right-0 z-20 p-4 flex items-center justify-between pointer-events-none">
                {/* Back Button */}
                <div className="pointer-events-auto">
                    <button
                        onClick={() => navigate('/')}
                        className="pixel-btn p-3 flex items-center justify-center bg-[var(--pixel-surface)] border-4 border-[var(--pixel-border)] shadow-[4px_4px_0_0_rgba(0,0,0,0.8)]"
                    >
                        <ArrowLeft size={24} />
                    </button>
                </div>

                {/* Tools (Run, Reload, Eject, Comms) */}
                <div className="flex items-center gap-2 pointer-events-auto bg-[var(--pixel-surface)] p-2 border-4 border-[var(--pixel-border)] shadow-[4px_4px_0_0_rgba(0,0,0,0.8)]">
                    <button
                        onClick={handleRefreshPreview}
                        className="pixel-btn p-3"
                        title="RUN / RELOAD"
                    >
                        <Play size={20} />
                    </button>
                    <button
                        onClick={handleOpenInNewTab}
                        className="pixel-btn p-3"
                        title="EJECT"
                    >
                        <ExternalLink size={20} />
                    </button>
                    <div className="w-1 h-8 bg-[var(--pixel-border)] mx-1" />
                    <button
                        onClick={() => setIsChatOpen(!isChatOpen)}
                        className={`pixel-btn p-3 ${isChatOpen ? 'bg-[var(--pixel-accent)] text-black' : ''}`}
                        title="COMMS"
                    >
                        <MessageSquare size={20} />
                    </button>
                </div>
            </div>

            {/* Bottom Bar: Project Selection */}
            <div className="absolute bottom-0 left-0 right-0 z-20 p-4 flex items-center justify-center pointer-events-none">
                <div className="flex items-center gap-2 pointer-events-auto bg-[var(--pixel-surface)] p-3 border-4 border-[var(--pixel-border)] shadow-[4px_4px_0_0_rgba(0,0,0,0.8)]">
                    <span className="font-['Press_Start_2P'] text-xs mr-2 text-[var(--pixel-primary)]">CARTRIDGE:</span>
                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="pixel-select py-2 px-4 text-sm min-w-[200px]"
                    >
                        <option value="" disabled>SELECT CARTRIDGE</option>
                        {projects.map(p => (
                            <option key={p} value={p}>{p.toUpperCase()}</option>
                        ))}
                    </select>
                    <button onClick={fetchProjects} className="pixel-btn p-3 flex items-center justify-center bg-[var(--pixel-surface)] border-[var(--pixel-border)] hover:bg-[var(--pixel-bg)]" title="REFRESH LIST">
                        <RefreshCw size={20} />
                    </button>
                </div>
            </div>

            {/* Chat Overlay (Drawer) */}
            <AnimatePresence>
                {isChatOpen && (
                    <motion.div
                        initial={{ x: '100%', opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: '100%', opacity: 0 }}
                        transition={{ type: "spring", damping: 20, stiffness: 120 }}
                        className="absolute bottom-4 right-4 w-[400px] h-[600px] bg-[var(--pixel-bg)] border-4 border-[var(--pixel-border)] shadow-[8px_8px_0_0_rgba(0,0,0,0.8)] z-30 flex flex-col overflow-hidden"
                    >
                        <div className="bg-[var(--pixel-primary)] text-black p-2 font-['Press_Start_2P'] text-xs flex justify-between items-center border-b-4 border-[var(--pixel-border)]">
                            <span>AGENT COMMS</span>
                            <button onClick={() => setIsChatOpen(false)} className="hover:text-white">
                                <ChevronDown size={16} />
                            </button>
                        </div>
                        <div className="flex-1 overflow-hidden relative">
                            <MiniChat
                                onClose={() => setIsChatOpen(false)}
                                className="w-full h-full"
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
