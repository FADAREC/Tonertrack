// frontend/src/components/ScanButton.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search as SearchIcon } from 'lucide-react';
import { printersAPI } from '../services/api';

const ScanButton: React.FC = () => {
  const [subnet, setSubnet] = useState('192.168.1.0/24');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleScan = async () => {
    setLoading(true);
    try {
      const res = await printersAPI.scan(subnet);
      setResult(res.data);
      window.location.reload();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Scan failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/80 backdrop-blur-md rounded-2xl shadow-xl p-6"
    >
      <h3 className="text-lg font-medium text-indigo-900 mb-4">Network Scan</h3>
      <div className="relative mb-4">
        <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-indigo-400 h-5 w-5" />
        <input
          type="text"
          value={subnet}
          onChange={(e) => setSubnet(e.target.value)}
          placeholder="Subnet (e.g., 192.168.1.0/24)"
          className="w-full pl-10 p-3 border border-indigo-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white/50 transition-all duration-300"
        />
      </div>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleScan}
        disabled={loading}
        className="w-full bg-gradient-to-r from-indigo-500 to-blue-500 text-white p-3 rounded-xl hover:from-indigo-600 hover:to-blue-600 disabled:opacity-50 transition-all duration-300 shadow-md"
      >
        {loading ? 'Scanning...' : 'Start Scan'}
      </motion.button>
      {result && (
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 text-sm text-green-600 text-center"
        >
          Discovered {result.discovered} printers
        </motion.p>
      )}
    </motion.div>
  );
};

export default ScanButton;