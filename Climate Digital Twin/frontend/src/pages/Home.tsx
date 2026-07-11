// frontend/src/pages/Home.tsx

import React, { useEffect } from 'react';
import { IndiaMap } from '../components/map/IndiaMap';
import { useTwinStore } from '../store/twinStore';
import { useAlertStore } from '../store/alertStore';
import { FiActivity, FiCloud, FiCloudRain, FiDroplet, FiInfo, FiThermometer, FiWind } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

export const Home: React.FC = () => {
  const fetchTwinState = useTwinStore((state) => state.fetchTwinState);
  const layers = useTwinStore((state) => state.layers);
  const syncPct = useTwinStore((state) => state.syncPct);
  const health = useTwinStore((state) => state.health);
  
  const fetchAlerts = useAlertStore((state) => state.fetchAlerts);
  const activeAlerts = useAlertStore((state) => state.activeAlerts);
  const predictions = useAlertStore((state) => state.predictions);

  useEffect(() => {
    fetchTwinState();
    fetchAlerts();
    
    // Poll every 5s for fallback updates if WebSockets aren't active yet
    const interval = setInterval(() => {
      fetchTwinState();
      fetchAlerts();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Compute average metrics from layers
  const getAvg = (layerName: string) => {
    if (!layers || !layers[layerName]) return 0;
    const grid = layers[layerName];
    let sum = 0;
    let count = 0;
    for (let r = 0; r < grid.length; r++) {
      for (let c = 0; c < grid[r].length; c++) {
        sum += grid[r][c];
        count++;
      }
    }
    return sum / count;
  };

  const rainfallVal = getAvg('rainfall');
  const tempVal = getAvg('temperature');
  const cloudVal = getAvg('cloud');
  const soilMoistureVal = getAvg('soil_moisture');
  const windVal = getAvg('wind');
  const humidityVal = getAvg('humidity');

  const liveCards = [
    { name: 'Rainfall Rate', value: `${rainfallVal.toFixed(1)} mm/h`, icon: FiCloudRain, color: 'text-cyanAccent' },
    { name: 'Air Temp', value: `${tempVal.toFixed(1)} °C`, icon: FiThermometer, color: 'text-redAccent' },
    { name: 'Cloud Cover', value: `${(cloudVal * 100).toFixed(0)} %`, icon: FiCloud, color: 'text-white' },
    { name: 'Soil Saturation', value: `${(soilMoistureVal * 100).toFixed(0)} %`, icon: FiDroplet, color: 'text-greenAccent' },
    { name: 'Wind Velocity', value: `${windVal.toFixed(1)} km/h`, icon: FiWind, color: 'text-blueAccent' },
    { name: 'Ambient Humidity', value: `${humidityVal.toFixed(1)} %`, icon: FiActivity, color: 'text-cyanAccent' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">Mission Control Dashboard</h2>
          <p className="text-xs text-textMuted mt-0.5">Steps 1-4 of 16 — Live twin monitoring, alerting, and forecast readiness</p>
        </div>
        <FlowBadge step="Step 1-4/16" label="Mission Loop" />
      </div>

      {/* Top Status Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[11px] text-textMuted uppercase font-semibold">Digital Twin Sync</span>
          <span className="text-2xl font-bold text-cyanAccent text-glow-cyan tabular-nums">{syncPct}%</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[11px] text-textMuted uppercase font-semibold">Twin Engine Status</span>
          <span className={`text-2xl font-bold capitalize ${health === 'optimal' ? 'text-greenAccent' : 'text-amberAccent'}`}>{health}</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[11px] text-textMuted uppercase font-semibold">Active Hazards</span>
          <span className="text-2xl font-bold text-redAccent text-glow-red tabular-nums">{activeAlerts.length} Events</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[11px] text-textMuted uppercase font-semibold">AI Predictions (T+48h)</span>
          <span className="text-2xl font-bold text-amberAccent text-glow-amber tabular-nums">{predictions.length} Warnings</span>
        </div>
      </div>

      {/* Map & Live Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 glass-panel p-5 flex flex-col h-[550px]">
          <h3 className="text-sm font-bold tracking-wider text-textMuted uppercase mb-3 flex items-center gap-2">
            🗺️ Live Subcontinental Telemetry
          </h3>
          <div className="flex-1 min-h-0">
            <IndiaMap />
          </div>
        </div>

        <div className="lg:col-span-4 space-y-6">
          {/* Live Climate Grid */}
          <div className="glass-panel p-5">
            <h3 className="text-sm font-bold tracking-wider text-textMuted uppercase mb-4 flex items-center gap-2">
              🚨 Subcontinental Live Averages
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {liveCards.map((card) => {
                const Icon = card.icon;
                return (
                  <div key={card.name} className="border border-white/5 bg-void/35 p-3 rounded-lg flex items-center gap-3">
                    <Icon className={`w-6 h-6 ${card.color}`} />
                    <div>
                      <p className="text-[10px] text-textMuted">{card.name}</p>
                      <p className="text-sm font-bold text-white tabular-nums">{card.value}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Active Warnings Scrollbox */}
          <div className="glass-panel p-5 h-64 flex flex-col">
            <h3 className="text-sm font-bold tracking-wider text-textMuted uppercase mb-3 flex items-center gap-2">
              ⚠️ Early Warnings Feed
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {activeAlerts.length === 0 && predictions.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-textMuted gap-2">
                  <FiInfo className="w-4 h-4 text-greenAccent" />
                  <span>Subcontinent is fully stable. No alerts.</span>
                </div>
              ) : (
                <>
                  {activeAlerts.map((alert) => (
                    <div key={alert.id} className="border-l-2 border-redAccent bg-redAccent/5 p-2 rounded text-xs flex items-center justify-between">
                      <div>
                        <span className="font-bold text-redAccent uppercase">{alert.type.replace('_', ' ')}</span>
                        <p className="text-[10px] text-textMuted">{alert.location.district}, {alert.location.state}</p>
                      </div>
                      <span className="bg-redAccent/10 border border-redAccent/20 px-2 py-0.5 rounded text-[10px] text-redAccent font-semibold uppercase">
                        {alert.severity}
                      </span>
                    </div>
                  ))}
                  {predictions.map((pred) => (
                    <div key={pred.id} className="border-l-2 border-amberAccent bg-amberAccent/5 p-2 rounded text-xs flex items-center justify-between">
                      <div>
                        <span className="font-bold text-amberAccent uppercase">{pred.type.replace('_', ' ')}</span>
                        <p className="text-[10px] text-textMuted">{pred.location.district}, {pred.location.state} • {pred.time_window}</p>
                      </div>
                      <span className="bg-amberAccent/10 border border-amberAccent/20 px-2 py-0.5 rounded text-[10px] text-amberAccent font-semibold uppercase">
                        {(pred.probability! * 100).toFixed(0)}% Conf
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
