import React from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, LogOut } from 'lucide-react';

const Settings: React.FC<{ darkMode: boolean; toggleDarkMode: () => void }> = ({ darkMode, toggleDarkMode }) => {
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.reload();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
    >
      <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
      <p className="text-white/70 mb-6">Customize your experience.</p>
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
        <motion.button
          onClick={handleLogout}
          whileHover={{ scale: 1.02 }}
          className="w-full flex items-center justify-center space-x-2 p-3 bg-red-500/20 text-red-300 rounded-xl hover:bg-red-500/30 transition-all duration-300"
        >
          <LogOut className="h-5 w-5" />
          <span>Logout</span>
        </motion.button>
      </div>
    </motion.div>
  );
};

export default Settings;