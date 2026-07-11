// frontend/src/store/resourceStore.ts

import { create } from 'zustand';

export interface ResourceAllocation {
  resource_type: string;
  available: number;
  allocated: number;
  location: { lat: number; lon: number };
  eta_minutes: number;
}

interface ResourceStore {
  allocations: ResourceAllocation[];
  isAllocating: boolean;
  fetchAllocations: (eventId: string) => Promise<void>;
  autoAllocate: (eventId: string, strategyId: string) => Promise<void>;
  clearResourceData: () => void;
}

export const useResourceStore = create<ResourceStore>((set) => ({
  allocations: [],
  isAllocating: false,
  fetchAllocations: async (eventId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/resources/allocation/${eventId}`);
      if (res.ok) {
        const data = await res.json();
        set({ allocations: data });
      }
    } catch (err) {
      console.error('Failed to fetch allocations:', err);
    }
  },
  autoAllocate: async (eventId, strategyId) => {
    set({ isAllocating: true });
    try {
      const res = await fetch('http://localhost:8000/api/resources/auto-allocate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, strategy_id: strategyId }),
      });
      if (res.ok) {
        const data = await res.json();
        set({ allocations: data });
      }
    } catch (err) {
      console.error('Failed to auto allocate resources:', err);
    }
    set({ isAllocating: false });
  },
  clearResourceData: () => set({ allocations: [] }),
}));
