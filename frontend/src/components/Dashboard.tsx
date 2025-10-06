import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Printer, AlertTriangle, Droplet } from 'lucide-react'; // Fixed: Removed unused Activity, Settings
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { printersAPI } from '../services/api';

interface Printer {
  id: number;
  ip: string;
  model?: string;
  toner_levels: { [key: string]: number };
  errors: string[];
  connection_mode: string;
}

const Dashboard: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [loading, setLoading] = useState(true);
  // Fixed: Removed unused activeTab/setActiveTab

  useEffect(() => {
    fetchPrinters();
  }, []);

  const fetchPrinters = async () => {
    try {
      const res = await printersAPI.list();
      const printersWithStatus = await Promise.all(
        res.data.printers.map(async (p: Printer) => ({
          ...p,
          ...(await printersAPI.status(p.id).catch(() => ({}))),
        }))
      );
      setPrinters(printersWithStatus);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Stats
  const totalPrinters = printers.length;
  const lowToner = printers.filter(p => Object.values(p.toner_levels).some(level => level < 20)).length;
  const withErrors = printers.filter(p => p.errors.length > 0).length;

  // Chart data
  const lineData = [
    { name: 'Mon', uv: 4000, pv: 2400 },
    { name: 'Tue', uv: 3000, pv: 1398 },
    { name: 'Wed', uv: 2000, pv: 9800 },
    { name: 'Thu', uv: 2780, pv: 3908 },
    { name: 'Fri', uv: 1890, pv: 4800 },
    { name: 'Sat', uv: 2390, pv: 3800 },
    { name: 'Sun', uv: 3490, pv: 4300 },
  ];

  const barData = [
    { name: 'Black', value: 70 },
    { name: 'Cyan', value: 85 },
    { name: 'Magenta', value: 60 },
    { name: 'Yellow', value: 90 },
  ];

  const COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B'];

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div></div>;

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-8"
    >
      {/* Hero Section */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Dashboard Overview
        </h1>
        <p className="text-white/70 mt-2">Monitor your printers in real-time</p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard icon={Printer} title="Total Printers" value={totalPrinters} color="from-blue-500 to-blue-600" />
        <StatCard icon={Droplet} title="Low Toner Alerts" value={lowToner} color="from-yellow-500 to-yellow-600" />
        <StatCard icon={AlertTriangle} title="Active Errors" value={withErrors} color="from-red-500 to-red-600" />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Toner Usage Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={lineData}>
              <XAxis dataKey="name" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ background: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '8px' }} />
              <Line type="monotone" dataKey="uv" stroke="#3B82F6" strokeWidth={3} dot={{ fill: '#3B82F6', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Color Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <XAxis dataKey="name" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ background: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '8px' }} />
              <Bar dataKey="value">
                {barData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Printers Grid */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-4"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Printers</h2>
          <div className="flex space-x-2">
            <button className="px-4 py-2 bg-white/10 rounded-xl text-white hover:bg-white/20 transition-colors">Grid</button>
            <button className="px-4 py-2 bg-white/10 rounded-xl text-white hover:bg-white/20 transition-colors">List</button>
          </div>
        </div>
        <AnimatePresence>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {printers.map((printer, index) => (
              <PrinterCard key={printer.id} printer={printer} index={index} darkMode={darkMode} />
            ))}
          </div>
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
};

// StatCard and PrinterCard remain the same as in previous response (no changes needed)
interface StatCardProps {
  icon: React.FC<{ className?: string }>;
  title: string;
  value: number;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon: Icon, title, value, color }) => (
  <motion.div 
    whileHover={{ y: -5, scale: 1.02 }}
    className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 cursor-pointer"
  >
    <div className={`p-3 rounded-xl ${color} text-white mb-4`}>
      <Icon className="h-6 w-6" />
    </div>
    <h3 className="text-sm text-white/70 font-medium">{title}</h3>
    <p className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
      {value}
    </p>
  </motion.div>
);

interface PrinterCardProps {
  printer: Printer;
  index: number;
  darkMode: boolean;
}

const PrinterCard: React.FC<PrinterCardProps> = ({ printer, index }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.05, type: 'spring' }}
    className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 group"
  >
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-white">{printer.model || 'Unknown'}</h3>
      <div className={`px-2 py-1 rounded-full text-xs font-medium ${printer.connection_mode === 'web' ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'}`}>
        {printer.connection_mode.toUpperCase()}
      </div>
    </div>
    <p className="text-white/70 text-sm mb-4">{printer.ip}</p>
    
    <div className="space-y-3 mb-4">
      {Object.entries(printer.toner_levels).map(([color, level]) => (
        <div key={color} className="flex items-center space-x-2">
          <div className={`h-2 w-2 rounded-full bg-${color}-400`}></div>
          <span className="text-white/70 text-sm capitalize">{color}</span>
          <div className="flex-1 bg-white/10 rounded-full h-1.5 overflow-hidden">
            <motion.div 
              className="h-1.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${level}%` }}
              transition={{ duration: 0.8 }}
            />
          </div>
          <span className="text-white font-medium">{level}%</span>
        </div>
      ))}
    </div>

    {printer.errors.length > 0 && (
      <div className="mb-4">
        <div className="flex items-center space-x-2 text-red-400 mb-2">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-sm font-medium">Errors</span>
        </div>
        <ul className="space-y-1">
          {printer.errors.map((err, i) => (
            <li key={i} className="text-white/70 text-sm flex items-center">
              <AlertTriangle className="h-3 w-3 mr-2" />
              {err}
            </li>
          ))}
        </ul>
      </div>
    )}

    <div className="flex space-x-3 pt-4 border-t border-white/10">
      <motion.button
        whileHover={{ scale: 1.05 }}
        className="flex-1 bg-red-500/20 text-red-300 py-2 rounded-xl hover:bg-red-500/30 transition-all duration-300"
      >
        Delete
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.05 }}
        className="flex-1 bg-blue-500/20 text-blue-300 py-2 rounded-xl hover:bg-blue-500/30 transition-all duration-300"
      >
        Refresh
      </motion.button>
    </div>
  </motion.div>
);

export default Dashboard;