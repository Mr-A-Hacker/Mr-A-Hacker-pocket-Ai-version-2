import React, { useState, useRef, useCallback } from 'react';

export default function ChatInput({ onSend, onAbort, streaming, disabled }) {
    const [text, setText] = useState('');
    const textareaRef = useRef(null);

    const handleSend = useCallback(() => {
        const trimmed = text.trim();
        if (!trimmed || streaming || disabled) return;
        onSend(trimmed);
        setText('');
        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    }, [text, streaming, disabled, onSend]);

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        },
        [handleSend]
    );

    const handleInput = useCallback((e) => {
        setText(e.target.value);
        // Auto-resize textarea
        const el = e.target;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }, []);

    return (
        <div className="min-h-[80px] px-4 py-3 bg-[var(--pixel-surface)] border-t-4 border-[var(--pixel-border)] flex items-end gap-2 pb-[max(12px,env(safe-area-inset-bottom,12px))]">
            <div className="flex-1 flex items-end bg-[var(--pixel-bg)] border-2 border-[var(--pixel-border)] px-4 py-2 focus-within:border-[var(--pixel-primary)]">
                <textarea
                    ref={textareaRef}
                    className="flex-1 border-none bg-transparent text-[var(--pixel-text)] font-['VT323'] text-xl leading-relaxed min-h-[32px] max-h-[120px] resize-none outline-none py-1 placeholder:text-gray-600"
                    value={text}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    placeholder="INSERT COINTOS..."
                    rows={1}
                    disabled={disabled}
                    autoComplete="off"
                    autoCorrect="off"
                />
            </div>

            {streaming ? (
                <button
                    className="w-14 h-14 border-4 border-[var(--pixel-text)] bg-red-500 text-white flex items-center justify-center cursor-pointer shadow-[2px_2px_0_0_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all"
                    onClick={onAbort}
                    aria-label="Stop response"
                >
                    <span className="font-['Press_Start_2P'] text-xs">STOP</span>
                </button>
            ) : (
                <button
                    className="w-14 h-14 border-4 border-[var(--pixel-text)] bg-[var(--pixel-primary)] text-black flex items-center justify-center cursor-pointer shadow-[2px_2px_0_0_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={handleSend}
                    disabled={!text.trim() || disabled}
                    aria-label="Send message"
                >
                    <span className="font-['Press_Start_2P'] text-xs">SEND</span>
                </button>
            )}
        </div>
    );
}
