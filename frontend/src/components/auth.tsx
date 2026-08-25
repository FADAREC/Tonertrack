import React, { useState } from 'react';
import { User, Lock, Mail, ArrowRight } from 'lucide-react';
import { authAPI } from '../services/api';

function formatError(err: any): string {
  if (!err) return 'Something went wrong. Try again.';
  if (!err.response) {
    if (err.message === 'Network Error') return 'Cannot reach the server. Check your connection.';
    return err.message || 'Something went wrong. Try again.';
  }
  const detail = err.response.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => {
        const field = Array.isArray(d.loc) ? d.loc.filter((x: any) => x !== 'body').join(' ') : '';
        const msg = d.msg || d.message || JSON.stringify(d);
        return field ? `${field}: ${msg}` : msg;
      })
      .join('. ');
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail);
  return `Request failed (${err.response.status}). Try again.`;
}

const Auth: React.FC<{ darkMode: boolean; onAuthed?: () => void }> = ({ darkMode, onAuthed }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);

  const inputCls =
    'w-full pl-10 p-3 rounded-xl border bg-white/5 border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400/50';

  const finishLogin = (accessToken: string, role?: string) => {
    localStorage.setItem('token', accessToken);
    if (role) localStorage.setItem('role', role);
    if (onAuthed) onAuthed();
    else window.location.reload();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');

    const user = username.trim();
    const mail = email.trim().toLowerCase();
    const pass = password;

    if (user.length < 3) {
      setError('Username must be at least 3 characters.');
      return;
    }
    if (pass.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    if (isRegister) {
      if (!mail || !mail.includes('@')) {
        setError('Enter a valid email address.');
        return;
      }
      if (pass !== confirm) {
        setError('Passwords do not match.');
        return;
      }
    }

    setLoading(true);
    try {
      if (isRegister) {
        const reg = await authAPI.register(user, mail, pass);
        // Auto sign-in after successful registration
        if (reg.data?.access_token) {
          finishLogin(reg.data.access_token, reg.data.role);
          return;
        }
        // Fallback: login with same credentials
        const loginRes = await authAPI.login(user, pass);
        finishLogin(loginRes.data.access_token, loginRes.data.role);
      } else {
        const loginRes = await authAPI.login(user, pass);
        finishLogin(loginRes.data.access_token, loginRes.data.role);
      }
    } catch (err: any) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsRegister(!isRegister);
    setError('');
    setInfo('');
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold">T</div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-50">TonerTrack</h1>
        <p className="text-sm text-zinc-500">Shared printer board for your office</p>
      </div>
    <form onSubmit={handleSubmit} className="space-y-5 bg-[#121214] rounded-2xl p-8 border border-white/10">
      <div className="text-center">
        <h2 className="text-lg font-semibold text-white mb-1">{isRegister ? 'Create account' : 'Sign in'}</h2>
        <p className="text-zinc-500 text-sm">
          {isRegister ? 'First account becomes admin for this office.' : 'Username and password.'}
        </p>
      </div>

      <div className="space-y-3">
        <div className="relative">
          <User className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 h-5 w-5" />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            autoComplete="username"
            required
            minLength={3}
            className={inputCls}
          />
        </div>

        {isRegister && (
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 h-5 w-5" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              autoComplete="email"
              required
              className={inputCls}
            />
          </div>
        )}

        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 h-5 w-5" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password (min 6 characters)"
            autoComplete={isRegister ? 'new-password' : 'current-password'}
            required
            minLength={6}
            className={inputCls}
          />
        </div>

        {isRegister && (
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 h-5 w-5" />
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Confirm password"
              autoComplete="new-password"
              required
              minLength={6}
              className={inputCls}
            />
          </div>
        )}
      </div>

      {error && (
        <p className="text-red-300 text-sm bg-red-500/15 border border-red-400/30 rounded-xl p-3 text-center">
          {error}
        </p>
      )}
      {info && (
        <p className="text-green-300 text-sm bg-green-500/15 border border-green-400/30 rounded-xl p-3 text-center">
          {info}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white p-3 rounded-xl font-medium transition"
      >
        <ArrowRight className="inline h-5 w-5 mr-2" />
        {loading ? (isRegister ? 'Creating…' : 'Signing in…') : isRegister ? 'Create account' : 'Sign in'}
      </button>

      <button type="button" onClick={switchMode} className="w-full text-zinc-500 hover:text-zinc-200 text-sm">
        {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Create one"}
      </button>
    </form>
    </div>
  );
};

export default Auth;
