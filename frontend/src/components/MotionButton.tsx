import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Check } from 'lucide-react';

type Props = {
  children: React.ReactNode;
  onClick?: () => void | Promise<void>;
  type?: 'button' | 'submit';
  disabled?: boolean;
  className?: string;
  successHoldMs?: number;
};

/**
 * Primary CTA with send → check morph (scale icon, fade label, overlay sweep).
 */
const MotionButton: React.FC<Props> = ({
  children,
  onClick,
  type = 'button',
  disabled,
  className = '',
  successHoldMs = 1200,
}) => {
  const [phase, setPhase] = useState<'idle' | 'loading' | 'done'>('idle');

  const handle = async () => {
    if (disabled || phase === 'loading') return;
    setPhase('loading');
    try {
      await onClick?.();
      setPhase('done');
      window.setTimeout(() => setPhase('idle'), successHoldMs);
    } catch {
      setPhase('idle');
    }
  };

  return (
    <motion.button
      type={type}
      disabled={disabled || phase === 'loading'}
      onClick={type === 'submit' ? undefined : handle}
      className={`tt-btn tt-btn-primary relative min-w-[8.5rem] ${className}`}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.97 }}
    >
      <AnimatePresence mode="wait" initial={false}>
        {phase === 'done' ? (
          <motion.span
            key="check"
            className="inline-flex items-center gap-1.5"
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1.15, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 420, damping: 22 }}
          >
            <motion.span
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
            >
              <Check className="h-4 w-4" strokeWidth={2.5} />
            </motion.span>
          </motion.span>
        ) : (
          <motion.span
            key="label"
            className="inline-flex items-center gap-2"
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0, x: 8 }}
            transition={{ duration: 0.18 }}
          >
            <motion.span
              animate={phase === 'loading' ? { x: [0, 4, 0], scale: [1, 1.15, 1] } : { scale: 1 }}
              transition={phase === 'loading' ? { repeat: Infinity, duration: 0.7 } : {}}
            >
              <ArrowRight className="h-4 w-4" />
            </motion.span>
            <span>{children}</span>
          </motion.span>
        )}
      </AnimatePresence>
      {/* transparent overlay sweep on success */}
      <AnimatePresence>
        {phase === 'done' && (
          <motion.span
            className="pointer-events-none absolute inset-0 bg-white/20"
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45, ease: 'easeOut' }}
          />
        )}
      </AnimatePresence>
    </motion.button>
  );
};

export default MotionButton;
