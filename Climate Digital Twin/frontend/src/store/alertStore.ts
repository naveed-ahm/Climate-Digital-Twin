// frontend/src/store/alertStore.ts

import { create } from 'zustand';

export interface Location {
  state: string;
  district: string;
  lat: number;
  lon: number;
}

export interface ClimateEvent {
  id: string;
  type: 'rain' | 'heavy_rain' | 'flood' | 'urban_flood' | 'cyclone' | 'heatwave' | 'cold_wave' | 'drought' | 'forest_fire' | 'urban_heat_island';
  location: Location;
  severity: 'low' | 'moderate' | 'high' | 'severe' | 'critical';
  confidence: number;
  detected_at: string;
  predicted_time?: string | null;
  probability?: number | null;
  impact: Record<string, number>;
  metrics?: Record<string, number>;
  time_window?: string;
}

interface AlertStore {
  activeAlerts: ClimateEvent[];
  predictions: ClimateEvent[];
  selectedAlert: ClimateEvent | null;
  setSelectedAlert: (alert: ClimateEvent | null) => void;
  fetchAlerts: () => Promise<void>;
  setAlerts: (active: ClimateEvent[], predicted: ClimateEvent[]) => void;
}

export const useAlertStore = create<AlertStore>((set) => ({
  activeAlerts: [],
  predictions: [],
  selectedAlert: null,
  setSelectedAlert: (alert) => set({ selectedAlert: alert }),
  setAlerts: (active, predicted) => set({ activeAlerts: active, predictions: predicted }),
  fetchAlerts: async () => {
    try {
      const activeRes = await fetch('http://localhost:8000/api/detection/events');
      const predRes = await fetch('http://localhost:8000/api/prediction/timeline');
      
      let active: ClimateEvent[] = [];
      let predicted: ClimateEvent[] = [];
      
      if (activeRes.ok) {
        active = await activeRes.json();
      }
      if (predRes.ok) {
        predicted = await predRes.json();
      }
      
      set((state) => {
        // Maintain selectedAlert if it still exists, else select the first active or predicted one
        let nextSelected = state.selectedAlert;
        if (nextSelected) {
          const foundActive = active.find((a) => a.id === nextSelected?.id);
          const foundPred = predicted.find((p) => p.id === nextSelected?.id);
          nextSelected = foundActive || foundPred || null;
        }
        if (!nextSelected) {
          nextSelected = active[0] || predicted[0] || null;
        }
        return {
          activeAlerts: active,
          predictions: predicted,
          selectedAlert: nextSelected,
        };
      });
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  },
}));
