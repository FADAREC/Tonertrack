import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { printersAPI } from '../services/api';

type ConnectKind = 'network' | 'local';

function formatApiError(err: any): string {
  const d = err?.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) {
    return d
      .map((x) => (typeof x === 'string' ? x : x?.msg || JSON.stringify(x)))
      .join(' ');
  }
  return 'Could not add printer';
}

const AddPrinterSimple: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const navigate = useNavigate();
  const [kind, setKind] = useState<ConnectKind>('network');
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [department, setDepartment] = useState('');
  const [ip, setIp] = useState('');
  const [localName, setLocalName] = useState('');
  const [toner, setToner] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (kind === 'network' && !ip.trim()) {
      setError('Network address is required for network printers');
      return;
    }
    if (kind === 'local' && !localName.trim() && !name.trim()) {
      setError('Windows printer name is required for USB / local printers');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const tonerVal = toner.trim() === '' ? null : Math.min(100, Math.max(0, parseInt(toner, 10)));
      if (kind === 'network') {
        await printersAPI.add({
          name: name.trim(),
          location: location.trim() || undefined,
          department: department.trim() || undefined,
          ip_address: ip.trim(),
          connection_mode: 'ping',
          toner_level: Number.isFinite(tonerVal as number) ? (tonerVal as number) : null,
        });
      } else {
        await printersAPI.add({
          name: name.trim(),
          location: location.trim() || undefined,
          department: department.trim() || undefined,
          local_name: (localName.trim() || name.trim()),
          connection_mode: 'local',
          toner_level: Number.isFinite(tonerVal as number) ? (tonerVal as number) : null,
        });
      }
      navigate('/');
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const tabBase =
    'flex-1 py-2.5 px-3 rounded-lg text-sm font-medium transition-colors border text-center';
  const tabOn = 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300';
  const tabOff = darkMode
    ? 'bg-transparent border-zinc-700 text-zinc-400 hover:text-zinc-200'
    : 'bg-transparent border-zinc-300 text-zinc-600 hover:text-zinc-900';

  return (
    <div className="max-w-lg mx-auto">
      <p className="text-xs text-zinc-500 mb-1">Fleet</p>
      <h1 className="text-2xl font-semibold tracking-tight mb-2">Add printer</h1>
      <p className="text-sm mb-6 text-zinc-500">
        Add a printer your team uses. The office checker only looks at printers on this board.
      </p>

      <form onSubmit={submit} className="tt-card p-6 space-y-4">
        <div>
          <p className="text-sm text-zinc-500 mb-2">How is this printer connected?</p>
          <div className="flex gap-2">
            <button
              type="button"
              className={`${tabBase} ${kind === 'network' ? tabOn : tabOff}`}
              onClick={() => setKind('network')}
            >
              On the network (IP)
            </button>
            <button
              type="button"
              className={`${tabBase} ${kind === 'local' ? tabOn : tabOff}`}
              onClick={() => setKind('local')}
            >
              USB / this PC
            </button>
          </div>
          <p className="text-xs text-zinc-500 mt-2">
            {kind === 'network'
              ? 'Best when the printer has an IP address the office PC can reach.'
              : 'Best for USB or printers only installed on one Windows PC (use the exact name from Windows).'}
          </p>
        </div>

        <div>
          <label className="text-sm text-zinc-500">Name on the board *</label>
          <input
            className="tt-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={kind === 'network' ? 'e.g. Front desk HP' : 'e.g. CEO desk printer'}
            required
          />
        </div>

        <div>
          <label className="text-sm text-zinc-500">Location</label>
          <input
            className="tt-input"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Ground floor"
          />
        </div>

        <div>
          <label className="text-sm text-zinc-500">Department</label>
          <input
            className="tt-input"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            placeholder="e.g. Accounts"
          />
        </div>

        {kind === 'network' ? (
          <div>
            <label className="text-sm text-zinc-500">Network address *</label>
            <input
              className="tt-input"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="e.g. 192.168.1.50"
              required
            />
            <p className="text-xs text-zinc-500 mt-1">
              The office checker uses this address. It does not scan your whole network.
            </p>
          </div>
        ) : (
          <div>
            <label className="text-sm text-zinc-500">Windows printer name *</label>
            <input
              className="tt-input"
              value={localName}
              onChange={(e) => setLocalName(e.target.value)}
              placeholder="e.g. HP DeskJet 2700 series"
              required
            />
            <p className="text-xs text-zinc-500 mt-1">
              Must match the name in Windows Settings → Printers. Run the office checker on that same PC.
            </p>
          </div>
        )}

        <div>
          <label className="text-sm text-zinc-500">Toner level % (optional)</label>
          <input
            className="tt-input"
            type="number"
            min={0}
            max={100}
            value={toner}
            onChange={(e) => setToner(e.target.value)}
            placeholder="Leave blank if unknown"
          />
          <p className="text-xs text-zinc-500 mt-1">
            Filled in automatically when the office checker can read it.
          </p>
        </div>

        {error && (
          <p className="text-red-400 text-sm" role="alert">
            {error}
          </p>
        )}

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
