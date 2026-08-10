import React, { useEffect, useState } from 'react';
import { Printer, AlertTriangle, Plus, RefreshCw } from 'lucide-react';
import { printersAPI } from '../services/api';
import { Link } from 'react-router-dom';

interface PrinterRow {
  id: number;
  name: string;
  ip_address?: string;
  location?: string;
  department?: string;
  status: string;
  toner_level: number | null;
  connection_mode: string;
}

function statusLabel(p: PrinterRow): { text: string; color: string } {
  if (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)) {
    return { text: 'Low toner', color: 'text-amber-500' };
  }
  if (p.status === 'offline') return { text: 'Offline', color: 'text-red-500' };
  if (p.status === 'online') return { text: 'OK', color: 'text-green-500' };
  return { text: 'Unknown', color: 'text-gray-400' };
}

function tonerText(level: number | null | undefined): string {
  if (level == null) return 'Unknown';
  return `${level}%`;
}

const FleetHome: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [printers, setPrinters] = useState<PrinterRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await printersAPI.list();
      setPrinters(res.data.printers || []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not load printers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const lowCount = printers.filter(
    (p) => p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)
  ).length;
  const unknownCount = printers.filter((p) => p.status === 'unknown' || p.toner_level == null).length;

  const panel = darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200 shadow-sm';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Fleet</h1>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            {printers.length} printer{printers.length === 1 ? '' : 's'}
            {lowCount > 0 && ` · ${lowCount} low toner`}
            {unknownCount > 0 && ` · ${unknownCount} unknown`}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={load}
            className={`px-3 py-2 rounded-lg border text-sm flex items-center gap-2 ${darkMode ? 'border-gray-600' : 'border-gray-300'}`}
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <Link
            to="/add-printer"
            className="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm flex items-center gap-2 hover:bg-blue-500"
          >
            <Plus className="h-4 w-4" /> Add printer
          </Link>
        </div>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
      {loading && <p className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Loading…</p>}

      {!loading && printers.length === 0 && (
        <div className={`rounded-xl border p-10 text-center ${panel}`}>
          <Printer className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="font-medium mb-1">No printers yet</p>
          <p className={`text-sm mb-4 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Add your first printer. Manual mode does not contact your network.
          </p>
          <Link to="/add-printer" className="text-blue-500 font-medium text-sm">
            Add printer →
          </Link>
        </div>
      )}

      <div className="grid gap-3">
        {printers.map((p) => {
          const st = statusLabel(p);
          return (
            <div
              key={p.id}
              className={`rounded-xl border p-4 flex flex-wrap items-center justify-between gap-3 ${panel}`}
            >
              <div className="flex items-start gap-3 min-w-0">
                <Printer className="h-5 w-5 mt-0.5 shrink-0 opacity-70" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{p.name}</p>
                  <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {[p.location, p.department, p.ip_address].filter(Boolean).join(' · ') || 'No location'}
                    {' · '}
                    {p.connection_mode === 'manual' ? 'Manual' : p.connection_mode.toUpperCase()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className={st.color}>
                  {(p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)) && (
                    <AlertTriangle className="inline h-4 w-4 mr-1" />
                  )}
                  {st.text}
                </span>
                <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>
                  Toner {tonerText(p.toner_level)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FleetHome;
