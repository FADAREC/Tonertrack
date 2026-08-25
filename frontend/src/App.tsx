import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/auth';
import TrustScreen from './components/TrustScreen';
import FleetHome from './components/FleetHome';
import AddPrinterSimple from './components/AddPrinterSimple';
import HelperSetup from './components/HelperSetup';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import { trustAPI } from './services/api';
import { Toaster } from 'react-hot-toast';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [trustReady, setTrustReady] = useState<boolean | null>(null);

  const toggleDarkMode = () => setDarkMode(!darkMode);
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  useEffect(() => {
    if (!token) {
      setTrustReady(null);
      return;
    }
    const cached = localStorage.getItem('trust_mode');
    if (cached) {
      setTrustReady(true);
      return;
    }
    trustAPI
      .status()
      .then((r) => {
        if (r.data?.mode) {
          localStorage.setItem('trust_mode', r.data.mode);
          setTrustReady(true);
        } else {
          setTrustReady(false);
        }
      })
      .catch(() => setTrustReady(false));
  }, [token]);

  // Re-read token after login (auth does full reload currently; keep state path too)
  useEffect(() => {
    const onStorage = () => setToken(localStorage.getItem('token'));
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  if (!token) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-[#0a0a0b] text-zinc-100`}>
        <div className="w-full max-w-md p-6">
          <Auth
            darkMode={darkMode}
            onAuthed={() => setToken(localStorage.getItem('token'))}
          />
        </div>
      </div>
    );
  }

  if (trustReady === null) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-[#0a0a0b] text-zinc-100`}>
        <p className="opacity-60">Loading…</p>
      </div>
    );
  }

  if (trustReady === false) {
    return <TrustScreen darkMode={darkMode} onDone={() => setTrustReady(true)} />;
  }

  return (
    <Router>
      <div className={`min-h-screen bg-[#0a0a0b] text-zinc-100`}>
        <Toaster
          position="bottom-center"
          toastOptions={{
            style: { background: '#1a1a1e', color: '#f4f4f5', border: '1px solid rgba(255,255,255,0.08)' },
          }}
        />
        <div className="flex h-screen overflow-hidden">
          <Sidebar darkMode={darkMode} isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />
          <div className={`flex-1 flex flex-col overflow-hidden transition-all ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
            <TopNav darkMode={darkMode} toggleDarkMode={toggleDarkMode} toggleSidebar={toggleSidebar} />
            <main className="flex-1 overflow-y-auto p-6">
              <Routes>
                <Route path="/" element={<FleetHome darkMode={darkMode} />} />
                <Route path="/add-printer" element={<AddPrinterSimple darkMode={darkMode} />} />
                <Route path="/helper" element={<HelperSetup darkMode={darkMode} />} />
                <Route path="/printers" element={<Navigate to="/" replace />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;
