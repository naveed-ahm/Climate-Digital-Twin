// frontend/src/components/layout/PageShell.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { AnimatedBackground } from './AnimatedBackground';

interface PageShellProps {
  children: React.ReactNode;
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const PageShell: React.FC<PageShellProps> = ({ children, currentPath, onNavigate }) => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-void select-none text-textPrimary">
      {/* Dynamic Background Mesh */}
      <AnimatedBackground />

      {/* Main Sidebar */}
      <Sidebar currentPath={currentPath} onNavigate={onNavigate} />

      {/* Content wrapper */}
      <div className="flex flex-col flex-1 h-full min-w-0">
        {/* Topbar Info */}
        <Topbar />

        {/* Content area */}
        <main className="flex-1 overflow-y-auto p-6 relative">
          <motion.div
            key={currentPath}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            className="h-full w-full"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};
