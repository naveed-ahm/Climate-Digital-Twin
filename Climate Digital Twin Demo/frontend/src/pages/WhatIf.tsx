// frontend/src/pages/WhatIf.tsx

import React, { useState, useEffect } from 'react';
import { IndiaMap } from '../components/map/IndiaMap';
import { useTwinStore } from '../store/twinStore';
import { FiSliders, FiActivity, FiRefreshCw } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

export const WhatIf: React.FC = () => {
  const setTwinState = useTwinStore((state) => state.setTwinState);
  const fetchTwinState = useTwinStore((state) => state.fetchTwinState);

  const [rainfall, setRainfall] = useState<number>(0.0);
  const [temperature, setTemperature] = useState<number>(28.0);
  const [cloudCover, setCloudCover] = useState<number>(0.2);
  const [soilMoisture, setSoilMoisture] = useState<number>(0.5);
  const [windSpeed, setWindSpeed] = useState<number>(15.0);
  const [humidity, setHumidity] = useState<number>(60.0);
  
  const [previewing, setPreviewing] = useState<boolean>(false);

  // Trigger POST /api/twin/whatif to preview grid modifications
  const handlePreview = async () => {
    setPreviewing(true);
    try {
      const res = await fetch('http://localhost:8000/api/twin/whatif', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rainfall,
          temperature,
          cloud_cover: cloudCover,
          soil_moisture: soilMoisture,
          wind_speed: windSpeed,
          humidity
        }),
      });
      if (res.ok) {
        const data = await res.json();
        // Update layers in twinStore to redraw heatmap
        setTwinState({ layers: data.layers });
      }
    } catch (err) {
      console.error('Failed to run what-if preview:', err);
    } finally {
      setPreviewing(false);
    }
  };

  const handleReset = async () => {
    setRainfall(0.0);
    setTemperature(28.0);
    setCloudCover(0.2);
    setSoilMoisture(0.5);
    setWindSpeed(15.0);
    setHumidity(60.0);
    await fetchTwinState();
  };

  // Run preview automatically when sliders change
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      handlePreview();
    }, 400); // debounce API requests
    return () => clearTimeout(delayDebounce);
  }, [rainfall, temperature, cloudCover, soilMoisture, windSpeed, humidity]);

  const sliderFields = [
    { name: 'Rainfall', min: 0.0, max: 80.0, step: 1.0, val: rainfall, setVal: setRainfall, unit: 'mm/h' },
    { name: 'Air Temperature', min: 10.0, max: 55.0, step: 0.5, val: temperature, setVal: setTemperature, unit: '°C' },
    { name: 'Cloud Cover', min: 0.0, max: 1.0, step: 0.05, val: cloudCover, setVal: setCloudCover, unit: 'fraction' },
    { name: 'Soil Moisture', min: 0.05, max: 1.0, step: 0.05, val: soilMoisture, setVal: setSoilMoisture, unit: 'fraction' },
    { name: 'Wind Speed', min: 0.0, max: 150.0, step: 2.0, val: windSpeed, setVal: setWindSpeed, unit: 'km/h' },
    { name: 'Relative Humidity', min: 10.0, max: 100.0, step: 1.0, val: humidity, setVal: setHumidity, unit: '%' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">🧪 Multi-Variate Climate What-If Sandbox</h2>
          <p className="text-xs text-textMuted mt-0.5">Simulate meteorological variables directly and witness physics twin reactions</p>
        </div>
        <FlowBadge step="Step 15/16" label="What-If" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders Control Panel */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-5 space-y-5 h-full flex flex-col justify-between">
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
                <FiSliders className="w-4 h-4 text-cyanAccent" />
                <span>Climate Parameter Sliders</span>
              </h3>
              
              <div className="space-y-4">
                {sliderFields.map((field) => (
                  <div key={field.name} className="space-y-1.5">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-textMuted">{field.name}</span>
                      <span className="text-cyanAccent font-bold tabular-nums">
                        {field.val.toFixed(field.step < 1 ? 2 : 1)} {field.unit}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={field.min}
                      max={field.max}
                      step={field.step}
                      value={field.val}
                      onChange={(e) => field.setVal(parseFloat(e.target.value))}
                      className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyanAccent"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-white/5 flex gap-2">
              <button
                onClick={handleReset}
                className="flex-1 py-2 border border-white/10 hover:bg-white/5 text-xs text-textMuted font-bold rounded flex items-center justify-center gap-1.5"
              >
                <FiRefreshCw className="w-3.5 h-3.5" />
                <span>Reset Simulation</span>
              </button>
            </div>
          </div>
        </div>

        {/* Live Map Previewer */}
        <div className="lg:col-span-8 glass-panel p-5 h-[580px] flex flex-col justify-between relative">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-bold tracking-wider text-textMuted uppercase">
              🧪 Simulated Climate Grid Layer
            </h3>
            {previewing && (
              <div className="flex items-center gap-1.5 text-xs text-cyanAccent font-bold animate-pulse">
                <FiActivity className="w-4 h-4" />
                <span>SOLVING EQUATIONS...</span>
              </div>
            )}
          </div>
          <div className="flex-1 min-h-0">
            <IndiaMap />
          </div>
        </div>
      </div>
    </div>
  );
};
