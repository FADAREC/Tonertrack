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
  const [info, setInfo] = useState('');
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
      setError(e?.response?.data?.detail || 'Admin only — sign in as admin to manage the helper.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createToken = async () => {
    setBusy(true);
    setError('');
    setInfo('');
    setRawOnce(null);
    try {
      const res = await agentAPI.createToken(`office-${new Date().toISOString().slice(0, 10)}`);
      setRawOnce(res.data.raw_token);
      setInfo(res.data.warning || 'Store this token now. It will not be shown again.');
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not create token');
    } finally {
      setBusy(false);
    }
  };

  const enableDownload = async (id: number) => {
    setBusy(true);
    setError('');
    try {
      await agentAPI.enableHelperDownload(id);
      setInfo('Helper download enabled for this token.');
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not enable download');
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id: number) => {
    if (!window.confirm('Revoke this token? The office helper will stop reporting until you issue a new one.')) return;
    setBusy(true);
    try {
      await agentAPI.revokeToken(id);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Revoke failed');
    } finally {
      setBusy(false);
    }
  };

  const copyRaw = async () => {
    if (!rawOnce) return;
    await navigator.clipboard.writeText(rawOnce);
    setCopied(true);
    toast.success('Token copied');
    setTimeout(() => setCopied(false), 1500);
  };

  const base = window.location.origin;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500 mb-1">Office helper</p>
        <h1 className="text-2xl font-semibold tracking-tight">Install on a LAN PC</h1>
        <p className="text-sm text-zinc-500 mt-1">
          The helper runs inside your network, checks only printers you listed, and updates the shared board.
          We never scan your subnet from the cloud.
        </p>
      </header>

      <ol className="tt-card divide-y divide-white/5">
        {[
          'Create an agent token (admin). Copy it once — it will not be shown again.',
          'Enable helper download for that token.',
          'On an office Windows PC, download the helper and set the token as an environment variable.',
          'Run the helper. Set poll frequency on the Fleet page.',
        ].map((step, i) => (
          <li key={step} className="px-4 py-3 flex gap-3 text-sm text-zinc-300">
            <span className="text-zinc-500 font-medium tabular-nums w-5">{i + 1}.</span>
            {step}
          </li>
        ))}
      </ol>

      {error && (
        <p className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">{error}</p>
      )}
      {info && (
        <p className="text-sm text-emerald-200/90 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3">
          {info}
        </p>
      )}

      {rawOnce && (
        <div className="tt-card p-4 border-amber-500/30">
          <p className="text-xs text-amber-200/90 mb-2 font-medium">Show-once token — store securely</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs break-all bg-black/40 rounded-lg px-3 py-2 text-zinc-200">{rawOnce}</code>
            <button type="button" onClick={copyRaw} className="tt-btn tt-btn-ghost shrink-0">
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={busy} onClick={createToken} className="tt-btn tt-btn-primary">
          <Key className="h-4 w-4" /> Create token
        </button>
        <button type="button" onClick={load} className="tt-btn tt-btn-ghost">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      <div className="space-y-2">
        {loading && <p className="text-sm text-zinc-500">Loading tokens…</p>}
        {!loading && tokens.length === 0 && (
          <p className="text-sm text-zinc-500">No tokens yet. Create one to unlock the helper.</p>
        )}
        {tokens.map((t) => (
          <div key={t.id} className="tt-card px-4 py-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-zinc-100 flex items-center gap-2">
                <Shield className="h-3.5 w-3.5 text-zinc-500" />
                {t.name}{' '}
                <span className="text-zinc-500 font-normal">· {t.token_prefix}…</span>
              </p>
              <p className="text-xs text-zinc-500 mt-0.5">
                {t.revoked_at
                  ? 'Revoked'
                  : t.helper_download_enabled
                    ? 'Download enabled'
                    : 'Download locked'}
                {t.last_used_at ? ` · last used ${new Date(t.last_used_at).toLocaleString()}` : ' · never used'}
              </p>
            </div>
            <div className="flex gap-2">
              {!t.revoked_at && !t.helper_download_enabled && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => enableDownload(t.id)}
                  className="tt-btn tt-btn-ghost text-xs"
                >
                  <Download className="h-3.5 w-3.5" /> Enable download
                </button>
              )}
              {!t.revoked_at && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => revoke(t.id)}
                  className="tt-btn tt-btn-ghost text-xs text-red-300"
                >
                  Revoke
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="tt-card p-4">
        <p className="text-sm font-medium text-zinc-100 mb-2">On the office PC</p>
        <pre className="text-[11px] leading-relaxed text-zinc-400 bg-black/40 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">{`curl -H "X-Agent-Token: tt_YOUR_TOKEN" -o tonertrack_helper.py ${base}/agent/helper/download
set TONERTRACK_URL=${base}
set TONERTRACK_AGENT_TOKEN=tt_YOUR_TOKEN
python tonertrack_helper.py`}</pre>
      </div>
    </div>
  );
};

export default HelperSetup;
