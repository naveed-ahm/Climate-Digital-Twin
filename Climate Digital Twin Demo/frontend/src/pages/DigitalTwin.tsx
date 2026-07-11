// frontend/src/pages/DigitalTwin.tsx

import React, { useEffect } from 'react';
import { IndiaMap } from '../components/map/IndiaMap';
import { useTwinStore } from '../store/twinStore';
import { FiCloud, FiCloudRain, FiDroplet, FiLayers, FiThermometer, FiWind } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

export const DigitalTwin: React.FC = () => {
  const fetchTwinState = useTwinStore((state) => state.fetchTwinState);
  const selectedLayer = useTwinStore((state) => state.selectedLayer);
  const setSelectedLayer = useTwinStore((state) => state.setSelectedLayer);
  const syncPct = useTwinStore((state) => state.syncPct);

  useEffect(() => {
    fetchTwinState();
  }, []);

  const layerOptions = [
    { name: 'Precipitation', id: 'rainfall', icon: FiCloudRain, desc: 'Accumulated rainfall rate' },
    { name: 'Air Temperature', id: 'temperature', icon: FiThermometer, desc: 'Ambient land/ocean air temperature' },
    { name: 'Cloud Cover', id: 'cloud', icon: FiCloud, desc: 'Visible and infrared satellite cloud fraction' },
    { name: 'Soil Moisture', id: 'soil_moisture', icon: FiDroplet, desc: 'Subsurface soil saturation fraction' },
    { name: 'Wind Velocity', id: 'wind', icon: FiWind, desc: 'Subcontinental atmospheric wind vectors' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">🌍 3D Subcontinental Digital Twin</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 1 & 3 of 16 — Spatial layer stacking and physics calculations</p>
        </div>
        <div className="flex items-center gap-3">
          <FlowBadge step="Step 1 & 3/16" label="Twin State" />
          <div className="glass-panel px-4 py-1.5 flex items-center gap-2 text-xs">
            <span className="w-2 h-2 rounded-full bg-cyanAccent animate-pulse" />
            <span className="text-textMuted">Sync:</span>
            <span className="font-bold text-cyanAccent tabular-nums">{syncPct}%</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Layer Selector Stack */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-5 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
              <FiLayers className="w-4 h-4 text-cyanAccent" />
              <span>Spatio-Temporal Layers</span>
            </h3>
            <p className="text-xs text-textMuted leading-relaxed">
              Bhoomi-Drishti aligns multi-spectral satellite channels and surface telemetry networks into a unified 3D physical grid. Toggle layers to isolate meteorological parameters.
            </p>
            <div className="space-y-2 pt-2">
              {layerOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = selectedLayer === opt.id;
                return (
                  <button
                    key={opt.id}
                    onClick={() => setSelectedLayer(opt.id)}
                    className={`w-full flex items-start gap-4 p-3 rounded-lg border text-left transition-all duration-200 ${
                      isSelected 
                        ? 'bg-cyanAccent/10 border-cyanAccent/30 text-cyanAccent shadow-md' 
                        : 'bg-void/20 border-white/5 text-textMuted hover:border-white/15 hover:text-textPrimary'
                    }`}
                  >
                    <Icon className={`w-5 h-5 mt-0.5 ${isSelected ? 'text-cyanAccent' : 'text-textMuted'}`} />
                    <div>
                      <p className="text-xs font-bold text-white">{opt.name}</p>
                      <p className="text-[10px] text-textMuted mt-0.5 leading-snug">{opt.desc}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Leaflet Viewer */}
        <div className="lg:col-span-8 glass-panel p-5 h-[580px] flex flex-col">
          <h3 className="text-sm font-bold tracking-wider text-textMuted uppercase mb-3">
            🌍 Subcontinental Visualizer
          </h3>
          <div className="flex-1 min-h-0">
            <IndiaMap />
          </div>
        </div>
      </div>
    </div>
  );
};
