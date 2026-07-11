// frontend/src/pages/MissionLogs.tsx

import React, { useState, useEffect } from 'react';
import { FiFilter } from 'react-icons/fi';
import { FlowBadge } from '../components/common/FlowBadge';

interface AuditLog {
  id: number;
  timestamp: string;
  module: string;
  severity: string;
  message: string;
  details?: Record<string, any>;
}

export const MissionLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedModule, setSelectedModule] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = 'http://localhost:8000/api/logs?limit=50';
      if (selectedModule) url += `&module=${selectedModule}`;
      if (selectedSeverity) url += `&severity=${selectedSeverity}`;
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedModule, selectedSeverity]);

  const modules = ['Digital Twin', 'Change Detection', 'AI Simulator', 'AI Optimizer', 'Resource Dispatcher'];
  const severities = ['info', 'warning', 'error', 'critical'];

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'critical':
        return 'bg-redAccent/15 border border-redAccent/25 text-redAccent';
      case 'warning':
      case 'error':
        return 'bg-amberAccent/15 border border-amberAccent/25 text-amberAccent';
      default:
        return 'bg-white/5 border border-white/10 text-textMuted';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-white">📋 Mission Audit Logs</h2>
          <p className="text-xs text-textMuted mt-0.5">Chronological system operations trail for wargames and optimizations</p>
        </div>
        <FlowBadge step="Step 16/16" label="Audit" />
      </div>

      <div className="glass-panel p-5 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center justify-between border-b border-white/5 pb-4">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-white">
            <FiFilter className="w-4 h-4 text-cyanAccent" />
            <span>Filter Operations Logs</span>
          </div>

          <div className="flex gap-3 text-xs">
            <select
              value={selectedModule}
              onChange={(e) => setSelectedModule(e.target.value)}
              className="bg-void/85 border border-white/15 px-3 py-1.5 rounded text-textPrimary outline-none focus:border-cyanAccent"
            >
              <option value="">All Modules</option>
              {modules.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>

            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-void/85 border border-white/15 px-3 py-1.5 rounded text-textPrimary outline-none focus:border-cyanAccent"
            >
              <option value="">All Severities</option>
              {severities.map((s) => (
                <option key={s} value={s}>{s.toUpperCase()}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Logs Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <p className="text-xs text-textMuted p-4">Loading operational records...</p>
          ) : logs.length === 0 ? (
            <p className="text-xs text-textMuted p-4">No audit logs found matching criteria.</p>
          ) : (
            <div className="overflow-y-auto max-h-[450px] space-y-2 pr-1">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-[10px] text-textMuted uppercase font-bold">
                    <th className="py-2.5">Timestamp</th>
                    <th className="py-2.5">Module</th>
                    <th className="py-2.5">Severity</th>
                    <th className="py-2.5">Message</th>
                  </tr>
                </thead>
                <tbody className="text-xs text-textPrimary">
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b border-white/5 hover:bg-white/5 transition-all">
                      <td className="py-3 font-mono text-[10px] text-textMuted tabular-nums">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-3 font-bold">{log.module}</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${getSeverityStyle(log.severity)}`}>
                          {log.severity}
                        </span>
                      </td>
                      <td className="py-3 pr-4 leading-relaxed">{log.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
