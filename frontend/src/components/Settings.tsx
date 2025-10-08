import React from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon } from 'lucide-react'; // Fixed: Alias import to avoid conflict

const Settings: React.FC<{ darkMode: boolean; toggleDarkMode: () => void }> = ({ darkMode, toggleDarkMode }) => { 
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
    >
      <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
      <p className="text-white/70 mb-6">Customize your Printer Management experience.</p>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-white/10 rounded-xl">
          <span className="text-white">Dark Mode</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" checked={darkMode} onChange={toggleDarkMode} className="sr-only" />
            <div className="w-11 h-6 bg-white/20 rounded-full peer dark:bg-white/20">
              <div className="w-5 h-5 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
            </div>
          </label>
        </div>
        {/* Add more settings like notifications, etc. */}
      </div>
    </motion.div>
  );
};

export default Settings;
