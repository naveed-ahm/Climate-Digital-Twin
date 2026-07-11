// frontend/src/pages/Simulation.tsx

import React, { useEffect, useState } from 'react';
import { useAlertStore } from '../store/alertStore';
import { useSimStore } from '../store/simStore';
import type { SimulationResult } from '../store/simStore';
import { LeaderboardBar } from '../components/charts/LeaderboardBar';
import { FlowBadge } from '../components/common/FlowBadge';
import { FiSliders, FiArrowRight, FiInfo, FiTrendingUp, FiActivity } from 'react-icons/fi';

interface SimulationProps {
  onNavigate: (path: string) => void;
}

export const Simulation: React.FC<SimulationProps> = ({ onNavigate }) => {
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  const simResults = useSimStore((state) => state.simResults);
  const fetchLeaderboard = useSimStore((state) => state.fetchLeaderboard);

  const [activeRes, setActiveRes] = useState<SimulationResult | null>(null);

  useEffect(() => {
    if (selectedAlert) {
      fetchLeaderboard(selectedAlert.id);
    }
  }, [selectedAlert]);

  // Set the latest simulation run as active
  useEffect(() => {
    if (simResults.length > 0) {
      setActiveRes(simResults[simResults.length - 1]);
    } else {
      setActiveRes(null);
    }
  }, [simResults]);

  const handleNext = () => {
    // Navigate to optimizer wargaming
    onNavigate('/optimizer');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">⚙️ Isolated Digital Twin Sandbox</h2>
          <p className="text-xs text-textMuted mt-0.5">Steps 7-10 of 16 — Isolated simulation sandbox and revert snapshots</p>
        </div>
        <FlowBadge step="Steps 7-10/16" label="Simulation" />
      </div>

      {!selectedAlert ? (
        <div className="glass-panel p-5 h-64 flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
          <FiInfo className="w-5 h-5 text-cyanAccent" />
          <span>No active event selected. Navigate to early warnings or dashboard first.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Simulation Output Stats */}
          <div className="lg:col-span-7 space-y-4">
            {activeRes ? (
              <div className="glass-panel p-5 space-y-5 h-full flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="border-b border-white/5 pb-3 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-cyanAccent uppercase font-bold tracking-widest">
                        Simulation Resulting Delta
                      </span>
                      <h3 className="text-lg font-bold text-white mt-1 uppercase">
                        Strategy: {activeRes.strategy_name || activeRes.strategy_id.replace('strat-', '')}
                      </h3>
                    </div>
                    <span className={`text-xs px-2.5 py-1 rounded font-bold uppercase ${
                      activeRes.success ? 'bg-greenAccent/15 border border-greenAccent/20 text-greenAccent' : 'bg-redAccent/15 border border-redAccent/20 text-redAccent'
                    }`}>
                      {activeRes.success ? 'Success' : 'Infeasible'}
                    </span>
                  </div>

                  {/* Simulated Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                      <span className="text-[10px] text-textMuted uppercase font-semibold">Risk Reduction</span>
                      <span className="text-xl font-bold text-cyanAccent tabular-nums">{activeRes.risk_reduction_pct}%</span>
                    </div>
                    <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                      <span className="text-[10px] text-textMuted uppercase font-semibold">Population Protected</span>
                      <span className="text-xl font-bold text-greenAccent tabular-nums">{activeRes.population_saved.toLocaleString()}</span>
                    </div>
                    <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                      <span className="text-[10px] text-textMuted uppercase font-semibold">Econ. Benefit (INR)</span>
                      <span className="text-xl font-bold text-white tabular-nums">{(activeRes.economic_loss_reduced_inr / 100000).toFixed(1)} Lakh</span>
                    </div>
                    <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                      <span className="text-[10px] text-textMuted uppercase font-semibold">Infra Saved</span>
                      <span className="text-xl font-bold text-white tabular-nums">{activeRes.infrastructure_saved_pct}%</span>
                    </div>
                    <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                      <span className="text-[10px] text-textMuted uppercase font-semibold">AI Utility Score</span>
                      <span className="text-xl font-bold text-cyanAccent tabular-nums">{activeRes.score}%</span>
                    </div>
                  </div>

                  {/* Physics diff details */}
                  <div className="border border-white/5 bg-void/20 p-3 rounded space-y-1">
                    <span className="text-[10px] font-bold text-textMuted uppercase">Simulation physics diff:</span>
                    <div className="flex gap-4 text-xs text-textPrimary">
                      <span>Before state: Temp avg {activeRes.before_state.avg_temp?.toFixed(1)} °C</span>
                      <FiArrowRight className="w-3.5 h-3.5 mt-0.5 text-textMuted" />
                      <span>After state: Temp avg {activeRes.after_state.avg_temp?.toFixed(1)} °C</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-textMuted">
                    <FiActivity className="w-4 h-4 text-greenAccent" />
                    <span>State reverted to pre-sim snapshot cleanly.</span>
                  </div>
                  <button
                    onClick={handleNext}
                    className="px-5 py-2.5 bg-blueAccent hover:bg-blueAccent/80 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow-md shadow-blueAccent/10"
                  >
                    <span>Proceed to Wargaming Leaderboard</span>
                    <FiArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="glass-panel p-5 h-full flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
                <FiSliders className="w-5 h-5 text-cyanAccent animate-pulse" />
                <span>Sandbox is ready. Run a simulation from the Strategy Generator tab to wargame.</span>
              </div>
            )}
          </div>

          {/* Current Leaderboard Comparison */}
          <div className="lg:col-span-5 space-y-4">
            <div className="glass-panel p-5 flex flex-col justify-between h-full">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FiTrendingUp className="w-4 h-4 text-cyanAccent" />
                  <span>Wargaming Leaderboard</span>
                </h3>
                {simResults.length === 0 ? (
                  <p className="text-xs text-textMuted">Run simulations to compare strategies side-by-side.</p>
                ) : (
                  <div className="space-y-4">
                    <LeaderboardBar data={simResults} />
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {simResults.map((r) => (
                        <div key={r.strategy_id} className="flex justify-between items-center text-xs border-b border-white/5 pb-2">
                          <span className="font-semibold text-white">{r.strategy_name || r.strategy_id}</span>
                          <span className="font-bold text-cyanAccent tabular-nums">{r.score}% Utility</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
