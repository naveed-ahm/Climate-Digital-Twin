// frontend/src/components/layout/AnimatedBackground.tsx

import React from 'react';

export const AnimatedBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 -z-50 overflow-hidden animated-mesh pointer-events-none">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,229,255,0.03),transparent_70%)]" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-blue/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-accent-cyan/5 rounded-full blur-[150px]" />
    </div>
  );
};
