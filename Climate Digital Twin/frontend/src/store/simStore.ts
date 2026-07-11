// frontend/src/store/simStore.ts

import { create } from 'zustand';

export interface Strategy {
  id: string;
  event_id: string;
  title: string;
  description: string;
  advantages: string[];
  disadvantages: string[];
  implementation_time_hours: number;
  estimated_cost_inr: number;
  required_resources: Record<string, number>;
  expected_risk_reduction_pct: number;
}

export interface SimulationResult {
  strategy_id: string;
  ran_at: string;
  before_state: Record<string, any>;
  after_state: Record<string, any>;
  risk_reduction_pct: number;
  population_saved: number;
  economic_loss_reduced_inr: number;
  water_saved_litres: number;
  infrastructure_saved_pct: number;
  success: boolean;
  score: number;
  strategy_name?: string;
  cost?: number;
  feasibility_score?: number;
  time_efficiency?: number;
}

interface SimStore {
  strategies: Strategy[];
  simResults: SimulationResult[];
  leaderboard: SimulationResult[];
  isRunningOptimizer: boolean;
  fetchStrategies: (eventId: string) => Promise<void>;
  fetchLeaderboard: (eventId: string) => Promise<void>;
  runSimulation: (eventId: string, strategyId: string) => Promise<SimulationResult | null>;
  runOptimizerAll: (eventId: string) => Promise<any>;
  clearSimulationData: () => void;
}

export const useSimStore = create<SimStore>((set, get) => ({
  strategies: [],
  simResults: [],
  leaderboard: [],
  isRunningOptimizer: false,
  fetchStrategies: async (eventId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/strategies/${eventId}`);
      if (res.ok) {
        const data = await res.json();
        set({ strategies: data });
      }
    } catch (err) {
      console.error('Failed to fetch strategies:', err);
    }
  },
  fetchLeaderboard: async (eventId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/optimizer/leaderboard/${eventId}`);
      if (res.ok) {
        const data = await res.json();
        set({ leaderboard: data });
      }
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err);
    }
  },
  runSimulation: async (eventId, strategyId) => {
    try {
      const res = await fetch('http://localhost:8000/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, strategy_id: strategyId }),
      });
      if (res.ok) {
        const data = await res.json();
        set((state) => ({
          simResults: [...state.simResults.filter((r) => r.strategy_id !== strategyId), data],
        }));
        await get().fetchLeaderboard(eventId);
        return data;
      }
    } catch (err) {
      console.error('Failed to run simulation:', err);
    }
    return null;
  },
  runOptimizerAll: async (eventId) => {
    set({ isRunningOptimizer: true });
    try {
      // Simulate running each strategy one by one with delays on the client side
      // for the visual "wargaming" effect before settling the leaderboard!
      const strategies = get().strategies;
      for (const s of strategies) {
        // Run simulation for each strategy
        await get().runSimulation(eventId, s.id);
        // Artificial delay for wargaming animation
        await new Promise((resolve) => setTimeout(resolve, 800));
      }
      
      const res = await fetch(`http://localhost:8000/api/optimizer/run-all/${eventId}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        await get().fetchLeaderboard(eventId);
        set({ isRunningOptimizer: false });
        return data;
      }
    } catch (err) {
      console.error('Failed to run optimizer all:', err);
    }
    set({ isRunningOptimizer: false });
    return null;
  },
  clearSimulationData: () => set({ simResults: [], leaderboard: [] }),
}));
