import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Network, Globe } from 'lucide-react';
import { printersAPI } from '../services/api';

const AddPrinterForm: React.FC = () => {
  const [form, setForm] = useState({
    name: '',
    ip_address: '',
    connection_mode: 'manual',
    snmp_community: 'public',
  });
  const [loading, setLoading] = useState(false);

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
      alert('Printer added!');
      window.location.reload();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Add failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/80 backdrop-blur-md rounded-2xl shadow-xl p-6 space-y-4"
    >
      <h3 className="text-lg font-medium text-indigo-900">Add New Printer</h3>
      <input
        type="text"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        placeholder="Name (required)"
        required
        className="w-full p-3 border border-indigo-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white/50 transition-all duration-300"
      />
      <input
        type="text"
        value={form.ip_address}
        onChange={(e) => setForm({ ...form, ip_address: e.target.value })}
        placeholder="IP Address (optional for manual)"
        className="w-full p-3 border border-indigo-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white/50 transition-all duration-300"
      />
      <div className="relative">
        <Network className="absolute left-3 top-1/2 transform -translate-y-1/2 text-indigo-400 h-5 w-5" />
        <select
          value={form.connection_mode}
          onChange={(e) => setForm({ ...form, connection_mode: e.target.value })}
          className="w-full pl-10 p-3 border border-indigo-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white/50 transition-all duration-300"
        >
          <option value="manual">Manual</option>
          <option value="web">Web</option>
          <option value="snmp">SNMP</option>
          <option value="ping">Ping</option>
        </select>
        <Globe className="absolute right-3 top-1/2 transform -translate-y-1/2 text-indigo-400 h-5 w-5" />
      </div>
      <input
        type="text"
        value={form.snmp_community}
        onChange={(e) => setForm({ ...form, snmp_community: e.target.value })}
        placeholder="SNMP Community (default: public)"
        className="w-full p-3 border border-indigo-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white/50 transition-all duration-300"
      />
      <motion.button
        type="submit"
        whileHover={{ scale: 1.02 }}
        disabled={loading}
        className="w-full bg-indigo-600 text-white p-3 rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50"
      >
        <Plus className="inline h-5 w-5 mr-2" />
        {loading ? 'Adding...' : 'Add Printer'}
      </motion.button>
    </motion.form>
  );
};

export default AddPrinterForm;
