import React from 'react';
import { motion } from 'framer-motion';
import { Bell, Search, User, Menu, Sun, Moon } from 'lucide-react';

const TopNav: React.FC<{ darkMode: boolean; toggleDarkMode: () => void; toggleSidebar: () => void }> = ({ darkMode, toggleDarkMode, toggleSidebar }) => {
  return (
    <header className="bg-white/5 backdrop-blur-lg shadow-md p-4 flex items-center justify-between border-b border-white/10">
      <div className="flex items-center space-x-4">
        <button className="p-2 rounded-xl hover:bg-white/10 transition-colors" onClick={toggleSidebar}> {/* New: Sidebar toggle */}
          <Menu className="h-6 w-6 text-white" />
        </button>
        <h2 className="text-xl font-semibold text-white">Dashboard</h2>
      </div>
      
      <div className="relative w-96">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
        <input
          type="text"
          placeholder="Search printers, errors..."
          className="w-full pl-10 p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all"
        />
      </div>
      
      <div className="flex items-center space-x-4">
        <motion.button
          whileHover={{ rotate: 15 }}
          className="p-2 hover:bg-white/10 rounded-xl transition-colors"
          onClick={toggleDarkMode}
        >
          {darkMode ? <Sun className="h-5 w-5 text-yellow-400" /> : <Moon className="h-5 w-5 text-indigo-400" />}
        </motion.button>
        
        <button className="relative p-2 hover:bg-white/10 rounded-xl transition-colors">
          <Bell className="h-5 w-5 text-white" />
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-pulse"></span>
        </button>
        
        <div className="flex items-center space-x-3 p-2 bg-white/10 rounded-xl">
          <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <span className="text-white font-medium">Admin User</span>
        </div>
      </div>
    </header>
  );
};

export default TopNav;
