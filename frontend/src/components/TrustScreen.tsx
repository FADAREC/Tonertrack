import React, { useEffect, useState } from 'react';
import { Shield, CheckCircle, XCircle } from 'lucide-react';
import { trustAPI } from '../services/api';

interface TrustInfo {
  title: string;
  what_we_access: string[];
  what_we_never_access: string[];
  what_leaves_network: string[];
  kill_switch: string;
  modes: { id: string; label: string; description: string }[];
}

const TrustScreen: React.FC<{ onDone: () => void; darkMode: boolean }> = ({ onDone, darkMode }) => {
  const [info, setInfo] = useState<TrustInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    trustAPI.info().then((r) => setInfo(r.data)).catch(() => setError('Could not load trust information'));
  }, []);

  const choose = async (mode: 'manual_only' | 'agent_accepted') => {
    setLoading(true);
    setError('');
    try {
      await trustAPI.choose(mode);
      localStorage.setItem('trust_mode', mode);
      onDone();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not save choice');
    } finally {
      setLoading(false);
    }
  };

  if (!info) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <p className={darkMode ? 'text-white/70' : 'text-gray-600'}>{error || 'Loading…'}</p>
      </div>
    );
  }

  const card = darkMode
    ? 'bg-white border-2 border-[#111] text-[#111] shadow-[4px_4px_0_#111]'
    : 'bg-white border-2 border-[#111] text-[#111] shadow-[4px_4px_0_#111]';

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${darkMode ? 'bg-[#f4f1ea]' : 'bg-slate-50'}`}>
      <div className={`max-w-xl w-full rounded-2xl p-8 ${card}`}>
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-8 w-8 text-blue-500" />
          <h1 className="text-2xl tracking-tight font-semibold">{info.title}</h1>
        </div>

        <section className="mb-5">
          <h2 className="text-sm font-semibold text-green-500 mb-2 flex items-center gap-2">
            <CheckCircle className="h-4 w-4" /> What we access
          </h2>
          <ul className="space-y-1 text-sm opacity-90 list-disc pl-5">
            {info.what_we_access.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </section>

        <section className="mb-5">
          <h2 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
            <XCircle className="h-4 w-4" /> What we never access
          </h2>
          <ul className="space-y-1 text-sm opacity-90 list-disc pl-5">
            {info.what_we_never_access.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </section>

        <section className="mb-5">
          <h2 className="text-sm font-semibold opacity-60 mb-2">What leaves your network</h2>
          <ul className="space-y-1 text-sm opacity-90 list-disc pl-5">
            {info.what_leaves_network.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </section>

        <p className="text-sm opacity-80 mb-6 border-l-4 border-blue-500 pl-3">{info.kill_switch}</p>

        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

        <div className="space-y-3">
          <button
            type="button"
            disabled={loading}
            onClick={() => choose('manual_only')}
            className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium transition disabled:opacity-50"
          >
            Continue with Manual only
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => choose('agent_accepted')}
            className="w-full py-3 rounded-xl border border-gray-500 hover:bg-white/5 font-medium transition disabled:opacity-50"
          >
            I understand. On-site helper later
          </button>
          <p className="text-xs opacity-60 text-center">
            Manual only never contacts your network. You can change this later in Settings.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TrustScreen;
