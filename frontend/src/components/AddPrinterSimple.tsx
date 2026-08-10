import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { printersAPI } from '../services/api';

const AddPrinterSimple: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [department, setDepartment] = useState('');
  const [ip, setIp] = useState('');
  const [toner, setToner] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const panel = darkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const tonerVal = toner.trim() === '' ? null : Math.min(100, Math.max(0, parseInt(toner, 10)));
      await printersAPI.add({
        name: name.trim(),
        location: location.trim() || undefined,
        department: department.trim() || undefined,
        ip_address: ip.trim() || undefined,
        connection_mode: 'manual',
        toner_level: Number.isFinite(tonerVal as number) ? (tonerVal as number) : null,
      });
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not add printer');
    } finally {
      setLoading(false);
    }
  };

  const inputCls = `w-full p-3 rounded-xl border ${
    darkMode ? 'bg-gray-900 border-gray-600 text-white' : 'bg-white border-gray-300'
  }`;

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Add printer</h1>
      <p className={`text-sm mb-6 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
        Manual entry — nothing on your network is contacted.
      </p>
      <form onSubmit={submit} className={`rounded-2xl border p-6 space-y-4 ${panel}`}>
        <div>
          <label className="text-sm opacity-70">Name *</label>
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Front desk HP" required />
        </div>
        <div>
          <label className="text-sm opacity-70">Location</label>
          <input className={inputCls} value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Ground floor" />
        </div>
        <div>
          <label className="text-sm opacity-70">Department</label>
          <input className={inputCls} value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="e.g. Accounts" />
        </div>
        <div>
          <label className="text-sm opacity-70">IP address (optional)</label>
          <input className={inputCls} value={ip} onChange={(e) => setIp(e.target.value)} placeholder="For your records only in manual mode" />
        </div>
        <div>
          <label className="text-sm opacity-70">Toner level % (optional)</label>
          <input
            className={inputCls}
            type="number"
            min={0}
            max={100}
            value={toner}
            onChange={(e) => setToner(e.target.value)}
            placeholder="Leave blank if unknown"
          />
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? 'Saving…' : 'Save printer'}
        </button>
      </form>
    </div>
  );
};

export default AddPrinterSimple;
