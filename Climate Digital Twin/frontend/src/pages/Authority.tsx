// frontend/src/pages/Authority.tsx

import React, { useEffect, useState } from 'react';
import { useAlertStore } from '../store/alertStore';
import { FiFileText, FiDownload, FiInfo, FiMessageSquare, FiList, FiCheckCircle } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface ReportDetails {
  sms_broadcast: string;
  scientific_rationale: string;
  operational_checklist: string[];
}

export const Authority: React.FC = () => {
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  const [report, setReport] = useState<ReportDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [acknowledged, setAcknowledged] = useState<boolean>(false);

  useEffect(() => {
    if (!selectedAlert) return;

    const fetchReport = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/authority/report/${selectedAlert.id}`);
        if (res.ok) {
          const data = await res.json();
          setReport(data);
        }
      } catch (err) {
        console.error('Failed to fetch authority report:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
    setAcknowledged(false);
  }, [selectedAlert]);

  const handleDownloadPdf = () => {
    if (selectedAlert) {
      window.open(`http://localhost:8000/api/authority/report/${selectedAlert.id}/pdf`, '_blank');
    }
  };

  const handleAcknowledge = () => {
    setAcknowledged(true);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">📋 Authority Command & Control</h2>
          <p className="text-xs text-textMuted mt-0.5">Steps 13-14 of 16 — Scientific diagnostic reporting and ground dispatch</p>
        </div>
        <FlowBadge step="Steps 13-14/16" label="Authority" />
      </div>

      {!selectedAlert ? (
        <div className="glass-panel p-5 h-64 flex flex-col items-center justify-center text-center text-xs text-textMuted gap-2">
          <FiInfo className="w-5 h-5 text-cyanAccent" />
          <span>Select an alert to activate command controls.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Action Cards */}
          <div className="lg:col-span-8 space-y-6">
            {loading || !report ? (
              <p className="text-xs text-textMuted">Compiling commander report...</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* SMS card */}
                <div className="glass-panel p-5 space-y-4">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <FiMessageSquare className="w-4 h-4 text-cyanAccent" />
                    <span>Emergency SMS Broadcast (CAP)</span>
                  </h3>
                  <p className="text-[11px] text-textMuted">concise emergency cell warning layout ready for distribution:</p>
                  <pre className="text-xs font-mono text-textPrimary leading-relaxed bg-void/35 p-3 rounded border border-white/5 whitespace-pre-wrap select-text">
                    {report.sms_broadcast}
                  </pre>
                </div>

                {/* Checklist card */}
                <div className="glass-panel p-5 space-y-4">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <FiList className="w-4 h-4 text-cyanAccent" />
                    <span>Chronological Operations Checklist</span>
                  </h3>
                  <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
                    {report.operational_checklist.map((item, idx) => (
                      <div key={idx} className="flex gap-2 text-xs text-textPrimary border-b border-white/5 pb-2">
                        <span className="text-cyanAccent font-bold">•</span>
                        <span>{item.replace(/^\d+\.\s+\*\*Phase\s+\d+\s+\([^)]+\)\*\*:\s+/, '').replace(/\*\*/g, '')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Acknowledgment Box */}
            <div className="glass-panel p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FiCheckCircle className={`w-6 h-6 ${acknowledged ? 'text-greenAccent' : 'text-textMuted'}`} />
                <div>
                  <h4 className="text-xs font-bold text-white">Ground Command Acknowledgment</h4>
                  <p className="text-[10px] text-textMuted mt-0.5">
                    {acknowledged ? 'Alert dispatched. Ground responders acknowledging.' : 'Confirm and authorize dispatch of command reports.'}
                  </p>
                </div>
              </div>
              {!acknowledged ? (
                <button
                  onClick={handleAcknowledge}
                  className="px-4 py-2 bg-greenAccent hover:bg-greenAccent/95 text-void font-bold text-xs rounded transition-all duration-200"
                >
                  Authorize Ground Dispatch
                </button>
              ) : (
                <span className="text-xs text-greenAccent font-bold">DISPATCHED & SIGNED</span>
              )}
            </div>
          </div>

          {/* Action Center - PDF Download */}
          <div className="lg:col-span-4 space-y-4">
            <div className="glass-panel p-5 space-y-5 h-full flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white uppercase flex items-center gap-2">
                  <FiFileText className="w-4 h-4 text-cyanAccent" />
                  <span>Command Center PDF</span>
                </h3>
                <p className="text-xs text-textMuted leading-relaxed">
                  Download the comprehensive Bhoomi-Drishti Emergency Climate Report containing scientific diagnosis rationale, spatial polygon coordinates, wargaming charts, and responder resource tables.
                </p>
              </div>

              <button
                onClick={handleDownloadPdf}
                className="w-full py-3 bg-cyanAccent hover:bg-cyanAccent/95 text-void font-bold text-xs rounded transition-all duration-200 flex items-center justify-center gap-2 shadow-md shadow-cyanAccent/10"
              >
                <FiDownload className="w-4 h-4" />
                <span>Download Command PDF Report</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
