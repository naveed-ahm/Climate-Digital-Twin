// frontend/src/pages/Strategies.tsx

import React, { useEffect } from 'react';
import { useAlertStore } from '../store/alertStore';
import { useSimStore } from '../store/simStore';
import { FiArrowRight, FiInfo, FiCheck, FiX, FiClock, FiDollarSign } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface StrategiesProps {
  onNavigate: (path: string) => void;
}

export const Strategies: React.FC<StrategiesProps> = ({ onNavigate }) => {
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  
  const strategies = useSimStore((state) => state.strategies);
  const fetchStrategies = useSimStore((state) => state.fetchStrategies);
  const runSimulation = useSimStore((state) => state.runSimulation);

  useEffect(() => {
    if (selectedAlert) {
      fetchStrategies(selectedAlert.id);
    }
  }, [selectedAlert]);

  const handleSimulate = async (strategyId: string) => {
    if (selectedAlert) {
      await runSimulation(selectedAlert.id, strategyId);
      // Move to simulation visualizer page
      onNavigate('/simulation');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">⚙️ AI Strategy Generator</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 6 of 16 — Contextual strategy template compiles</p>
        </div>
        <FlowBadge step="Step 6/16" label="Strategies" />
      </div>

      {!selectedAlert ? (
        <div className="glass-panel p-5 h-64 flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
          <FiInfo className="w-5 h-5 text-cyanAccent" />
          <span>No event selected. Please select an alert from the Dashboard or Detection panels first.</span>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="glass-panel p-4 bg-blueAccent/5 border border-blueAccent/25 flex items-center justify-between">
            <div className="text-xs">
              <span className="text-textMuted font-medium">Mitigation Focus:</span>
              <span className="text-white font-bold ml-2 uppercase">{selectedAlert.type.replace('_', ' ')}</span>
              <span className="text-textMuted font-medium ml-4">Coordinates:</span>
              <span className="text-white font-bold ml-2">Lat {selectedAlert.location.lat.toFixed(2)}, Lon {selectedAlert.location.lon.toFixed(2)}</span>
            </div>
            <span className="text-[10px] text-cyanAccent font-bold uppercase tracking-wider bg-cyanAccent/10 px-2 py-0.5 rounded">
              Ready to Simulate
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategies.length === 0 ? (
              <p className="text-xs text-textMuted col-span-full">Compiling applicable strategies...</p>
            ) : (
              strategies.map((strat) => (
                <div key={strat.id} className="glass-panel p-5 flex flex-col justify-between h-[360px]">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold text-white uppercase">{strat.title}</h3>
                      <span className="bg-white/5 border border-white/10 px-2 py-0.5 rounded text-[9px] text-textMuted">
                        {(strat.expected_risk_reduction_pct)}% Target Red.
                      </span>
                    </div>
                    <p className="text-xs text-textMuted leading-relaxed h-12 overflow-hidden">{strat.description}</p>
                    
                    {/* Pros and Cons */}
                    <div className="space-y-1.5 pt-2">
                      <div className="flex items-center gap-1.5 text-[11px] text-greenAccent">
                        <FiCheck className="w-3.5 h-3.5" />
                        <span className="truncate">{strat.advantages[0] || 'High efficiency'}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-[11px] text-redAccent">
                        <FiX className="w-3.5 h-3.5" />
                        <span className="truncate">{strat.disadvantages[0] || 'High cost'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Core Metrics & Trigger */}
                  <div className="pt-4 border-t border-white/5 space-y-3">
                    <div className="flex justify-between items-center text-xs text-textMuted">
                      <div className="flex items-center gap-1">
                        <FiClock className="w-3.5 h-3.5 text-cyanAccent" />
                        <span className="tabular-nums">{strat.implementation_time_hours} hrs</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FiDollarSign className="w-3.5 h-3.5 text-greenAccent" />
                        <span className="tabular-nums">{(strat.estimated_cost_inr / 100000).toFixed(0)} Lakh INR</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleSimulate(strat.id)}
                      className="w-full py-2 bg-cyanAccent/10 hover:bg-cyanAccent hover:text-void border border-cyanAccent/30 text-cyanAccent rounded text-xs font-bold transition-all duration-200 flex items-center justify-center gap-1.5"
                    >
                      <span>Simulate Strategy</span>
                      <FiArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
