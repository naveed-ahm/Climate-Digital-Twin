// frontend/src/App.tsx

import React, { useState, useEffect } from 'react';
import { PageShell } from './components/layout/PageShell';
import { Home } from './pages/Home';
import { DigitalTwin } from './pages/DigitalTwin';
import { Monitoring } from './pages/Monitoring';
import { ChangeDetection } from './pages/ChangeDetection';
import { Prediction } from './pages/Prediction';
import { Strategies } from './pages/Strategies';
import { Simulation } from './pages/Simulation';
import { Optimizer } from './pages/Optimizer';
import { Resources } from './pages/Resources';
import { Authority } from './pages/Authority';
import { WhatIf } from './pages/WhatIf';
import { MissionLogs } from './pages/MissionLogs';

import { useTwinStore } from './store/twinStore';
import { useAlertStore } from './store/alertStore';

const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>('/');
  const setTwinState = useTwinStore((state) => state.setTwinState);
  const setAlerts = useAlertStore((state) => state.setAlerts);

  // Set up WebSocket connection for real-time telemetry broadcasts
  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWS = () => {
      console.log('Establishing satellite WebSocket connection...');
      socket = new WebSocket('ws://localhost:8000/ws/live');

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'telemetry_update') {
            // Update twin synchronization metrics
            setTwinState({
              sync_pct: data.sync_pct,
              health: data.health,
              last_updated: data.timestamp,
            });
            // Update active anomalies and predictions
            setAlerts(data.active_anomalies, data.predictions);
          }
        } catch (err) {
          console.error('Error parsing WebSocket payload:', err);
        }
      };

      socket.onclose = () => {
        console.log('WebSocket link closed. Attempting reconnect in 5 seconds...');
        reconnectTimeout = setTimeout(connectWS, 5000);
      };

      socket.onerror = (err) => {
        console.error('WebSocket error encountered:', err);
      };
    };

    connectWS();

    return () => {
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  // Simple state router
  const renderPage = () => {
    switch (currentPath) {
      case '/':
        return <Home />;
      case '/digital-twin':
        return <DigitalTwin />;
      case '/monitoring':
        return <Monitoring />;
      case '/detection':
        return <ChangeDetection onNavigate={setCurrentPath} />;
      case '/prediction':
        return <Prediction onNavigate={setCurrentPath} />;
      case '/strategies':
        return <Strategies onNavigate={setCurrentPath} />;
      case '/simulation':
        return <Simulation onNavigate={setCurrentPath} />;
      case '/optimizer':
        return <Optimizer onNavigate={setCurrentPath} />;
      case '/resources':
        return <Resources onNavigate={setCurrentPath} />;
      case '/authority':
        return <Authority />;
      case '/what-if':
        return <WhatIf />;
      case '/mission-logs':
        return <MissionLogs />;
      default:
        return <Home />;
    }
  };

  return (
    <PageShell currentPath={currentPath} onNavigate={setCurrentPath}>
      {renderPage()}
    </PageShell>
  );
};

export default App;
