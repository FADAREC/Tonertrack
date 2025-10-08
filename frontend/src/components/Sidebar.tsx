import React from 'react';
import { motion } from 'framer-motion';
import { LayoutDashboard, Printer, Settings, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';  // Fixed: Added Link for routing

const Sidebar: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Printer, label: 'Printers', path: '/printers' },
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
      className="w-64 bg-white/5 backdrop-blur-lg shadow-2xl rounded-r-3xl p-6 flex flex-col justify-between border-r border-white/10"
    >
      <div>
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-8">
          PrintHub
        </h1>
        <nav className="space-y-2">
          {menuItems.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                to={item.path}
                className="flex items-center p-3 rounded-xl text-white/70 hover:text-white hover:bg-white/10 transition-all duration-300"
              >
                <item.icon className="h-5 w-5 mr-3" />
                {item.label}
              </Link>
            </motion.div>
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
