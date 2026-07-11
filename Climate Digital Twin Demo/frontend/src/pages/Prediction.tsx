// frontend/src/pages/Prediction.tsx

import React, { useEffect, useState } from 'react';
import { useAlertStore } from '../store/alertStore';
import { FiTrendingUp, FiArrowRight, FiInfo, FiUsers, FiActivity } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface PredictionProps {
  onNavigate: (path: string) => void;
}

export const Prediction: React.FC<PredictionProps> = ({ onNavigate }) => {
  const fetchAlerts = useAlertStore((state) => state.fetchAlerts);
  const predictions = useAlertStore((state) => state.predictions);
  const activeAlerts = useAlertStore((state) => state.activeAlerts);
  
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  const setSelectedAlert = useAlertStore((state) => state.setSelectedAlert);

  const [impact, setImpact] = useState<Record<string, number> | null>(null);
  const [loadingImpact, setLoadingImpact] = useState<boolean>(false);

  useEffect(() => {
    fetchAlerts();
  }, []);

  // Fetch impact details for selectedAlert
  useEffect(() => {
    if (!selectedAlert) {
      setImpact(null);
      return;
    }

    const fetchImpact = async () => {
      setLoadingImpact(true);
      try {
        const res = await fetch(`http://localhost:8000/api/prediction/${selectedAlert.id}/impact`);
        if (res.ok) {
          const data = await res.json();
          setImpact(data);
        }
      } catch (err) {
        console.error('Failed to fetch event impact:', err);
      } finally {
        setLoadingImpact(false);
      }
    };
    fetchImpact();
  }, [selectedAlert]);

  const handleMitigate = () => {
    // Navigate to strategy generator
    onNavigate('/strategies');
  };

  // Combine active & predicted events for selector
  const allEvents = [...activeAlerts, ...predictions];

  const getImpactColor = (val: number) => {
    if (val >= 75) return 'text-redAccent';
    if (val >= 40) return 'text-amberAccent';
    return 'text-greenAccent';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">🔮 AI Early Warning & Rationale</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 5 of 16 — Temporal projections and population impact modelling</p>
        </div>
        <FlowBadge step="Step 5/16" label="Forecast" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Alerts Timeline / Selector */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-panel p-5 h-[560px] flex flex-col justify-between">
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
                <FiTrendingUp className="w-4 h-4 text-cyanAccent" />
                <span>Forecasting Warning Timeline</span>
              </h3>
              
              <div className="overflow-y-auto max-h-[420px] space-y-2 pr-1">
                {allEvents.length === 0 ? (
                  <p className="text-xs text-textMuted">No climate alerts in the forecast.</p>
                ) : (
                  allEvents.map((evt) => {
                    const isSelected = selectedAlert?.id === evt.id;
                    const isPred = evt.id.startsWith('pred-') || evt.predicted_time != null;
                    return (
                      <div
                        key={evt.id}
                        onClick={() => setSelectedAlert(evt)}
                        className={`p-3 rounded-lg border text-left cursor-pointer transition-all duration-200 ${
                          isSelected 
                            ? 'bg-amberAccent/10 border-amberAccent/30' 
                            : 'bg-void/25 border-white/5 hover:border-white/10'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white uppercase">
                            {isPred ? '🔮' : '🚨'} {evt.type.replace('_', ' ')}
                          </span>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${
                            isPred ? 'bg-amberAccent/15 border border-amberAccent/30 text-amberAccent' : 'bg-redAccent/15 border border-redAccent/30 text-redAccent'
                          }`}>
                            {isPred ? evt.time_window || 'Forecast' : 'Active'}
                          </span>
                        </div>
                        <p className="text-[10px] text-textMuted mt-1">{evt.location.district}, {evt.location.state}</p>
                        <p className="text-[10px] text-cyanAccent font-medium mt-1">Confidence: {(evt.confidence * 100).toFixed(0)}%</p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Selected Alert Details & Impact Model */}
        <div className="lg:col-span-7 space-y-4">
          {selectedAlert ? (
            <div className="glass-panel p-5 space-y-5 h-full flex flex-col justify-between">
              <div className="space-y-4">
                <div className="border-b border-white/5 pb-3">
                  <span className="text-[10px] text-cyanAccent uppercase font-bold tracking-widest">
                    Selected Event Diagnostics
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1">
                    {selectedAlert.type.replace('_', ' ').toUpperCase()} in {selectedAlert.location.district}
                  </h3>
                  <p className="text-xs text-textMuted">{selectedAlert.location.state} • Coordinates: Lat {selectedAlert.location.lat.toFixed(3)}, Lon {selectedAlert.location.lon.toFixed(3)}</p>
                </div>

                {/* Impact Modeling */}
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <FiUsers className="w-4 h-4 text-cyanAccent" />
                    <span>Subcontinental Exposure & Vulnerability Index</span>
                  </h4>
                  {loadingImpact || !impact ? (
                    <p className="text-xs text-textMuted">Running exposure models...</p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                        <span className="text-[10px] text-textMuted uppercase font-semibold">Population Exposed</span>
                        <span className="text-sm font-bold text-white tabular-nums">{impact.population?.toLocaleString()}</span>
                      </div>
                      <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                        <span className="text-[10px] text-textMuted uppercase font-semibold">Infrastructure Risk</span>
                        <span className={`text-sm font-bold tabular-nums ${getImpactColor(impact.infrastructure)}`}>{impact.infrastructure}%</span>
                      </div>
                      <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                        <span className="text-[10px] text-textMuted uppercase font-semibold">Agricultural Loss Risk</span>
                        <span className={`text-sm font-bold tabular-nums ${getImpactColor(impact.agriculture)}`}>{impact.agriculture}%</span>
                      </div>
                      <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                        <span className="text-[10px] text-textMuted uppercase font-semibold">Road Disruptions</span>
                        <span className={`text-sm font-bold tabular-nums ${getImpactColor(impact.roads)}`}>{impact.roads}%</span>
                      </div>
                      <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                        <span className="text-[10px] text-textMuted uppercase font-semibold">Hospital Vulnerability</span>
                        <span className={`text-sm font-bold tabular-nums ${getImpactColor(impact.hospitals)}`}>{impact.hospitals}%</span>
                      </div>
                      <div className="border border-white/5 bg-void/35 p-3 rounded flex flex-col justify-between">
                        <span className="text-[10px] text-textMuted uppercase font-semibold">Power Grid Outage Risk</span>
                        <span className={`text-sm font-bold tabular-nums ${getImpactColor(impact.power)}`}>{impact.power}%</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Mitigation Trigger Button */}
              <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-textMuted">
                  <FiActivity className="w-4 h-4 text-cyanAccent animate-pulse" />
                  <span>Physics projections completed. Ready to wargame.</span>
                </div>
                <button
                  onClick={handleMitigate}
                  className="px-5 py-2.5 bg-blueAccent hover:bg-blueAccent/80 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow-md shadow-blueAccent/10"
                >
                  <span>Select Strategies</span>
                  <FiArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-panel p-5 h-full flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
              <FiInfo className="w-5 h-5 text-cyanAccent" />
              <span>Select an active or predicted alert on the left to review telemetry rationale and population impact models.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
