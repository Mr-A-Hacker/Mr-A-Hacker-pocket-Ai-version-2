import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Avatar({
    className = "",
    variant = "lg", // 'sm' | 'lg'
    onClick,
    animate = true
}) {
    const isSmall = variant === 'sm';
    const scale = isSmall ? 0.4 : 1;

    // States for random behavior
    const [blink, setBlink] = useState(false);
    const [glitch, setGlitch] = useState(false);
    const [expression, setExpression] = useState('neutral'); // neutral, happy, thinking, surprised

    // Random blinking
    useEffect(() => {
        if (!animate) return;
        const interval = setInterval(() => {
            if (Math.random() > 0.7) {
                setBlink(true);
                setTimeout(() => setBlink(false), 150);
            }
        }, 2000);
        return () => clearInterval(interval);
    }, [animate]);

    // Random Personality / Expression Changes
    useEffect(() => {
        if (!animate) return;
        const interval = setInterval(() => {
            const rand = Math.random();
            if (rand > 0.8) {
                const exprs = ['happy', 'thinking', 'surprised', 'neutral'];
                const nextExpr = exprs[Math.floor(Math.random() * exprs.length)];
                setExpression(nextExpr);
                // Reset to neutral after a few seconds
                setTimeout(() => setExpression('neutral'), 2000 + Math.random() * 2000);
            }
        }, 4000);
        return () => clearInterval(interval);
    }, [animate]);

    // Random glitch effect
    useEffect(() => {
        if (!animate) return;
        const interval = setInterval(() => {
            if (Math.random() > 0.95) { // Less frequent glitch
                setGlitch(true);
                setTimeout(() => setGlitch(false), 200);
            }
        }, 5000);
        return () => clearInterval(interval);
    }, [animate]);

    // Pixel sizes
    const pixelSize = 4;

    // Colors
    const c = {
        primary: 'var(--pixel-primary)',
        secondary: 'var(--pixel-secondary)',
        accent: 'var(--pixel-accent)',
        dark: '#1a1b26',
        screen: '#24283b',
        eye: '#00ffff', // Cyan
        highlight: '#ffffff'
    };

    const containerStyle = {
        width: isSmall ? '48px' : '160px',
        height: isSmall ? '48px' : '160px',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: onClick ? 'pointer' : 'default',
    };

    // --- Animation Variants ---

    const floatVariants = {
        animate: {
            y: [0, -4, 0],
            transition: {
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
            }
        }
    };

    const glitchVariants = {
        idle: { x: 0, opacity: 1 },
        glitch: {
            x: [-2, 2, -1, 1, 0],
            opacity: [1, 0.8, 1, 0.9, 1],
            transition: { duration: 0.2 }
        }
    };

    const antennaVariants = {
        animate: {
            rotate: [-5, 5, -5],
            transition: {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
            }
        }
    };

    // Expression-based Eye Variants
    const getEyeScale = (side) => {
        if (blink) return { scaleY: 0.1 };

        switch (expression) {
            case 'happy':
                return { scaleY: 0.5, translateY: -5, borderRadius: '50%' }; // squinty/happy
            case 'thinking':
                return side === 'left' ? { scaleY: 1 } : { scaleY: 0.4 }; // one eye raised/squinted
            case 'surprised':
                return { scale: 1.2 };
            default:
                return { scaleY: 1 };
        }
    };

    return (
        <motion.div
            className={`${className}`}
            style={containerStyle}
            onClick={onClick}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={onClick ? { scale: 1.1 } : {}}
            whileTap={onClick ? { scale: 0.95 } : {}}
        >
            <motion.div
                style={{
                    scale: scale,
                    width: '128px',
                    height: '128px',
                    position: 'relative',
                }}
                variants={floatVariants}
                animate={animate ? "animate" : "initial"}
            >
                {/* --- ROBOT HEAD CONSTRUCTION --- */}
                <motion.div
                    variants={glitchVariants}
                    animate={glitch ? "glitch" : "idle"}
                    className="relative w-full h-full"
                >
                    {/* Antenna */}
                    <motion.div
                        className="absolute left-1/2 top-0"
                        style={{ x: '-50%', transformOrigin: 'bottom center' }}
                        variants={antennaVariants}
                        animate={animate ? "animate" : "initial"}
                    >
                        <div className="w-1 h-6 bg-[var(--pixel-secondary)] mx-auto" />
                        <div className="w-3 h-3 bg-[var(--pixel-accent)] relative -top-1 animate-pulse rounded-none" />
                    </motion.div>

                    {/* Head Shape (Main Box) */}
                    <div className="absolute top-6 left-12 right-12 bottom-20 bg-[var(--pixel-primary)] shadow-[4px_4px_0_0_rgba(0,0,0,0.5)] z-0"
                        style={{
                            left: '24px', right: '24px', top: '24px', bottom: '24px',
                            clipPath: 'polygon(10% 0, 90% 0, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0 90%, 0 10%)'
                        }}>

                        {/* Highlights/Shadows on metal */}
                        <div className="absolute top-2 left-2 w-4 h-4 bg-white/30" />
                        <div className="absolute top-2 right-2 w-full h-2 bg-black/10" />
                    </div>

                    {/* Face Screen */}
                    <div className="absolute bg-[var(--pixel-surface)]"
                        style={{
                            left: '32px', right: '32px', top: '40px', bottom: '40px',
                            boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.5)'
                        }}>

                        {/* Eyes Container - INCREASED GAP */}
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full flex justify-center gap-4">
                            {/* Left Eye */}
                            <motion.div
                                className="w-5 h-8 bg-[#00ffff] shadow-[0_0_10px_#00ffff]"
                                animate={getEyeScale('left')}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                            />
                            {/* Right Eye */}
                            <motion.div
                                className="w-5 h-8 bg-[#00ffff] shadow-[0_0_10px_#00ffff]"
                                animate={getEyeScale('right')}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                            />
                        </div>

                        {/* Mouth - Appears when happy/speaking */}
                        <motion.div
                            className="absolute bottom-3 left-1/2 transform -translate-x-1/2 bg-[#00ffff] opacity-80"
                            animate={{
                                height: expression === 'happy' ? 4 : 2,
                                width: expression === 'happy' ? 24 : 12,
                                opacity: expression === 'neutral' ? 0 : 0.8
                            }}
                        />
                    </div>

                    {/* Earpieces / Headphones */}
                    <div className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-12 bg-[var(--pixel-border)] shadow-[-2px_2px_0_0_rgba(0,0,0,0.3)]" />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-12 bg-[var(--pixel-border)] shadow-[2px_2px_0_0_rgba(0,0,0,0.3)]" />

                </motion.div>

                {/* Orbital Particles (Optional, for 'Amazing' effect) */}
                {!isSmall && animate && (
                    <>
                        <motion.div
                            className="absolute -inset-4 border-2 border-[var(--pixel-primary)] opacity-20"
                            animate={{
                                rotate: 360,
                                scale: [1, 1.05, 1]
                            }}
                            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                            style={{ borderRadius: '40%' }} // Semi-circle glitchy orbit
                        />
                    </>
                )}
            </motion.div>

            {/* Shadow beneath */}
            {!isSmall && (
                <motion.div
                    className="absolute -bottom-4 w-24 h-4 bg-black/20 rounded-[50%]"
                    animate={{
                        scaleX: [1, 0.8, 1],
                        opacity: [0.3, 0.5, 0.3]
                    }}
                    transition={{
                        duration: 4,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
            )}
        </motion.div>
    );
}
