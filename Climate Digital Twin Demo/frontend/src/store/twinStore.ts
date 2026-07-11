// frontend/src/store/twinStore.ts

import { create } from 'zustand';

export interface TwinStateData {
  sync_pct: number;
  health: 'optimal' | 'degraded' | 'critical';
  last_updated: string;
  layers: Record<string, number[][]>;
}

interface TwinStore {
  syncPct: number;
  health: 'optimal' | 'degraded' | 'critical';
  lastUpdated: string | null;
  layers: Record<string, number[][]> | null;
  selectedLayer: string;
  setSelectedLayer: (layer: string) => void;
  setTwinState: (state: Partial<TwinStateData>) => void;
  fetchTwinState: () => Promise<void>;
}

export const useTwinStore = create<TwinStore>((set) => ({
  syncPct: 98.5,
  health: 'optimal',
  lastUpdated: null,
  layers: null,
  selectedLayer: 'rainfall',
  setSelectedLayer: (layer) => set({ selectedLayer: layer }),
  setTwinState: (state) => set((prev) => ({
    syncPct: state.sync_pct !== undefined ? state.sync_pct : prev.syncPct,
    health: state.health || prev.health,
    lastUpdated: state.last_updated || prev.lastUpdated,
    layers: state.layers || prev.layers,
  })),
  fetchTwinState: async () => {
    try {
      const res = await fetch('http://localhost:8000/api/twin/state');
      if (res.ok) {
        const data = await res.json();
        set({
          syncPct: data.sync_pct,
          health: data.health,
          lastUpdated: data.last_updated,
          layers: data.layers,
        });
      }
    } catch (err) {
      console.error('Failed to fetch digital twin state:', err);
    }
  },
}));
