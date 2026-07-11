// frontend/src/pages/Monitoring.tsx

import React, { useState, useEffect } from 'react';
import { FiRadio, FiCheckCircle, FiCpu, FiServer, FiGlobe } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface Feed {
  name: string;
  source: string;
  quality: number;
  status: string;
  payload_preview: string;
}

export const Monitoring: React.FC = () => {
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedFeed, setSelectedFeed] = useState<Feed | null>(null);

  useEffect(() => {
    const fetchFeeds = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/monitoring/feeds');
        if (res.ok) {
          const data = await res.json();
          setFeeds(data);
          setSelectedFeed(data[0]);
        }
      } catch (err) {
        console.error('Failed to fetch feeds:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchFeeds();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">📡 Continuous Monitoring Sat-Feeds</h2>
          <p className="text-xs text-textMuted mt-0.5">Step 2 of 16 — Live multi-sensor ingestion and telemetry calibration</p>
        </div>
        <FlowBadge step="Step 2/16" label="Ingestion" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Feeds List */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-panel p-5">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-4">
              <FiRadio className="w-4 h-4 text-cyanAccent" />
              <span>Active Sat-Telemetry Feeds</span>
            </h3>
            {loading ? (
              <p className="text-xs text-textMuted">Calibrating feeds...</p>
            ) : (
              <div className="space-y-3">
                {feeds.map((feed) => {
                  const isSelected = selectedFeed?.name === feed.name;
                  return (
                    <button
                      key={feed.name}
                      onClick={() => setSelectedFeed(feed)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg border text-left transition-all duration-200 ${
                        isSelected 
                          ? 'bg-blueAccent/10 border-blueAccent/30 text-cyanAccent' 
                          : 'bg-void/25 border-white/5 text-textMuted hover:border-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-2.5 h-2.5 rounded-full bg-greenAccent animate-pulse" />
                        <div>
                          <p className="text-xs font-bold text-white">{feed.name}</p>
                          <p className="text-[10px] text-textMuted">{feed.source} • Calibration Quality: {feed.quality}%</p>
                        </div>
                      </div>
                      <FiCheckCircle className="w-4 h-4 text-greenAccent shrink-0 ml-4" />
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Selected Feed Raw Payload */}
        <div className="lg:col-span-6 space-y-4">
          {selectedFeed && (
            <div className="glass-panel p-5 space-y-4 h-full flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FiCpu className="w-4 h-4 text-cyanAccent" />
                  <span>Raw Telemetry Calibration Payload</span>
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="border border-white/5 bg-void/35 p-3 rounded-lg flex items-center gap-3">
                    <FiServer className="w-5 h-5 text-cyanAccent" />
                    <div>
                      <p className="text-[10px] text-textMuted">Downlink Hub</p>
                      <p className="text-xs font-bold text-white">{selectedFeed.source}</p>
                    </div>
                  </div>
                  <div className="border border-white/5 bg-void/35 p-3 rounded-lg flex items-center gap-3">
                    <FiGlobe className="w-5 h-5 text-cyanAccent" />
                    <div>
                      <p className="text-[10px] text-textMuted">Channel Link</p>
                      <p className="text-xs font-bold text-white">Secure UHF S-Band</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-[11px] font-bold text-textMuted uppercase tracking-wider">Payload Description:</p>
                  <p className="text-xs text-textPrimary leading-relaxed bg-void/30 p-3 rounded border border-white/5 font-mono">
                    {selectedFeed.payload_preview}
                  </p>
                </div>
              </div>

              <div className="text-[10px] text-textMuted leading-relaxed pt-4 border-t border-white/5">
                <i>Continuous monitoring feeds are updated every simulation step via Websocket broadcasting. Interrupted frames automatically fall back to ISRO reanalysis calibrations.</i>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
