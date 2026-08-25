import React, { useCallback, useEffect, useState } from 'react';
import { Printer, Plus, RefreshCw, Trash2, Check, Activity, AlertTriangle, HelpCircle } from 'lucide-react';
import { printersAPI, agentAPI } from '../services/api';
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
  last_verified_at?: string | null;
  last_attempt_at?: string | null;
  days_since_update?: number | null;
  seconds_since_verified?: number | null;
  stale?: boolean;
  status_note?: string | null;
  status_detail?: string | null;
  fail_streak?: number;
}

function statusLabel(p: PrinterRow): { text: string; color: string; bg: string } {
  if (p.status_detail === 'unreachable' || (p.stale && p.status === 'unknown')) {
    return { text: p.stale ? 'Stale' : 'Unreachable', color: 'text-zinc-300', bg: 'bg-zinc-500/15' };
  }
  if (p.stale || p.status === 'unknown') {
    return { text: 'Unknown', color: 'text-zinc-300', bg: 'bg-zinc-500/15' };
  }
  if (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)) {
    return { text: 'Low toner', color: 'text-amber-300', bg: 'bg-amber-500/15' };
  }
  if (p.status === 'offline') {
    return { text: 'Offline', color: 'text-red-300', bg: 'bg-red-500/15' };
  }
  if (p.status === 'online' || p.status === 'ok') {
    return { text: 'Online', color: 'text-emerald-300', bg: 'bg-emerald-500/15' };
  }
  return { text: 'Unknown', color: 'text-zinc-300', bg: 'bg-zinc-500/15' };
}

function ageText(p: PrinterRow): string {
  if (p.status_note) return p.status_note;
  if (p.days_since_update == null && !p.last_checked && !p.last_verified_at) {
    return 'Never verified — no poll yet';
  }
  const d = p.days_since_update;
  if (d == null) return 'Status verified';
  if (d < 1 / 1440) return 'Last good read just now';
  if (d < 1 / 24) return `Last good read ${Math.max(1, Math.round(d * 1440))} min ago`;
  if (d < 1) return `Last good read ${Math.round(d * 24)}h ago`;
  if (d < 2) return 'Last good read 1 day ago';
  return `Last good read ${Math.round(d)} days ago`;
}

function tonerColor(level: number | null): string {
  if (level == null) return 'bg-zinc-600';
  if (level <= 20) return 'bg-amber-400';
  if (level <= 40) return 'bg-yellow-400';
  return 'bg-emerald-400';
}

const FleetHome: React.FC<{ darkMode: boolean }> = () => {
  const [printers, setPrinters] = useState<PrinterRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [tonerDraft, setTonerDraft] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);
  const [pollSeconds, setPollSeconds] = useState<number | null>(null);
  const [pollLabel, setPollLabel] = useState('');
  const [allowedIntervals, setAllowedIntervals] = useState<number[]>([]);
  const [pollSaving, setPollSaving] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await printersAPI.list();
      setPrinters(res.data.printers || []);
      setLastRefresh(new Date());
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not load printers');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPollConfig = useCallback(async () => {
    try {
      const res = await agentAPI.getPollConfig();
      setPollSeconds(res.data.poll_interval_seconds);
      setPollLabel(res.data.label || '');
      setAllowedIntervals(res.data.allowed_intervals_seconds || []);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    load();
    loadPollConfig();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load, loadPollConfig]);

  const savePollInterval = async (seconds: number) => {
    setPollSaving(true);
    setError('');
    try {
      const res = await agentAPI.setPollConfig(seconds);
      setPollSeconds(res.data.poll_interval_seconds);
      setPollLabel(res.data.label || '');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not save poll interval (admin only)');
    } finally {
      setPollSaving(false);
    }
  };

  const saveToner = async (id: number) => {
    const n = parseInt(tonerDraft, 10);
    if (Number.isNaN(n) || n < 0 || n > 100) {
      setError('Toner must be 0–100');
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
    try {
      await printersAPI.delete(id);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Delete failed');
    } finally {
      setBusyId(null);
    }
  };

  const online = printers.filter((p) => !p.stale && (p.status === 'online' || p.status === 'ok')).length;
  const lowCount = printers.filter(
    (p) => !p.stale && (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20))
  ).length;
  const staleCount = printers.filter((p) => p.stale || p.status === 'unknown').length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500 mb-1">Fleet</p>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">Printer board</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Live status from your office helper · only printers you list
            {pollLabel ? ` · polls every ${pollLabel}` : ''}
            {lastRefresh ? ` · board refreshed ${lastRefresh.toLocaleTimeString()}` : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={load} className="tt-btn tt-btn-ghost">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <Link to="/helper" className="tt-btn tt-btn-ghost">
            <Activity className="h-4 w-4" /> Helper
          </Link>
          <Link to="/add-printer" className="tt-btn tt-btn-primary">
            <Plus className="h-4 w-4" /> Add printer
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total', value: printers.length, icon: Printer },
          { label: 'Online', value: online, icon: Activity },
          { label: 'Low toner', value: lowCount, icon: AlertTriangle },
          { label: 'Need check', value: staleCount, icon: HelpCircle },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="tt-card px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-500">{label}</span>
              <Icon className="h-3.5 w-3.5 text-zinc-600" />
            </div>
            <p className="text-2xl font-semibold tabular-nums tracking-tight">{loading ? '—' : value}</p>
          </div>
        ))}
      </div>

      {allowedIntervals.length > 0 && (
        <div className="tt-card p-4">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div>
              <p className="text-sm font-medium text-zinc-100">Helper poll frequency</p>
              <p className="text-xs text-zinc-500 mt-0.5">
                How often the PC inside the office checks listed printers and updates this board.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {allowedIntervals.map((s) => (
              <button
                key={s}
                type="button"
                disabled={pollSaving}
                onClick={() => savePollInterval(s)}
                className={`px-3 py-1.5 rounded-lg text-xs border transition ${
                  pollSeconds === s
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-white/10 text-zinc-300 hover:bg-white/5'
                }`}
              >
                {s < 3600 ? `${s / 60} min` : s < 86400 ? `${s / 3600} h` : `${s / 86400} d`}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
          {error}
        </p>
      )}

      {loading && (
        <div className="space-y-2" aria-hidden>
          {[0, 1, 2].map((i) => (
            <div key={i} className="tt-card px-4 py-4 flex gap-3 items-center">
              <div className="tt-skeleton h-9 w-9 rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="tt-skeleton h-3.5 w-40" />
                <div className="tt-skeleton h-2.5 w-56" />
              </div>
              <div className="tt-skeleton h-6 w-16 rounded-full" />
            </div>
          ))}
        </div>
      )}

      {!loading && printers.length === 0 && (
        <div className="tt-card px-8 py-14 text-center">
          <Printer className="h-10 w-10 mx-auto mb-4 text-zinc-600" />
          <p className="text-lg font-medium text-zinc-100 mb-1">No printers yet</p>
          <p className="text-sm text-zinc-500 max-w-sm mx-auto mb-6">
            Add devices your team uses. The office helper will poll only these IPs — nothing else on the network.
          </p>
          <Link to="/add-printer" className="tt-btn tt-btn-primary">
            <Plus className="h-4 w-4" /> Add first printer
          </Link>
        </div>
      )}

      <div className="space-y-2">
        {printers.map((p) => {
          const st = statusLabel(p);
          const isEditing = editingId === p.id;
          return (
            <div
              key={p.id}
              className="tt-card px-4 py-3.5 flex flex-wrap items-center gap-4 hover:border-white/12 transition-colors"
            >
              <div className="flex items-start gap-3 min-w-0 flex-1">
                <div className="h-9 w-9 rounded-lg bg-white/5 flex items-center justify-center shrink-0">
                  <Printer className="h-4 w-4 text-zinc-400" />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-zinc-100 truncate">{p.name}</p>
                  <p className="text-xs text-zinc-500 truncate">
                    {[p.location, p.department].filter(Boolean).join(' · ') || 'No location'}
                    {p.ip_address ? (
                      <>
                        {' · '}
                        <span className="tt-mono text-zinc-400">{p.ip_address}</span>
                      </>
                    ) : (
                      <span className="text-zinc-600"> · No IP</span>
                    )}
                  </p>
                  <p className={`text-xs mt-1 ${p.stale ? 'text-amber-400/90' : 'text-zinc-500'}`}>
                    {ageText(p)}
                    {p.status_detail && p.status_detail !== 'probe_skipped_cloud_disabled'
                      ? ` · ${p.status_detail.replace(/_/g, ' ')}`
                      : ''}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${st.bg} ${st.color}`}>
                  {st.text}
                </span>

                <div className="flex items-center gap-2 min-w-[7rem]">
                  <div className="tt-toner-track" title={p.toner_level != null ? `${p.toner_level}%` : 'No toner data'}>
                    <div
                      className={`tt-toner-fill ${tonerColor(p.toner_level)}`}
                      style={{ width: p.toner_level != null ? `${p.toner_level}%` : '0%' }}
                    />
                  </div>
                  {isEditing ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={tonerDraft}
                        onChange={(e) => setTonerDraft(e.target.value)}
                        className="tt-input w-14 !py-1 !px-2 text-sm"
                        autoFocus
                      />
                      <button
                        type="button"
                        disabled={busyId === p.id}
                        onClick={() => saveToner(p.id)}
                        className="p-1.5 rounded-lg bg-emerald-600 text-white"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(p.id);
                        setTonerDraft(p.toner_level != null ? String(p.toner_level) : '');
                      }}
                      className="text-xs tabular-nums text-zinc-300 hover:text-white"
                    >
                      {p.toner_level != null ? `${p.toner_level}%` : '—'}
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  disabled={busyId === p.id}
                  onClick={() => remove(p.id, p.name)}
                  className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
                  title="Remove"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {printers.length > 0 && printers.length < 5 && (
        <p className="text-xs text-zinc-600 text-center">Free plan · {printers.length}/5 printers</p>
      )}
    </div>
  );
};

export default FleetHome;
