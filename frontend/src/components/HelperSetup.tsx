import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Copy, Download, Key, Loader2, RefreshCw } from 'lucide-react';
import { agentAPI } from '../services/api';
import BrandMark from './BrandMark';
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
  /** Full secret only in memory briefly for advanced reveal / retry download */
  const [rawOnce, setRawOnce] = useState<string | null>(null);
  const [tokenPrefix, setTokenPrefix] = useState<string | null>(null);
  const [showFullKey, setShowFullKey] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);

  const clearSecret = useCallback(() => {
    setRawOnce(null);
    setShowFullKey(false);
    setSecondsLeft(0);
    setCopied(false);
  }, []);

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const res = await agentAPI.listTokens();
      setTokens(res.data || []);
      setError('');
    } catch (e: any) {
      if (!quiet) setError(e?.response?.data?.detail || 'Only an admin can manage the office checker.');
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Full secret only lives briefly after create (for optional CLI / re-download)
  useEffect(() => {
    if (!rawOnce) return;
    if (secondsLeft <= 0) {
      clearSecret();
      return;
    }
    const id = window.setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => window.clearTimeout(id);
  }, [rawOnce, secondsLeft, clearSecret]);

  useEffect(() => {
    return () => {
      setRawOnce(null);
    };
  }, []);

  const activeTokens = useMemo(() => tokens.filter((t) => !t.revoked_at), [tokens]);
  const liveToken = useMemo(
    () => activeTokens.find((t) => !!t.last_used_at) || null,
    [activeTokens]
  );

  const step1Done = activeTokens.length > 0 || !!tokenPrefix || !!rawOnce;
  const step2Done = downloaded;
  const step3Done = !!liveToken;
  const activeStep = step3Done ? 3 : !step1Done ? 1 : !step2Done ? 2 : 3;

  useEffect(() => {
    if (!step1Done || step3Done) return;
    const id = setInterval(() => load(true), 5000);
    return () => clearInterval(id);
  }, [step1Done, step3Done, load]);

  const downloadWithRaw = async (raw: string) => {
    await agentAPI.downloadStarterBat(raw);
    setDownloaded(true);
  };

  /** Create key and download starter in one shot so the secret is not required on screen. */
  const createKeyAndDownload = async () => {
    setBusy(true);
    setError('');
    clearSecret();
    setDownloaded(false);
    setTokenPrefix(null);
    try {
      const res = await agentAPI.quickSetup();
      const raw = res.data.raw_token as string;
      const prefix =
        res.data.token?.token_prefix ||
        (typeof raw === 'string' ? raw.slice(0, 10) : null);
      setTokenPrefix(prefix);
      setRawOnce(raw);
      setSecondsLeft(180);
      setShowFullKey(false);

      try {
        await downloadWithRaw(raw);
        toast.success('Key created and starter downloaded');
      } catch (dlErr: any) {
        setError(
          dlErr?.message ||
            'Key was created but the starter download failed. Use Retry download below while the session is still open.'
        );
        toast.error('Download failed - use Retry download');
      }
      await load(true);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not create access key');
    } finally {
      setBusy(false);
    }
  };

  const retryDownload = async () => {
    if (!rawOnce) {
      setError(
        'The starter can only be downloaded right after a key is created. Create a new key to get a new starter file.'
      );
      return;
    }
    setBusy(true);
    setError('');
    try {
      await downloadWithRaw(rawOnce);
      toast.success('Starter downloaded');
    } catch (e: any) {
      setError(e?.message || 'Download failed');
    } finally {
      setBusy(false);
    }
  };

  const copyRaw = async () => {
    if (!rawOnce) return;
    try {
      await navigator.clipboard.writeText(rawOnce);
      setCopied(true);
      toast.success('Copied - clear it from the clipboard when done');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Could not copy');
    }
  };

  const revoke = async (id: number) => {
    if (!window.confirm('Stop this office checker key? The starter file for it will stop working.')) return;
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

  const StepShell: React.FC<{
    n: number;
    title: string;
    done: boolean;
    active: boolean;
    children: React.ReactNode;
  }> = ({ n, title, done, active, children }) => (
    <section className={`tt-card overflow-hidden ${done ? 'tt-card-live' : active ? '' : 'opacity-75'}`}>
      <div className="px-4 py-3 flex items-center gap-3 border-b border-white/10">
        <span
          className={`h-7 w-7 rounded-md flex items-center justify-center text-xs font-bold shrink-0 ${
            done ? 'bg-[#2db84b] text-[#1a1c1f]' : 'bg-[#e8eaed] text-[#1a1c1f]'
          }`}
        >
          {done ? <Check className="h-4 w-4" /> : n}
        </span>
        <div className="min-w-0 flex-1">
          <p className="tt-display text-sm tracking-wide">{title}</p>
          {done && <p className="text-[11px] text-[#2db84b]">Done</p>}
        </div>
      </div>
      {(active || done) && <div className="p-4 space-y-3">{children}</div>}
    </section>
  );

  return (
    <div className="max-w-xl mx-auto space-y-5 pb-16">
      <div className="space-y-3">
        <BrandMark size={28} wordmarkClassName="tt-display text-base tracking-wide" />
        <div>
          <h1 className="tt-display text-2xl tracking-wide">Office checker</h1>
          <p className="text-sm text-[#9aa0a8] mt-1">
            Updates the board from a PC on your network. Only printers on your board are checked - no network
            scan.
          </p>
        </div>
      </div>

      {error && (
        <div className="tt-card px-4 py-3 text-sm text-[#e02424] border-[rgba(224,36,36,0.4)]">{error}</div>
      )}

      {step3Done && liveToken && (
        <div className="tt-card tt-card-live px-4 py-4 space-y-2">
          <p className="text-sm font-semibold text-[#2db84b]">Checker is live</p>
          <p className="text-xs text-[#9aa0a8]">
            Key {liveToken.token_prefix}… last used{' '}
            <span className="tt-lcd text-[#e8eaed]">
              {new Date(liveToken.last_used_at!).toLocaleString()}
            </span>
          </p>
          <Link to="/" className="tt-btn tt-btn-primary inline-flex text-sm">
            View fleet board
          </Link>
        </div>
      )}

      <StepShell
        n={1}
        title="Create key and download starter"
        done={step1Done && step2Done}
        active={activeStep <= 2 || step1Done}
      >
        <p className="text-xs text-[#9aa0a8]">
          Creates an access key and downloads the Windows starter in one step. The full key is not shown by
          default. The starter file contains the secret - treat that file like a password. If it leaks, revoke
          the key here.
        </p>
        <button
          type="button"
          disabled={busy}
          onClick={createKeyAndDownload}
          className="tt-btn tt-btn-primary"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Key className="h-4 w-4" />}
          Create key and download
        </button>

        {(tokenPrefix || rawOnce) && (
          <div className="space-y-2 rounded-md border border-white/10 p-3">
            <p className="text-xs text-[#9aa0a8]">
              Key prefix{' '}
              <span className="tt-lcd text-[#e8eaed]">{tokenPrefix || rawOnce?.slice(0, 10)}…</span>
              {rawOnce && secondsLeft > 0 && (
                <span className="ml-2">· session {secondsLeft}s (retry / advanced only)</span>
              )}
            </p>
            {downloaded ? (
              <p className="text-xs text-[#2db84b]">Starter downloaded. Continue to step 2 on an office PC.</p>
            ) : (
              <p className="text-xs text-[#e6b800]">Starter not saved yet - use Retry download while this session is open.</p>
            )}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy || !rawOnce}
                onClick={retryDownload}
                className="tt-btn tt-btn-ghost text-sm"
              >
                <Download className="h-3.5 w-3.5" /> Retry download
              </button>
              {rawOnce && !showFullKey && (
                <button
                  type="button"
                  className="tt-btn tt-btn-ghost text-sm"
                  onClick={() => setShowFullKey(true)}
                >
                  Show full key (advanced)
                </button>
              )}
              {rawOnce && (
                <button type="button" className="tt-btn tt-btn-ghost text-sm" onClick={clearSecret}>
                  Clear secret from this page
                </button>
              )}
            </div>
            {showFullKey && rawOnce && (
              <div className="space-y-2 pt-1">
                <p className="text-xs text-[#e6b800]">
                  Only for manual CLI use. Prefer the starter file. Hides when the session ends.
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs break-all tt-lcd bg-[#1a1c1f] border border-white/10 px-3 py-2 rounded-md">
                    {rawOnce}
                  </code>
                  <button type="button" onClick={copyRaw} className="tt-btn tt-btn-ghost shrink-0">
                    {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {step1Done && !rawOnce && !downloaded && (
          <p className="text-xs text-[#e6b800]">
            A key already exists, but a new starter file needs a new key (the secret is only available at
            creation). Create key and download again, then revoke the old key if you no longer need it.
          </p>
        )}
      </StepShell>

      <StepShell
        n={2}
        title="Run on an office PC"
        done={step3Done}
        active={activeStep >= 2 || step2Done}
      >
        <p className="text-xs text-[#9aa0a8]">
          Copy <span className="tt-lcd">Run-TonerTrack-Checker.bat</span> to a PC on the same network as the
          printers. Double-click it. Needs Python 3 on PATH. No key paste - the file already carries the
          secret.
        </p>
        {!step3Done && (
          <>
            <div className="flex items-center gap-2 text-sm text-[#9aa0a8]">
              <Loader2 className="h-4 w-4 animate-spin" />
              Waiting for first check-in…
            </div>
            <p className="text-[11px] text-[#9aa0a8]">
              Stuck? Same LAN · printers have valid IPs · Python installed · key not revoked.
            </p>
            <button type="button" onClick={() => load()} className="tt-btn tt-btn-ghost text-sm">
              <RefreshCw className="h-3.5 w-3.5" /> Check now
            </button>
          </>
        )}
        {step3Done && (
          <p className="text-xs text-[#2db84b]">First check received. Board will show fresh status and toner.</p>
        )}
      </StepShell>

      {activeTokens.length > 0 && (
        <div className="space-y-2 pt-2">
          <p className="text-xs text-[#9aa0a8] uppercase tracking-wide">Keys</p>
          <p className="text-[11px] text-[#9aa0a8]">
            Revoke if a starter file may have been shared or lost. Prefix only is stored in the app - the full
            secret is never shown again.
          </p>
          {loading && <p className="text-sm text-[#9aa0a8]">Loading…</p>}
          {activeTokens.map((tok) => (
            <div key={tok.id} className="tt-card px-4 py-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">
                  {tok.name}{' '}
                  <span className="text-[#9aa0a8] font-normal tt-lcd">· {tok.token_prefix}…</span>
                </p>
                <p className="text-xs text-[#9aa0a8] mt-0.5">
                  {tok.last_used_at
                    ? `Last used ${new Date(tok.last_used_at).toLocaleString()}`
                    : 'Not used yet'}
                </p>
              </div>
              <button
                type="button"
                disabled={busy}
                onClick={() => revoke(tok.id)}
                className="tt-btn tt-btn-ghost text-xs text-[#e02424]"
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HelperSetup;
