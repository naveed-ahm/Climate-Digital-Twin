// frontend/src/components/layout/Topbar.tsx

import React, { useState, useEffect } from 'react';
import { FiClock, FiAlertTriangle } from 'react-icons/fi';
import { useAlertStore } from '../../store/alertStore';

export const Topbar: React.FC = () => {
  const [elapsed, setElapsed] = useState<number>(0);
  const activeAlerts = useAlertStore((state) => state.activeAlerts);
  const predictions = useAlertStore((state) => state.predictions);

  // Calculate elapsed session time
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatElapsed = (sec: number) => {
    const hrs = Math.floor(sec / 3600).toString().padStart(2, '0');
    const mins = Math.floor((sec % 3600) / 60).toString().padStart(2, '0');
    const secs = (sec % 60).toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
  };

  return (
    <header className="h-16 px-6 glass-panel rounded-none border-b border-x-0 border-t-0 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        <span className="text-[11px] font-bold text-cyanAccent tracking-widest uppercase bg-cyanAccent/10 border border-cyanAccent/20 px-2.5 py-1 rounded">
          🛰️ Mission Control Live
        </span>
        <h2 className="text-sm font-semibold tracking-wide text-textPrimary uppercase">
          Climate Digital Twin AI Platform
        </h2>
      </div>

      <div className="flex items-center gap-6 text-sm">
        {/* Time elapsed timer */}
        <div className="flex items-center gap-2 text-textMuted tabular-nums">
          <FiClock className="w-4 h-4 text-cyanAccent" />
          <span>Mission Elapsed:</span>
          <span className="font-semibold text-textPrimary">{formatElapsed(elapsed)}</span>
        </div>

        {/* Hazard counts */}
        <div className="flex items-center gap-3">
          {activeAlerts.length > 0 && (
            <div className="flex items-center gap-1.5 bg-redAccent/15 border border-redAccent/20 px-2 py-0.5 rounded text-xs text-redAccent font-bold">
              <FiAlertTriangle className="w-3.5 h-3.5" />
              <span>{activeAlerts.length} Active Anomalies</span>
            </div>
          )}
          
          {predictions.length > 0 && (
            <div className="flex items-center gap-1.5 bg-amberAccent/15 border border-amberAccent/20 px-2 py-0.5 rounded text-xs text-amberAccent font-bold">
              <FiAlertTriangle className="w-3.5 h-3.5" />
              <span>{predictions.length} Predicted Hazards</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
