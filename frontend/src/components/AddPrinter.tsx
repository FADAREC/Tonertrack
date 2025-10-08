import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Network, Globe } from 'lucide-react';
import { printersAPI } from '../services/api';

const AddPrinter: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [form, setForm] = useState({ ip: '', model: '', connection_mode: 'web', snmp_community: 'public' });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await printersAPI.add(form);
      setSuccess(true);
      setTimeout(() => window.location.href = '/printers', 1500); // Redirect to list
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Add failed');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center py-12 bg-white/5 rounded-2xl"
      >
        <Plus className="mx-auto h-16 w-16 text-green-400 mb-4 animate-bounce" />
        <h3 className="text-xl font-semibold text-white mb-2">Printer Added!</h3>
        <p className="text-white/70">Redirecting to your printers...</p>
      </motion.div>
    );
  }

  return (
    <motion.form 
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 space-y-4 max-w-md mx-auto"
    >
      <h2 className="text-2xl font-bold text-white text-center">Add New Printer</h2>
      <input
        type="text"
        value={form.ip}
        onChange={(e) => setForm({...form, ip: e.target.value})}
        placeholder="IP Address (required)"
        required
        className="w-full p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all"
      />
      <input
        type="text"
        value={form.model}
        onChange={(e) => setForm({...form, model: e.target.value})}
        placeholder="Model (optional)"
        className="w-full p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all"
      />
      <div className="relative">
        <Network className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
        <select
          value={form.connection_mode}
          onChange={(e) => setForm({...form, connection_mode: e.target.value})}
          className="w-full pl-10 p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white transition-all"
        >
          <option value="web">Web</option>
          <option value="snmp">SNMP</option>
        </select>
        <Globe className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
      </div>
      <input
        type="text"
        value={form.snmp_community}
        onChange={(e) => setForm({...form, snmp_community: e.target.value})}
        placeholder="SNMP Community (default: public)"
        className="w-full p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all"
      />
      <motion.button
        type="submit"
        whileHover={{ scale: 1.02 }}
        disabled={loading}
        className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50"
      >
        <Plus className="inline h-5 w-5 mr-2" />
        {loading ? 'Adding...' : 'Add Printer'}
      </motion.button>
    </motion.form>
  );
};

export default AddPrinter;