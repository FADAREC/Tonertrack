import React, { useCallback, useEffect, useState } from 'react';
import { Printer, Plus, RefreshCw, Trash2, Check, Activity, AlertTriangle, HelpCircle } from 'lucide-react';
import { printersAPI, agentAPI } from '../services/api';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

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

function statusLabel(p: PrinterRow): { text: string; kind: string } {
  if (p.status === 'offline') return { text: 'Offline', kind: 'crit' };
  if (p.stale) return { text: 'Needs check', kind: 'warn' };
  if (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)) {
    return { text: 'Low toner', kind: 'warn' };
  }
  if (p.status === 'online' || p.status === 'ok') {
    return { text: 'Verified', kind: 'ok' };
  }
  return { text: 'Unknown', kind: 'muted' };
}


function ageText(p: PrinterRow): string {
  if (p.status_note) return p.status_note;
  if (p.days_since_update == null && !p.last_checked && !p.last_verified_at) {
    return 'Not checked yet';
  }
  const d = p.days_since_update;
  if (d == null) return 'Checked';
  if (d < 1 / 1440) return 'Checked just now';
  if (d < 1 / 24) return `Checked ${Math.max(1, Math.round(d * 1440))} min ago`;
  if (d < 1) return `Checked ${Math.round(d * 24)}h ago`;
  if (d < 2) return 'Checked 1 day ago';
  return `Checked ${Math.round(d)} days ago`;
}

function cmykLevels(p: PrinterRow): { c: number | null; m: number | null; y: number | null; k: number | null } {
  // Single reported level maps to K until multi-cartridge data exists
  const k = p.toner_level;
  return { c: null, m: null, y: null, k };
}


function rowTone(p: PrinterRow): string {
  if (p.status === 'offline') return 'tt-card-critical';
  if (!p.stale && (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20))) return 'tt-card-attention';
  if (p.stale || p.status === 'unknown') return 'tt-card-stale';
  if (!p.stale && (p.status === 'online' || p.status === 'ok')) return 'tt-card-live';
  return '';
}

function CmykBars({ p }: { p: PrinterRow }) {
  const levels = cmykLevels(p);
  const rows: { key: 'c' | 'm' | 'y' | 'k'; label: string; cls: string }[] = [
    { key: 'c', label: 'C', cls: 'c' },
    { key: 'm', label: 'M', cls: 'm' },
    { key: 'y', label: 'Y', cls: 'y' },
    { key: 'k', label: 'K', cls: 'k' },
  ];
  return (
    <div className="tt-cmyk" title={p.toner_level != null ? `Black ${p.toner_level}% (reported)` : 'No toner reading'}>
      {rows.map((r) => {
        const v = levels[r.key];
        return (
          <div key={r.key} className="tt-cmyk-row">
            <span className="tt-cmyk-label">{r.label}</span>
            <div className="tt-cmyk-track">
              <div
                className={`tt-cmyk-fill ${r.cls}`}
                style={{
                  width: v != null ? `${Math.max(0, Math.min(100, v))}%` : '0%',
                  opacity: v != null ? 1 : 0.25,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
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
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [checksById, setChecksById] = useState<Record<number, any[]>>({});
  const [checksLoading, setChecksLoading] = useState<number | null>(null);

  const load = useCallback(async (opts?: { quiet?: boolean }) => {
    const quiet = !!opts?.quiet;
    if (!quiet) {
      setLoading(true);
      setError('');
    }
    try {
      const res = await printersAPI.list();
      setPrinters(res.data.printers || []);
      setLastRefresh(new Date());
    } catch (e: any) {
      if (!quiet) setError(e?.response?.data?.detail || 'Could not load printers');
    } finally {
      if (!quiet) setLoading(false);
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
    const id = setInterval(() => load({ quiet: true }), 60000);
    return () => clearInterval(id);
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
      setError('Toner must be 0-100');
      return;
    }
    setBusyId(id);
    setError('');
    try {
      await printersAPI.update(id, { toner_level: n });
      setEditingId(null);
      toast.success('Toner updated');
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
      toast.success('Printer removed');
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
  // Goal 1: operational freshness = checked within 2x poll interval (default 30 min if unknown)
  const freshWindowSec = Math.max(1800, (pollSeconds || 900) * 2);
  const freshCount = printers.filter((p) => {
    if (p.seconds_since_verified == null) return false;
    return p.seconds_since_verified <= freshWindowSec;
  }).length;
  const freshnessPct = printers.length ? Math.round((100 * freshCount) / printers.length) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-5 sm:space-y-6 pb-24 md:pb-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs text-[#8b9bb8] mb-1">Fleet</p>
          <h1 className="text-2xl font-semibold tracking-tight text-[#f2f5ff]">Printer board</h1>
          <p className="text-sm text-[#8b9bb8] mt-1">
            Shared view for your team · only printers you add
            {pollLabel ? ` · polls every ${pollLabel}` : ''}
            {lastRefresh ? ` · refreshed ${lastRefresh.toLocaleTimeString()}` : ''}
          </p>
        </div>
        <div className="hidden sm:flex gap-2">
          <button type="button" onClick={() => load()} className="tt-btn tt-btn-ghost">
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

      {/* Goal 1 path: get printers listed and checks running */}
      {!loading && (
        <div className="tt-card px-4 py-3 space-y-2">
          <p className="text-sm font-medium text-[#f2f5ff]">Get the board useful for support</p>
          <ul className="text-xs text-[#8b9bb8] space-y-1">
            <li>{printers.length > 0 ? 'Done' : 'Next'}: Add the printers on this floor (with network addresses).</li>
            <li>{freshCount > 0 ? 'Done' : 'Next'}: Run the office checker so status stays current.</li>
            <li>Support opens this board first when a printer problem is reported.</li>
          </ul>
          <div className="flex flex-wrap gap-2 pt-1">
            {printers.length === 0 && (
              <Link to="/add-printer" className="tt-btn tt-btn-primary text-xs">Add printers</Link>
            )}
            {printers.length > 0 && freshCount === 0 && (
              <Link to="/helper" className="tt-btn tt-btn-primary text-xs">Set up office checker</Link>
            )}
          </div>
        </div>
      )}

      {/* Glance strip — quiet when healthy */}
      {!loading && (lowCount > 0 || staleCount > 0) && (
        <div
          className="tt-card px-4 py-3 flex flex-wrap items-center gap-3"
          style={{ borderColor: lowCount > 0 ? 'rgba(255,46,58,0.45)' : 'rgba(255,177,74,0.4)' }}
          role="status"
        >
          <span
            className={`tt-status-dot ${lowCount > 0 ? 'tt-status-dot-danger' : ''}`}
            style={lowCount === 0 ? { background: '#ffb14a' } : undefined}
          />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-[#f2f5ff]">
              {lowCount > 0 && staleCount > 0
                ? `${lowCount} low toner · ${staleCount} need a check`
                : lowCount > 0
                  ? `${lowCount} printer${lowCount === 1 ? '' : 's'} low on toner`
                  : `${staleCount} printer${staleCount === 1 ? '' : 's'} need a fresh check`}
            </p>
            <p className="text-xs text-[#8b9bb8] mt-0.5">
              This bar only shows when something needs attention. If everything is fine, it stays hidden.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total', value: printers.length, icon: Printer, kind: 'plain' as const },
          {
            label: 'Checked on time',
            value: loading ? '…' : `${freshCount}/${printers.length || 0}`,
            icon: Activity,
            kind: printers.length && freshnessPct >= 90 ? 'live' : printers.length ? 'warn' : 'plain',
          },
          { label: 'Low toner', value: lowCount, icon: AlertTriangle, kind: lowCount > 0 ? 'warn' : 'plain' },
          { label: 'Needs check', value: staleCount, icon: HelpCircle, kind: staleCount > 0 ? 'warn' : 'plain' },
        ].map(({ label, value, icon: Icon, kind }) => (
          <div
            key={label}
            className={`tt-card px-4 py-3 ${
              kind === 'danger' ? 'tt-card-critical' : kind === 'warn' ? 'tt-card-attention' : kind === 'live' ? 'tt-card-live' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#8b9bb8]">{label}</span>
              <Icon className="h-3.5 w-3.5 text-[#8b9bb8]" />
            </div>
            <p className="tt-lcd text-2xl">{loading ? '…' : value}</p>
          </div>
        ))}
      </div>
      {!loading && printers.length > 0 && (
        <p className="text-xs text-[#8b9bb8]">
          Goal 1 target: at least 90% checked on time during work hours. Now {freshnessPct}%.
        </p>
      )}

      {allowedIntervals.length > 0 && (
        <div className="tt-card p-4">
          <p className="text-sm font-medium text-[#f2f5ff]">How often to check printers</p>
          <p className="text-xs text-[#8b9bb8] mt-0.5 mb-3">
            How often the office computer should check the printers you added.
          </p>
          <div className="flex flex-wrap gap-2">
            {allowedIntervals.map((s) => (
              <button
                key={s}
                type="button"
                disabled={pollSaving}
                onClick={() => savePollInterval(s)}
                className={`px-3 py-2 rounded-lg text-xs border min-h-[40px] transition ${
                  pollSeconds === s
                    ? 'bg-[#39ff88] text-[#0b132b] border-[#39ff88]'
                    : 'border-white/10 text-[#f2f5ff] hover:bg-white/5'
                }`}
              >
                {s < 3600 ? `${s / 60} min` : s < 86400 ? `${s / 3600} h` : `${s / 86400} d`}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">{error}</p>
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
            </div>
          ))}
        </div>
      )}

      {!loading && printers.length === 0 && (
        <div className="tt-card px-8 py-14 text-center">
          <Printer className="h-10 w-10 mx-auto mb-4 text-[#5c6b86]" />
          <p className="text-lg font-medium text-[#f2f5ff] mb-1">No printers yet</p>
          <p className="text-sm text-[#8b9bb8] max-w-sm mx-auto mb-6">
            Add the printers your team uses. The office program only checks the ones you add.
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            <Link to="/add-printer" className="tt-btn tt-btn-primary">
              <Plus className="h-4 w-4" /> Add first printer
            </Link>
            <Link to="/helper" className="tt-btn tt-btn-ghost">
              Set up office computer
            </Link>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {printers.map((p) => {
          const st = statusLabel(p);
          const isEditing = editingId === p.id;
          const open = expandedId === p.id;
          return (
            <div key={p.id} className={`tt-card overflow-hidden ${rowTone(p)}`}>
              <div
                role="button"
                tabIndex={0}
                onClick={async () => {
                  if (open) {
                    setExpandedId(null);
                    return;
                  }
                  setExpandedId(p.id);
                  if (!checksById[p.id]) {
                    setChecksLoading(p.id);
                    try {
                      const res = await printersAPI.checks(p.id, 8);
                      setChecksById((prev) => ({ ...prev, [p.id]: res.data.checks || [] }));
                    } catch {
                      setChecksById((prev) => ({ ...prev, [p.id]: [] }));
                    } finally {
                      setChecksLoading(null);
                    }
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setExpandedId(open ? null : p.id);
                  }
                }}
                className="px-4 py-3.5 sm:py-4 flex flex-wrap items-center gap-3 sm:gap-4 cursor-pointer"
              >
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <div className="h-9 w-9 rounded-lg bg-white/5 flex items-center justify-center shrink-0">
                    <Printer className="h-4 w-4 text-[#8b9bb8]" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-[#f2f5ff] truncate">{p.name}</p>
                    <p className="text-xs text-[#8b9bb8] truncate">
                      {[p.location, p.department].filter(Boolean).join(' · ') || 'No location'}
                      {p.ip_address ? (
                        <>
                          {' · '}
                          <span className="tt-mono">{p.ip_address}</span>
                        </>
                      ) : (
                        <span className="text-[#5c6b86]"> · No IP</span>
                      )}
                    </p>
                    <p className={`text-xs mt-1 ${p.stale ? 'text-[#ffb14a]' : 'text-[#8b9bb8]'}`}>{ageText(p)}</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <span
                    className={`tt-status-pill tt-status-${st.kind}`}
                  >
                    {(p.status === 'online' || p.status === 'ok') && !p.stale && (
                      <span className="tt-status-dot tt-status-dot-online" aria-hidden />
                    )}
                    {!p.stale && (p.status === 'low' || (p.toner_level != null && p.toner_level <= 20)) && (
                      <span className="tt-status-dot tt-status-dot-danger" aria-hidden />
                    )}
                    {st.text}
                  </span>

                  <div className="flex items-center gap-2 min-w-[7rem]">
                    <CmykBars p={p} />
                    {isEditing ? (
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="number"
                          min={0}
                          max={100}
                          value={tonerDraft}
                          onChange={(e) => setTonerDraft(e.target.value)}
                          className="tt-input w-14 !py-1 !px-2 text-sm !min-h-0"
                          autoFocus
                        />
                        <button
                          type="button"
                          disabled={busyId === p.id}
                          onClick={() => saveToner(p.id)}
                          className="p-1.5 rounded-lg bg-[#39ff88] text-[#0b132b]"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingId(p.id);
                          setTonerDraft(p.toner_level != null ? String(p.toner_level) : '');
                        }}
                        className="text-xs tt-lcd text-[#e8eaed] hover:text-white"
                      >
                        {p.toner_level != null ? `${p.toner_level}%` : '—'}
                      </button>
                    )}
                  </div>

                  <button
                    type="button"
                    disabled={busyId === p.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      remove(p.id, p.name);
                    }}
                    className="p-2 rounded-lg text-[#8b9bb8] hover:text-red-400 hover:bg-red-500/10"
                    title="Remove"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Pinecone disclosure — detail only when opened */}
              {open && (
                <div className="px-4 pb-4 border-t border-white/5 grid gap-3 sm:grid-cols-2 text-xs text-[#8b9bb8]">
                  <div className="space-y-1 pt-3">
                    <p className="text-[10px] text-[#5c6b86]">Detail</p>
                    <p>Mode · {p.connection_mode || 'manual'}</p>
                    <p>Status detail · {p.status_detail ? p.status_detail.replace(/_/g, ' ') : 'n/a'}</p>
                    <p>Fail streak · {p.fail_streak ?? 0}</p>
                    <p>{ageText(p)}</p>
                    <p className="tt-mono">{p.ip_address || 'No IP for helper'}</p>
                  </div>
                  <div className="space-y-1 pt-3">
                    <p className="text-[10px] text-[#5c6b86]">Recent checks (evidence)</p>
                    {checksLoading === p.id && <p>Loading…</p>}
                    {(checksById[p.id] || []).length === 0 && checksLoading !== p.id && (
                      <p>No checks recorded yet.</p>
                    )}
                    <ul className="space-y-1">
                      {(checksById[p.id] || []).map((c: any) => (
                        <li key={c.id} className="flex flex-wrap gap-x-2">
                          <span className="text-[#f2f5ff]/90">
                            {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
                          </span>
                          <span>{c.source}</span>
                          <span>{c.ok === false ? 'failed' : c.status || 'ok'}</span>
                          {c.toner_level != null && <span>{c.toner_level}%</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {printers.length > 0 && printers.length < 5 && (
        <p className="text-xs text-[#5c6b86] text-center">Listed · {printers.length} printers</p>
      )}

      <div className="tt-thumb-bar md:hidden">
        <button type="button" onClick={() => load()} className="tt-btn tt-btn-ghost">
          <RefreshCw className="h-4 w-4" />
        </button>
        <Link to="/helper" className="tt-btn tt-btn-ghost">
          Helper
        </Link>
        <Link to="/add-printer" className="tt-btn tt-btn-primary">
          Add
        </Link>
      </div>
    </div>
  );
};

export default FleetHome;
