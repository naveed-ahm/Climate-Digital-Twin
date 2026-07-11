// frontend/src/components/layout/Sidebar.tsx

import React from 'react';
import { 
  FiHome, FiRadio, FiAlertTriangle, FiTrendingUp, FiCpu, 
  FiSliders, FiLayers, FiList, FiCheckSquare, FiFileText
} from 'react-icons/fi';
import { useTwinStore } from '../../store/twinStore';

interface NavItem {
  name: string;
  path: string;
  step?: string;
  icon: any;
}

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPath, onNavigate }) => {
  const syncPct = useTwinStore((state) => state.syncPct);
  const health = useTwinStore((state) => state.health);

  const navItems: NavItem[] = [
    { name: 'Mission Dashboard', path: '/', icon: FiHome },
    { name: 'Digital Twin Layers', path: '/digital-twin', step: 'Step 1 & 3', icon: FiLayers },
    { name: 'Continuous Monitoring', path: '/monitoring', step: 'Step 2', icon: FiRadio },
    { name: 'Change Detection', path: '/detection', step: 'Step 4', icon: FiAlertTriangle },
    { name: 'Early Warnings', path: '/prediction', step: 'Step 5', icon: FiTrendingUp },
    { name: 'Strategy Room', path: '/strategies', step: 'Step 6', icon: FiCpu },
    { name: 'Twin Simulation', path: '/simulation', step: 'Steps 7-10', icon: FiSliders },
    { name: 'AI Action Optimizer', path: '/optimizer', step: 'Step 11', icon: FiSliders },
    { name: 'Resource Logistics', path: '/resources', step: 'Step 12', icon: FiCheckSquare },
    { name: 'Authority Dispatch', path: '/authority', step: 'Steps 13-14', icon: FiFileText },
    { name: 'What-If Sandbox', path: '/what-if', icon: FiSliders },
    { name: 'System Audit Logs', path: '/mission-logs', icon: FiList },
  ];

  return (
    <aside className="w-80 h-screen glass-panel rounded-none border-r border-y-0 border-l-0 flex flex-col justify-between shrink-0">
      <div>
        {/* Header Branding */}
        <div className="p-6 border-b border-[rgba(255,255,255,0.08)] flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyanAccent to-blueAccent text-lg font-bold relative overflow-hidden shadow-lg shadow-cyanAccent/10">
            <div className="absolute inset-0 flex items-center justify-center text-void">◆</div>
            <div className="absolute top-2 left-2 w-1.5 h-1.5 bg-greenAccent rounded-full opacity-70"></div>
            <div className="absolute bottom-2 right-2 w-1 h-1 bg-redAccent rounded-full opacity-60"></div>
          </div>
          <div>
            <h1 className="font-bold text-lg text-glow-cyan text-white tracking-wide">Climate Digital Twin</h1>
            <p className="text-[10px] text-textMuted uppercase font-semibold">AI Mission Control</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1 overflow-y-auto max-h-[70vh]">
          {navItems.map((item) => {
            const isActive = currentPath === item.path;
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={`w-full flex items-center justify-between p-3 rounded-lg text-sm font-medium transition-all duration-200 group text-left ${
                  isActive 
                    ? 'bg-blueAccent/10 text-cyanAccent border border-blueAccent/30' 
                    : 'text-textMuted hover:bg-white/5 hover:text-textPrimary border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110 ${isActive ? 'text-cyanAccent' : 'text-textMuted'}`} />
                  <span>{item.name}</span>
                </div>
                {item.step && (
                  <span className={`text-[9px] px-2 py-0.5 rounded-full border tabular-nums ${
                    isActive 
                      ? 'bg-cyanAccent/10 border-cyanAccent/30 text-cyanAccent' 
                      : 'bg-white/5 border-white/10 text-textMuted'
                  }`}>
                    {item.step}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="p-5 border-t border-[rgba(255,255,255,0.08)] space-y-3 bg-[rgba(5,7,13,0.3)]">
        <div className="flex items-center justify-between text-xs">
          <span className="text-textMuted">Satellite Sync Status:</span>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-greenAccent animate-pulse" />
            <span className="font-semibold text-greenAccent tabular-nums">{syncPct}%</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-xs">
          <span className="text-textMuted">Digital Twin Health:</span>
          <span className={`font-semibold capitalize ${
            health === 'optimal' ? 'text-greenAccent' : health === 'degraded' ? 'text-amberAccent' : 'text-redAccent'
          }`}>
            {health}
          </span>
        </div>
      </div>
    </aside>
  );
};
