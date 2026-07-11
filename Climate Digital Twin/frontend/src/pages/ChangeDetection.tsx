// frontend/src/pages/ChangeDetection.tsx

import React, { useEffect } from 'react';
import { IndiaMap } from '../components/map/IndiaMap';
import { useAlertStore } from '../store/alertStore';
import { useTwinStore } from '../store/twinStore';
import { FiAlertCircle, FiArrowRight } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface ChangeDetectionProps {
  onNavigate: (path: string) => void;
}

export const ChangeDetection: React.FC<ChangeDetectionProps> = ({ onNavigate }) => {
  const fetchAlerts = useAlertStore((state) => state.fetchAlerts);
  const activeAlerts = useAlertStore((state) => state.activeAlerts);
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  const setSelectedAlert = useAlertStore((state) => state.setSelectedAlert);
  
  const selectedLayer = useTwinStore((state) => state.selectedLayer);
  const setSelectedLayer = useTwinStore((state) => state.setSelectedLayer);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleInspect = (alert: any) => {
    setSelectedAlert(alert);
    // Move to early warning/prediction tab
    onNavigate('/prediction');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">🔍 Real-Time Change Detection</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 4 of 16 — Localized anomaly scanning and threshold breaches</p>
        </div>
        <FlowBadge step="Step 4/16" label="Detection" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Events List */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-5 h-[580px] flex flex-col justify-between">
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
                <FiAlertCircle className="w-4 h-4 text-cyanAccent" />
                <span>Detected Grid Anomalies</span>
              </h3>
              
              <div className="overflow-y-auto max-h-[420px] space-y-2 pr-1">
                {activeAlerts.length === 0 ? (
                  <p className="text-xs text-textMuted">No active anomalies detected across the grid.</p>
                ) : (
                  activeAlerts.map((alert) => {
                    const isSelected = selectedAlert?.id === alert.id;
                    return (
                      <div
                        key={alert.id}
                        onClick={() => setSelectedAlert(alert)}
                        className={`p-3 rounded-lg border text-left cursor-pointer transition-all duration-200 ${
                          isSelected 
                            ? 'bg-redAccent/10 border-redAccent/30' 
                            : 'bg-void/25 border-white/5 hover:border-white/10'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white uppercase">{alert.type.replace('_', ' ')}</span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-redAccent/15 border border-redAccent/30 text-redAccent font-bold uppercase">
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-[10px] text-textMuted">{alert.location.district}, {alert.location.state}</p>
                        
                        {isSelected && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInspect(alert);
                            }}
                            className="mt-3 w-full py-1.5 bg-redAccent hover:bg-redAccent/80 text-white rounded text-[10px] font-bold flex items-center justify-center gap-1.5"
                          >
                            <span>Inspect Forecast & Impact</span>
                            <FiArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-white/5 flex gap-2">
              <button 
                onClick={() => setSelectedLayer('rainfall')}
                className={`flex-1 py-2 rounded text-xs font-bold ${selectedLayer === 'rainfall' ? 'bg-cyanAccent/10 text-cyanAccent' : 'bg-white/5 text-textMuted'}`}
              >
                Rain Heatmap
              </button>
              <button 
                onClick={() => setSelectedLayer('temperature')}
                className={`flex-1 py-2 rounded text-xs font-bold ${selectedLayer === 'temperature' ? 'bg-redAccent/10 text-redAccent' : 'bg-white/5 text-textMuted'}`}
              >
                Temp Heatmap
              </button>
            </div>
          </div>
        </div>

        {/* Geographic Visualizer */}
        <div className="lg:col-span-8 glass-panel p-5 h-[580px] flex flex-col">
          <h3 className="text-sm font-bold tracking-wider text-textMuted uppercase mb-3">
            🌍 Subcontinental Anomaly Map
          </h3>
          <div className="flex-1 min-h-0">
            <IndiaMap />
          </div>
        </div>
      </div>
    </div>
  );
};
