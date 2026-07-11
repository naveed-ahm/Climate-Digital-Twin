// frontend/src/components/charts/TempTrend.tsx

import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

interface DataPoint {
  time: string;
  value: number;
}

interface TempTrendProps {
  data: DataPoint[];
  color?: string;
  name?: string;
}

export const TempTrend: React.FC<TempTrendProps> = ({ data, color = '#00e5ff', name = 'Value' }) => {
  return (
    <div className="w-full h-32">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={`color-${name}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis dataKey="time" stroke="#7d8aa3" fontSize={9} tickLine={false} />
          <YAxis stroke="#7d8aa3" fontSize={9} tickLine={false} axisLine={false} />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(13, 20, 33, 0.95)', 
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              color: '#e8f1ff',
              fontSize: '11px'
            }} 
          />
          <Area 
            type="monotone" 
            dataKey="value" 
            name={name} 
            stroke={color} 
            strokeWidth={1.5}
            fillOpacity={1} 
            fill={`url(#color-${name})`} 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
