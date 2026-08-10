import React, { useEffect, useState } from 'react';
import { Printer, Plus, RefreshCw, Trash2, Check } from 'lucide-react';
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
  last_checked?: string | null;
  days_since_update?: number | null;
  stale?: boolean;
}

function statusLabel(p: PrinterRow): { text: string; color: string; bg: string } {
  if (p.stale || p.status === 'unknown') {
    return { text: 'Unknown / stale', color: 'text-gray-400', bg: 'bg-gray-500/15' };
  }
  if (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)) {
    return { text: 'Low toner', color: 'text-amber-400', bg: 'bg-amber-500/15' };
  }
  if (p.status === 'offline') {
    return { text: 'Offline', color: 'text-red-400', bg: 'bg-red-500/15' };
  }
  if (p.status === 'online' || p.status === 'ok') {
    return { text: 'OK', color: 'text-green-400', bg: 'bg-green-500/15' };
  }
  return { text: 'Unknown', color: 'text-gray-400', bg: 'bg-gray-500/15' };
}

function ageText(p: PrinterRow): string {
  if (p.days_since_update == null && !p.last_checked) return 'Never updated';
  const d = p.days_since_update;
  if (d == null) return 'Updated';
  if (d < 0.04) return 'Updated just now';
  if (d < 1) return `Updated ${Math.round(d * 24)}h ago`;
  if (d < 2) return 'Updated 1 day ago';
  return `Updated ${Math.round(d)} days ago`;
}

const FleetHome: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [printers, setPrinters] = useState<PrinterRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [tonerDraft, setTonerDraft] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);

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

  const saveToner = async (id: number) => {
    const n = parseInt(tonerDraft, 10);
    if (Number.isNaN(n) || n < 0 || n > 100) {
      setError('Toner must be a number from 0 to 100');
      return;
    }
    setBusyId(id);
    setError('');
    try {
      await printersAPI.update(id, { toner_level: n });
      setEditingId(null);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Update failed');
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (id: number, name: string) => {
    if (!window.confirm(`Remove “${name}” from the fleet?`)) return;
    setBusyId(id);
    setError('');
    try {
      await printersAPI.delete(id);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Delete failed');
    } finally {
      setBusyId(null);
    }
  };

  const lowCount = printers.filter(
    (p) => !p.stale && (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20))
  ).length;
  const staleCount = printers.filter((p) => p.stale || p.status === 'unknown').length;

  const panel = darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200 shadow-sm';
  const muted = darkMode ? 'text-gray-400' : 'text-gray-500';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Fleet</h1>
          <p className={`text-sm ${muted}`}>
            {printers.length} printer{printers.length === 1 ? '' : 's'}
            {printers.length > 0 && printers.length < 5 && ` · free plan ${printers.length}/5`}
            {printers.length >= 5 && ` · free plan full (5/5)`}
            {lowCount > 0 && ` · ${lowCount} low toner`}
            {staleCount > 0 && ` · ${staleCount} need update`}
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

      {error && (
        <p className="text-red-300 text-sm bg-red-500/10 border border-red-400/30 rounded-xl p-3">{error}</p>
      )}
      {loading && <p className={muted}>Loading…</p>}

      {!loading && printers.length === 0 && (
        <div className={`rounded-xl border p-10 text-center ${panel}`}>
          <Printer className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="font-medium mb-1">No printers yet</p>
          <p className={`text-sm mb-4 ${muted}`}>
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
          const isEditing = editingId === p.id;
          return (
            <div
              key={p.id}
              className={`rounded-xl border p-4 flex flex-wrap items-center justify-between gap-3 ${panel}`}
            >
              <div className="flex items-start gap-3 min-w-0 flex-1">
                <Printer className="h-5 w-5 mt-0.5 shrink-0 opacity-70" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{p.name}</p>
                  <p className={`text-xs ${muted}`}>
                    {[p.location, p.department, p.ip_address].filter(Boolean).join(' · ') || 'No location'}
                    {' · '}
                    {p.connection_mode === 'manual' ? 'Manual' : p.connection_mode.toUpperCase()}
                  </p>
                  <p className={`text-xs mt-0.5 ${p.stale ? 'text-amber-500/90' : muted}`}>{ageText(p)}</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${st.bg} ${st.color}`}>
                  {st.text}
                </span>

                {isEditing ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={tonerDraft}
                      onChange={(e) => setTonerDraft(e.target.value)}
                      className={`w-16 px-2 py-1 rounded border text-sm ${darkMode ? 'bg-gray-900 border-gray-600' : 'bg-white border-gray-300'}`}
                      placeholder="%"
                      autoFocus
                    />
                    <button
                      type="button"
                      disabled={busyId === p.id}
                      onClick={() => saveToner(p.id)}
                      className="p-1.5 rounded bg-green-600 text-white"
                      title="Save"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className={`text-xs px-2 ${muted}`}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(p.id);
                      setTonerDraft(p.toner_level != null ? String(p.toner_level) : '');
                    }}
                    className={`text-sm px-2 py-1 rounded border ${darkMode ? 'border-gray-600' : 'border-gray-300'}`}
                    title="Update toner"
                  >
                    {p.toner_level != null ? `${p.toner_level}%` : 'Set toner'}
                  </button>
                )}

                <button
                  type="button"
                  disabled={busyId === p.id}
                  onClick={() => remove(p.id, p.name)}
                  className="p-1.5 rounded text-red-400/80 hover:bg-red-500/10"
                  title="Remove"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FleetHome;
