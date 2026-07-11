// frontend/src/pages/Resources.tsx

import React, { useEffect } from 'react';
import { useAlertStore } from '../store/alertStore';
import { useSimStore } from '../store/simStore';
import { useResourceStore } from '../store/resourceStore';
import { FiArrowRight, FiInfo, FiActivity, FiTruck } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface ResourcesProps {
  onNavigate: (path: string) => void;
}

export const Resources: React.FC<ResourcesProps> = ({ onNavigate }) => {
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  const leaderboard = useSimStore((state) => state.leaderboard);
  const allocations = useResourceStore((state) => state.allocations);
  const isAllocating = useResourceStore((state) => state.isAllocating);
  const fetchAllocations = useResourceStore((state) => state.fetchAllocations);
  const autoAllocate = useResourceStore((state) => state.autoAllocate);

  useEffect(() => {
    if (selectedAlert) {
      fetchAllocations(selectedAlert.id);
    }
  }, [selectedAlert]);

  const handleAutoAllocate = async () => {
    if (selectedAlert) {
      const bestStrategy = leaderboard[0];
      const strategyId = bestStrategy ? bestStrategy.strategy_id : 'strat-sms';
      await autoAllocate(selectedAlert.id, strategyId);
    }
  };

  const handleProceed = () => {
    // Navigate to Authority Dispatch Module
    onNavigate('/authority');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">🚒 Subcontinental Emergency Resource Allocator</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 12 of 16 — Logistics allocation and response routing</p>
        </div>
        <FlowBadge step="Step 12/16" label="Resources" />
      </div>

      {!selectedAlert ? (
        <div className="glass-panel p-5 h-64 flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
          <FiInfo className="w-5 h-5 text-cyanAccent" />
          <span>Select an alert to activate logistics modeling.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Resource allocations list */}
          <div className="lg:col-span-8 space-y-4">
            <div className="glass-panel p-5 space-y-5 h-full flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-white/5 pb-3">
                  <h3 className="text-sm font-bold text-white uppercase">Linear Assignment Inventory Dispatch</h3>
                  {allocations.length === 0 && !isAllocating && (
                    <button
                      onClick={handleAutoAllocate}
                      className="px-4 py-2 bg-cyanAccent hover:bg-cyanAccent/95 text-void font-bold text-xs rounded transition-all duration-200"
                    >
                      Trigger Logistics Solver
                    </button>
                  )}
                  {isAllocating && (
                    <span className="text-xs text-cyanAccent font-bold animate-pulse">
                      🚚 ROUTING RESOURCES...
                    </span>
                  )}
                  {allocations.length > 0 && !isAllocating && (
                    <button
                      onClick={handleAutoAllocate}
                      className="px-4 py-2 border border-cyanAccent/30 text-cyanAccent hover:bg-cyanAccent/10 font-bold text-xs rounded transition-all duration-200"
                    >
                      Re-run Solver
                    </button>
                  )}
                </div>

                <div className="overflow-y-auto max-h-[380px] space-y-3">
                  {allocations.length === 0 ? (
                    <p className="text-xs text-textMuted">No resources dispatched yet. Activate the solver above.</p>
                  ) : (
                    allocations.map((alloc) => (
                      <div key={alloc.resource_type} className="border border-white/5 bg-void/35 p-3 rounded-lg flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FiTruck className="w-5 h-5 text-cyanAccent" />
                          <div>
                            <span className="text-xs font-bold text-white uppercase">{alloc.resource_type}</span>
                            <p className="text-[10px] text-textMuted">Available pool: {alloc.available} units</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-bold text-greenAccent tabular-nums">{alloc.allocated} units</span>
                          <p className="text-[10px] text-textMuted mt-0.5">ETA: {alloc.eta_minutes} mins</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {allocations.length > 0 && !isAllocating && (
                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-greenAccent">
                    <FiActivity className="w-4 h-4 text-greenAccent" />
                    <span>Resource assignment completed. Route ETAs calculated.</span>
                  </div>
                  <button
                    onClick={handleProceed}
                    className="px-5 py-2.5 bg-blueAccent hover:bg-blueAccent/80 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow-md shadow-blueAccent/10"
                  >
                    <span>Generate Authority Dispatch Payload</span>
                    <FiArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Allocation explanation */}
          <div className="lg:col-span-4 space-y-4">
            <div className="glass-panel p-5 space-y-4 h-full flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white uppercase">Linear Solver Details</h3>
                <p className="text-xs text-textMuted leading-relaxed">
                  Bhoomi-Drishti's resource allocator runs a constraint-based linear optimization script (`scipy.optimize.linear_sum_assignment`) matching nearest available inventory pools to the local demand coordinates, factoring in transport corridors and terrain difficulty.
                </p>
                <div className="border border-white/5 bg-void/35 p-3 rounded text-xs space-y-1 text-textMuted">
                  <p>• Minimizes dispatch delay</p>
                  <p>• Respects regional reserve quotas</p>
                  <p>• Avoids double assignment</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
