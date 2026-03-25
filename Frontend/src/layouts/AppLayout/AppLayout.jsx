import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../../components/layout/Sidebar';
import Topbar from '../../components/layout/Topbar';
import { motion, AnimatePresence } from 'framer-motion';

const AppLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen">

      {/* Sidebar */}
      <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />

      {/* Main Content */}
      <motion.main
        initial={false}
        animate={{ 
          marginLeft: isCollapsed ? 80 : 280,
          width: `calc(100% - ${isCollapsed ? 80 : 280}px)`
        }}
        className="relative flex-1 p-8 pt-28 min-h-screen transition-all duration-300"
      >
        <Topbar isCollapsed={isCollapsed} />
        
        {/* Background Gradients */}
        <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
          <div className="absolute top-0 right-0 w-200 h-50 bg-blue-600/10 blur-[150px] -translate-y-1/2 translate-x-1/2"></div>
          <div className="absolute bottom-0 left-0 w-150 h-37.5 bg-indigo-600/10 blur-[120px] translate-y-1/2 -translate-x-1/2"></div>
        </div>

        {/* Content Area */}
        <div className="max-w-7xl mx-auto w-full pb-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.main>
    </div>
  );
};

export default AppLayout;
