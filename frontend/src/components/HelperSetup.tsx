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
  const [rawOnce, setRawOnce] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);

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

  // GitHub-style: secret only stays on screen briefly
  useEffect(() => {
    if (!rawOnce) return;
    if (secondsLeft <= 0) {
      setRawOnce(null);
      return;
    }
    const id = window.setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => window.clearTimeout(id);
  }, [rawOnce, secondsLeft]);

  // Never keep the secret if the user leaves the page
  useEffect(() => {
    return () => {
      setRawOnce(null);
    };
  }, []);

  const activeTokens = useMemo(
    () => tokens.filter((t) => !t.revoked_at),
    [tokens]
  );

  const liveToken = useMemo(
    () => activeTokens.find((t) => !!t.last_used_at) || null,
    [activeTokens]
  );

  const step1Done = activeTokens.length > 0 || !!rawOnce;
  const step2Done = downloaded || (!!rawOnce && activeTokens.some((t) => t.helper_download_enabled));
  const step3Done = !!liveToken;

  // Poll while waiting for first helper use
  useEffect(() => {
    if (!step1Done || step3Done) return;
    const id = setInterval(() => load(true), 5000);
    return () => clearInterval(id);
  }, [step1Done, step3Done, load]);

  const createKey = async () => {
    setBusy(true);
    setError('');
    setRawOnce(null);
    setDownloaded(false);
    try {
      const res = await agentAPI.quickSetup();
      setRawOnce(res.data.raw_token);
      setSecondsLeft(60);
      toast.success('Access key created - copy it now');
      await load(true);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not create access key');
    } finally {
      setBusy(false);
    }
  };

  const hideKey = () => {
    setRawOnce(null);
    setSecondsLeft(0);
    setCopied(false);
  };

  const copyRaw = async () => {
    if (!rawOnce) return;
    try {
      await navigator.clipboard.writeText(rawOnce);
      setCopied(true);
      toast.success('Copied - hide the key when you are done');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Could not copy - select the key and copy manually');
    }
  };

  const downloadStarter = async () => {
    if (!rawOnce) {
      setError('Create an access key first (step 1), then download while the key is still on screen.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await agentAPI.downloadStarterBat(rawOnce);
      setDownloaded(true);
      toast.success('Starter downloaded - hide the key when finished');
      setSecondsLeft((s) => (s > 20 ? 20 : s));
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Download failed');
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id: number) => {
    if (!window.confirm('Stop this office checker key? Updates from it will stop.')) return;
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
    <section
      className={`tt-card overflow-hidden ${done ? 'tt-card-live' : active ? '' : 'opacity-75'}`}
    >
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

  const activeStep = step3Done ? 3 : !step1Done ? 1 : !step2Done ? 2 : 3;

  return (
    <div className="max-w-xl mx-auto space-y-5 pb-16">
      <div className="space-y-3">
        <BrandMark size={28} wordmarkClassName="tt-display text-base tracking-wide" />
        <div>
          <h1 className="tt-display text-2xl tracking-wide">Office checker</h1>
          <p className="text-sm text-[#9aa0a8] mt-1">
            Updates the board from a PC on your network. Only printers on your board are checked - no network scan.
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

      <StepShell n={1} title="Create an access key" done={step1Done} active={activeStep === 1 || step1Done}>
        {!rawOnce && (
          <button
            type="button"
            disabled={busy}
            onClick={createKey}
            className="tt-btn tt-btn-primary"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Key className="h-4 w-4" />}
            Create key
          </button>
        )}
        {rawOnce && (
          <>
            <p className="text-xs text-[#e6b800] font-medium">
              Shown once. Copy it now - it disappears after {secondsLeft}s or when you hide it.
              You cannot view it again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs break-all tt-lcd bg-[#1a1c1f] border border-white/10 px-3 py-2 rounded-md select-all">
                {rawOnce}
              </code>
              <button type="button" onClick={copyRaw} className="tt-btn tt-btn-ghost shrink-0" title="Copy">
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
            <button type="button" onClick={hideKey} className="tt-btn tt-btn-ghost text-sm">
              I saved this key - hide it
            </button>
          </>
        )}
        {step1Done && !rawOnce && (
          <p className="text-xs text-[#9aa0a8]">
            You already have a key. Create another if you need a new secret, or continue to step 2 if you still
            have the secret from creation.
          </p>
        )}
        {step1Done && !rawOnce && (
          <button type="button" disabled={busy} onClick={createKey} className="tt-btn tt-btn-ghost text-sm">
            Create another key
          </button>
        )}
      </StepShell>

      <StepShell
        n={2}
        title="Download the helper for an office PC"
        done={step2Done}
        active={activeStep >= 2 || step2Done}
      >
        <p className="text-xs text-[#9aa0a8]">
          Run this on a PC that can reach the printers (same office network). Needs Python 3 on PATH.
        </p>
        <button
          type="button"
          disabled={busy || !rawOnce}
          onClick={downloadStarter}
          className="tt-btn tt-btn-primary"
        >
          <Download className="h-4 w-4" /> Download Windows starter
        </button>
        {!rawOnce && (
          <p className="text-[11px] text-[#e6b800]">
            Download is available right after you create a key (step 1), while the secret is still on screen.
          </p>
        )}
        {downloaded && (
          <p className="text-xs text-[#2db84b]">Starter downloaded - run it in step 3.</p>
        )}
      </StepShell>

      <StepShell n={3} title="Run once and confirm live" done={step3Done} active={activeStep >= 3 || step3Done}>
        {!step3Done && (
          <>
            <p className="text-xs text-[#9aa0a8]">
              On the office PC: open the downloaded file, allow it to run, wait for it to finish. This page
              updates when the checker checks in.
            </p>
            <div className="flex items-center gap-2 text-sm text-[#9aa0a8]">
              <Loader2 className="h-4 w-4 animate-spin" />
              Waiting for first check…
            </div>
            <p className="text-[11px] text-[#9aa0a8]">
              Stuck? Same LAN as the printers · full key pasted · printers on the board have IP addresses.
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
