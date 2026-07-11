// frontend/src/pages/Optimizer.tsx

import React, { useEffect, useState } from 'react';
import { useAlertStore } from '../store/alertStore';
import { useSimStore } from '../store/simStore';
import type { SimulationResult } from '../store/simStore';
import { FiArrowRight, FiInfo, FiTrendingUp, FiCheckCircle } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import { FlowBadge } from '../components/common/FlowBadge';

interface OptimizerProps {
  onNavigate: (path: string) => void;
}

export const Optimizer: React.FC<OptimizerProps> = ({ onNavigate }) => {
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  
  const leaderboard = useSimStore((state) => state.leaderboard);
  const isRunningOptimizer = useSimStore((state) => state.isRunningOptimizer);
  const runOptimizerAll = useSimStore((state) => state.runOptimizerAll);
  const fetchLeaderboard = useSimStore((state) => state.fetchLeaderboard);

  const [bestStrategy, setBestStrategy] = useState<SimulationResult | null>(null);

  useEffect(() => {
    if (selectedAlert) {
      fetchLeaderboard(selectedAlert.id);
    }
  }, [selectedAlert]);

  useEffect(() => {
    if (leaderboard.length > 0) {
      setBestStrategy(leaderboard[0]);
    } else {
      setBestStrategy(null);
    }
  }, [leaderboard]);

  const handleRunOptimizer = async () => {
    if (selectedAlert) {
      await runOptimizerAll(selectedAlert.id);
    }
  };

  const handleProceed = () => {
    // Navigate to Resource Logistics
    onNavigate('/resources');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">🥇 Closed-Loop AI Action Optimizer</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 11 of 16 — Sequential multi-criteria optimization wargames</p>
        </div>
        <FlowBadge step="Step 11/16" label="Optimizer" />
      </div>

      {!selectedAlert ? (
        <div className="glass-panel p-5 h-64 flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
          <FiInfo className="w-5 h-5 text-cyanAccent" />
          <span>Select an alert to activate optimization wargames.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls & Leaderboard */}
          <div className="lg:col-span-7 space-y-4">
            <div className="glass-panel p-5 space-y-5 h-full flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-white/5 pb-3">
                  <h3 className="text-sm font-bold text-white uppercase">Wargaming Simulation Engine</h3>
                  {!isRunningOptimizer && leaderboard.length === 0 && (
                    <button
                      onClick={handleRunOptimizer}
                      className="px-4 py-2 bg-cyanAccent hover:bg-cyanAccent/95 text-void font-bold text-xs rounded transition-all duration-200"
                    >
                      Run Closed-Loop Optimization
                    </button>
                  )}
                  {isRunningOptimizer && (
                    <span className="text-xs text-cyanAccent font-bold animate-pulse">
                      🛠️ WARGAMING RUNNING...
                    </span>
                  )}
                  {!isRunningOptimizer && leaderboard.length > 0 && (
                    <button
                      onClick={handleRunOptimizer}
                      className="px-4 py-2 border border-cyanAccent/30 text-cyanAccent hover:bg-cyanAccent/10 font-bold text-xs rounded transition-all duration-200"
                    >
                      Re-run Optimization
                    </button>
                  )}
                </div>

                {/* Animated Medal Leaderboard */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-textMuted uppercase tracking-wider">Strategy Ranked Utility</h4>
                  <div className="space-y-2">
                    <AnimatePresence>
                      {leaderboard.length === 0 ? (
                        <p className="text-xs text-textMuted">Optimizer is on standby. Run the optimization loop to evaluate strategies.</p>
                      ) : (
                        leaderboard.map((res, index) => {
                          const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '•';
                          return (
                            <motion.div
                              key={res.strategy_id}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className={`p-3 rounded-lg border flex items-center justify-between text-xs transition-all duration-300 ${
                                index === 0 
                                  ? 'bg-blueAccent/10 border-blueAccent/30 text-cyanAccent' 
                                  : 'bg-void/25 border-white/5 text-textMuted'
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <span className="text-lg">{medal}</span>
                                <div>
                                  <p className="font-bold text-white uppercase">
                                    {res.strategy_name || res.strategy_id.replace('strat-', '')}
                                  </p>
                                  <p className="text-[10px] text-textMuted">Risk reduction: {res.risk_reduction_pct}%</p>
                                </div>
                              </div>
                              <span className="font-bold text-textPrimary tabular-nums">{res.score}% Utility</span>
                            </motion.div>
                          );
                        })
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>

              {/* Action trigger to next step */}
              {!isRunningOptimizer && leaderboard.length > 0 && (
                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-greenAccent">
                    <FiCheckCircle className="w-4 h-4" />
                    <span>Optimization settled. Best strategy identified.</span>
                  </div>
                  <button
                    onClick={handleProceed}
                    className="px-5 py-2.5 bg-blueAccent hover:bg-blueAccent/80 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow-md shadow-blueAccent/10"
                  >
                    <span>Allocate Emergency Assets</span>
                    <FiArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Best Strategy card display */}
          <div className="lg:col-span-5 space-y-4">
            {bestStrategy ? (
              <div className="glass-panel p-5 space-y-4 bg-greenAccent/5 border-greenAccent/20">
                <span className="text-[10px] text-greenAccent uppercase font-bold tracking-widest">
                  🏆 Optimal Solution Identified
                </span>
                <h3 className="text-lg font-bold text-white uppercase">
                  {bestStrategy.strategy_name || bestStrategy.strategy_id.replace('strat-', '')}
                </h3>
                
                <p className="text-xs text-textMuted leading-relaxed">
                  The Multi-Criteria Decision Model scored this strategy as optimal because it provides the best trade-off between risk reduction capacity, economic cost limit constraints, response implementation speed, and feasibility readiness indices.
                </p>

                <div className="border border-white/5 bg-void/35 p-3 rounded space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-textMuted">Simulated Risk Red:</span>
                    <span className="font-bold text-cyanAccent tabular-nums">{bestStrategy.risk_reduction_pct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-textMuted">Survivors Saved:</span>
                    <span className="font-bold text-greenAccent tabular-nums">{bestStrategy.population_saved.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-textMuted">Economic Loss Mitigated:</span>
                    <span className="font-bold text-white tabular-nums">{(bestStrategy.economic_loss_reduced_inr / 100000).toFixed(1)} Lakh INR</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-textMuted">AI Optimization Utility:</span>
                    <span className="font-bold text-cyanAccent tabular-nums">{bestStrategy.score}%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-panel p-5 h-full flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
                <FiTrendingUp className="w-5 h-5 text-cyanAccent" />
                <span>Leaderboard statistics will load once the wargaming loop is executed.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
