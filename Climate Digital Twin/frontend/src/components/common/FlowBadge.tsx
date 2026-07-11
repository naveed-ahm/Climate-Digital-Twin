import React from 'react';

interface FlowBadgeProps {
  step: string;
  label?: string;
}

export const FlowBadge: React.FC<FlowBadgeProps> = ({ step, label = 'Mission Flow' }) => {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-cyanAccent/20 bg-cyanAccent/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-cyanAccent">
      <span className="h-2 w-2 animate-pulse rounded-full bg-cyanAccent" />
      <span>{step}</span>
      <span className="text-textMuted">{label}</span>
    </div>
  );
};
