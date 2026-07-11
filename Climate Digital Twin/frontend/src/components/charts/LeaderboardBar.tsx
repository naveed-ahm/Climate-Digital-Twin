// frontend/src/components/charts/LeaderboardBar.tsx

import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import type { SimulationResult } from '../../store/simStore';

interface LeaderboardBarProps {
  data: SimulationResult[];
}

export const LeaderboardBar: React.FC<LeaderboardBarProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    name: d.strategy_name || d.strategy_id,
    'Composite Utility (%)': d.score,
    'Risk Reduction (%)': d.risk_reduction_pct,
  }));

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 5, left: 30, bottom: 5 }}>
          <XAxis type="number" stroke="#7d8aa3" fontSize={9} tickLine={false} domain={[0, 100]} />
          <YAxis type="category" dataKey="name" stroke="#e8f1ff" fontSize={10} tickLine={false} width={130} />
          <Tooltip
            contentStyle={{
              background: 'rgba(13, 20, 33, 0.95)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              color: '#e8f1ff',
              fontSize: '11px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '10px', color: '#7d8aa3' }} />
          <Bar dataKey="Composite Utility (%)" fill="#2979ff" radius={[0, 4, 4, 0]} barSize={10} />
          <Bar dataKey="Risk Reduction (%)" fill="#00e676" fillOpacity={0.4} stroke="#00e676" strokeWidth={1} radius={[0, 4, 4, 0]} barSize={10} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
