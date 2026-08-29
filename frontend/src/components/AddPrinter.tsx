import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { printersAPI } from '../services/api';
import BrandMark from './BrandMark';
import toast from 'react-hot-toast';

const AddPrinter: React.FC<{ darkMode: boolean }> = () => {
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
      toast.success('Printer added');
      setTimeout(() => {
        window.location.href = '/';
      }, 1200);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Add failed');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <BrandMark size={40} />
        <p className="text-sm text-[#2db84b]">Printer added. Opening the board…</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto space-y-5 pb-16">
      <div className="space-y-3">
        <BrandMark size={28} wordmarkClassName="tt-display text-base tracking-wide" />
        <div>
          <h1 className="tt-display text-2xl tracking-wide">Add printer</h1>
          <p className="text-sm text-[#9aa0a8] mt-1">
            List only devices you want on the board. IP is required for the office checker.
          </p>
        </div>
      </div>

      <div className="tt-card p-4 space-y-3">
        <label className="block space-y-1">
          <span className="text-xs text-[#9aa0a8]">Name</span>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Lobby HP"
            required
            className="tt-input"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-xs text-[#9aa0a8]">IP address</span>
          <input
            type="text"
            value={form.ip_address}
            onChange={(e) => setForm({ ...form, ip_address: e.target.value })}
            placeholder="10.0.0.25"
            className="tt-input tt-lcd"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-xs text-[#9aa0a8]">How it’s listed</span>
          <select
            value={form.connection_mode}
            onChange={(e) => setForm({ ...form, connection_mode: e.target.value })}
            className="tt-input"
          >
            <option value="manual">Manual</option>
            <option value="web">Web</option>
            <option value="snmp">SNMP</option>
            <option value="ping">Ping</option>
          </select>
        </label>
        {form.connection_mode === 'snmp' && (
          <label className="block space-y-1">
            <span className="text-xs text-[#9aa0a8]">SNMP community</span>
            <input
              type="text"
              value={form.snmp_community}
              onChange={(e) => setForm({ ...form, snmp_community: e.target.value })}
              className="tt-input"
            />
          </label>
        )}
        <button type="submit" disabled={loading} className="tt-btn tt-btn-primary w-full">
          <Plus className="h-4 w-4" />
          {loading ? 'Adding…' : 'Add to board'}
        </button>
      </div>

      <Link to="/" className="text-sm text-[#9aa0a8] hover:text-[#e8eaed]">
        ← Back to fleet board
      </Link>
    </form>
  );
};

export default AddPrinter;
