import React from 'react';
import { motion } from 'framer-motion';
import { MessageCircle, Settings, Camera, Image as GalleryIcon, Clock, Cpu, Code } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Avatar from './Avatar';

const MenuButton = ({ icon: Icon, label, onClick, color }) => (
    <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onClick}
        className="pixel-btn flex flex-col items-center justify-center gap-2 w-full h-32 aspect-square"
        style={{ borderColor: color, color: color }}
    >
        <Icon size={32} />
        <span className="text-xs">{label}</span>
    </motion.button>
);

export default function Home() {
    const navigate = useNavigate();

    const handleAvatarClick = () => {
        navigate('/chat');
    };

    return (
        <div className="relative w-full h-full overflow-hidden bg-[var(--pixel-bg)] flex flex-col items-center justify-center p-4">

            {/* Avatar - Centered */}
            <div className="mb-8 z-10">
                <Avatar
                    variant="lg"
                    animate={true}
                    onClick={handleAvatarClick}
                    className="cursor-pointer hover:scale-105 transition-transform"
                />
            </div>

            {/* Title */}
            <div className="text-center mb-6 z-10">
                <h1 className="text-4xl text-[var(--pixel-primary)] mb-2 drop-shadow-[4px_4px_0_rgba(0,0,0,1)] tracking-widest">POCKET AI</h1>
                <p className="text-[var(--pixel-accent)] text-lg animate-pulse">SYSTEM ONLINE</p>
            </div>

            {/* Settings Button - Top Left */}
            <div className="absolute top-4 left-4 z-20">
                <button
                    onClick={() => navigate('/settings')}
                    className="pixel-btn flex items-center justify-center p-4"
                >
                    <Settings size={32} />
                </button>
            </div>

            {/* Main Menu Grid */}
            <div className="grid grid-cols-2 gap-4 z-10 w-full max-w-[400px]">
                <MenuButton icon={MessageCircle} label="CHAT" onClick={() => navigate('/chat')} color="var(--pixel-primary)" />
                <MenuButton icon={Camera} label="VISION" onClick={() => navigate('/camera')} color="var(--pixel-accent)" />
                <MenuButton icon={GalleryIcon} label="GALLERY" onClick={() => navigate('/gallery')} color="var(--pixel-secondary)" />
                <MenuButton icon={Code} label="AGENT" onClick={() => navigate('/agent')} color="#f7768e" />
                <MenuButton icon={Clock} label="TASKS" onClick={() => navigate('/cron')} color="#e0af68" />
                <MenuButton icon={Cpu} label="GPIO" onClick={() => navigate('/gpio')} color="#7dcfff" />
            </div>

            {/* Decorative BG Elements */}
            <div className="absolute inset-0 pointer-events-none opacity-10"
                style={{
                    backgroundImage: 'linear-gradient(var(--pixel-border) 1px, transparent 1px), linear-gradient(90deg, var(--pixel-border) 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                }}
            />
        </div>
    );
}
