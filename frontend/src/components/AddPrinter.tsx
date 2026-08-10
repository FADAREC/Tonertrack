import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Network, Globe } from 'lucide-react';
import { printersAPI } from '../services/api';

const AddPrinter: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [form, setForm] = useState({
    name: '',
    ip_address: '',
    connection_mode: 'manual',
    snmp_community: 'public',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await printersAPI.add({
        name: form.name || form.ip_address || 'Printer',
        ip_address: form.ip_address || undefined,
        connection_mode: form.connection_mode,
        snmp_community: form.snmp_community,
      });
      setSuccess(true);
      setTimeout(() => (window.location.href = '/'), 1500);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Add failed');
    } finally {
      setLoading(false);
    }
  };

  if (success) return <p>Printer Added!</p>;

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
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        placeholder="Name (required)"
        required
        className="w-full p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all"
      />
      <input
        type="text"
        value={form.ip_address}
        onChange={(e) => setForm({ ...form, ip_address: e.target.value })}
        placeholder="IP Address (optional for manual)"
        className="w-full p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all"
      />
      <div className="relative">
        <Network className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
        <select
          value={form.connection_mode}
          onChange={(e) => setForm({ ...form, connection_mode: e.target.value })}
          className="w-full pl-10 p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white transition-all"
        >
          <option value="manual">Manual</option>
          <option value="web">Web</option>
          <option value="snmp">SNMP</option>
          <option value="ping">Ping</option>
        </select>
        <Globe className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
      </div>
      <input
        type="text"
        value={form.snmp_community}
        onChange={(e) => setForm({ ...form, snmp_community: e.target.value })}
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
