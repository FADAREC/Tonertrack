import React, { useEffect, useState } from 'react';
import { Download, Key, Shield, Copy, Check, RefreshCw } from 'lucide-react';
import { agentAPI } from '../services/api';
import toast from 'react-hot-toast';

type TokenRow = {
  id: number;
  name: string;
  token_prefix: string;
  created_by: string;
  created_at?: string | null;
  last_used_at?: string | null;
  revoked_at?: string | null;
  helper_download_enabled?: boolean;
};

const HelperSetup: React.FC<{ darkMode: boolean }> = () => {
  const [tokens, setTokens] = useState<TokenRow[]>([]);
  const [error, setError] = useState('');
  const [rawOnce, setRawOnce] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await agentAPI.listTokens();
      setTokens(res.data || []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Only an admin can manage the office checker.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const quickSetup = async () => {
    setBusy(true);
    setError('');
    setRawOnce(null);
    try {
      const res = await agentAPI.quickSetup();
      setRawOnce(res.data.raw_token);
      toast.success('Access key created');
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not set up office checker');
    } finally {
      setBusy(false);
    }
  };

  const downloadStarter = async () => {
    if (!rawOnce) {
      setError('Create an access key first, then download the Windows file while the key is still on screen.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await agentAPI.downloadStarterBat(rawOnce);
      toast.success('Starter downloaded');
    } catch (e: any) {
      setError(e?.message || 'Download failed');
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id: number) => {
    if (!window.confirm('Stop this office checker key? Status updates from it will stop.')) return;
    setBusy(true);
    try {
      await agentAPI.revokeToken(id);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not revoke');
    } finally {
      setBusy(false);
    }
  };

  const copyRaw = async () => {
    if (!rawOnce) return;
    await navigator.clipboard.writeText(rawOnce);
    setCopied(true);
    toast.success('Access key copied');
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <header>
        <p className="text-xs text-[#8b9bb8] mb-1">Office checker</p>
        <h1 className="text-2xl font-semibold tracking-tight">Keep the board up to date</h1>
        <p className="text-sm text-[#8b9bb8] mt-1">
          Run a small program on one office computer. It checks only the printers on your board and
          updates status so support does not have to walk the floor.
        </p>
      </header>

      <ol className="tt-card divide-y divide-white/5 text-sm text-[#f2f5ff]/90">
        <li className="px-4 py-3">1. Add printers on the board (with network addresses).</li>
        <li className="px-4 py-3">2. Create an access key and download the Windows starter.</li>
        <li className="px-4 py-3">3. On an office PC, double-click the starter and leave the window open.</li>
      </ol>

      {error && (
        <p className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">{error}</p>
      )}

      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={busy} onClick={quickSetup} className="tt-btn tt-btn-primary">
          <Key className="h-4 w-4" /> Create access key
        </button>
        <button
          type="button"
          disabled={busy || !rawOnce}
          onClick={downloadStarter}
          className="tt-btn tt-btn-ghost"
        >
          <Download className="h-4 w-4" /> Download Windows starter
        </button>
        <button type="button" onClick={load} className="tt-btn tt-btn-ghost">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {rawOnce && (
        <div className="tt-card p-4 border-2 border-[#111]">
          <p className="text-xs text-[#9a6b00] mb-2 font-medium">
            Save this key. It will not be shown again. Download the Windows starter while you still have it.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs break-all bg-[#e8e4dc] border-2 border-[#111] px-3 py-2 text-[#f2f5ff]">
              {rawOnce}
            </code>
            <button type="button" onClick={copyRaw} className="tt-btn tt-btn-ghost shrink-0">
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <p className="text-xs text-[#8b9bb8]">Existing keys</p>
        {loading && <p className="text-sm text-[#8b9bb8]">Loading…</p>}
        {!loading && tokens.length === 0 && (
          <p className="text-sm text-[#8b9bb8]">No keys yet. Create one to start automatic checks.</p>
        )}
        {tokens.map((tok) => (
          <div key={tok.id} className="tt-card px-4 py-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-[#f2f5ff] flex items-center gap-2">
                <Shield className="h-3.5 w-3.5 text-[#8b9bb8]" />
                {tok.name} <span className="text-[#8b9bb8] font-normal">· {tok.token_prefix}…</span>
              </p>
              <p className="text-xs text-[#8b9bb8] mt-0.5">
                {tok.revoked_at
                  ? 'Revoked'
                  : tok.helper_download_enabled
                    ? 'Download allowed'
                    : 'Download locked'}
                {tok.last_used_at
                  ? ` · last used ${new Date(tok.last_used_at).toLocaleString()}`
                  : ' · not used yet'}
              </p>
            </div>
            {!tok.revoked_at && (
              <button
                type="button"
                disabled={busy}
                onClick={() => revoke(tok.id)}
                className="tt-btn tt-btn-ghost text-xs text-red-300"
              >
                Revoke
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default HelperSetup;
