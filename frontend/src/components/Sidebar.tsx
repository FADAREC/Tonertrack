import React from 'react';
import { motion } from 'framer-motion';
import { LayoutDashboard, Printer, Settings, LogOut } from 'lucide-react'; // Fixed: Removed unused ChevronLeft

const Sidebar: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Printer, label: 'Printers', path: '/printers' },
    {icon: Printer, label: 'Add a new Printer', path: '/add-printer'},
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.reload();
  };

  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.3 }}
      className="w-64 bg-white/5 backdrop-blur-lg shadow-2xl rounded-r-3xl p-6 flex flex-col justify-between border-r border-white/10"
    >
      <div>
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-8">
          PrintHub
        </h1>
        <nav className="space-y-2">
          {menuItems.map((item, index) => (
            <motion.a
              key={item.label}
              href={item.path}
              whileHover={{ x: 5 }}
              className="flex items-center p-3 rounded-xl dark:text-white/70 hover:dark:text-white hover:bg-white/10 transition-all duration-300"
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.label}
            </motion.a>
          ))}
        </nav>
      </div>
      <motion.button
        onClick={handleLogout}
        whileHover={{ scale: 1.02 }}
        className="flex items-center p-3 rounded-xl text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all duration-300"
      >
        <LogOut className="h-5 w-5 mr-3" />
        Logout
      </motion.button>
    </motion.aside>
  );
};

export default Sidebar;