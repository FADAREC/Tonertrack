import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/auth';
import BrandMark from './components/BrandMark';
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
  const [sidebarOpen, setSidebarOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth >= 768 : true
  );
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
    const onExpired = () => setToken(null);
    window.addEventListener('storage', onStorage);
    window.addEventListener('tonertrack:session-expired', onExpired);
    return () => {
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('tonertrack:session-expired', onExpired);
    };
  }, []);

  if (!token) {
    return (
      <div className={`min-h-screen flex items-center justify-center tt-app-shell text-[#e8eaed]`}>
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
      <div className={`min-h-screen flex items-center justify-center tt-app-shell text-[#e8eaed]`}>
        <p className="opacity-60">Loading…</p>
      </div>
    );
  }

  if (trustReady === false) {
    return <TrustScreen darkMode={darkMode} onDone={() => setTrustReady(true)} />;
  }

  return (
    <Router>
      <div className={`min-h-screen tt-app-shell text-[#e8eaed]`}>
        <Toaster
          position="bottom-center"
          toastOptions={{
            style: { background: '#24272b', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px' },
          }}
        />
        <div className="flex h-screen overflow-hidden">
          <Sidebar darkMode={darkMode} isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />
          <div className="flex-1 flex flex-col overflow-hidden min-w-0">
            <TopNav darkMode={darkMode} toggleDarkMode={toggleDarkMode} toggleSidebar={toggleSidebar} />
            <main className="flex-1 overflow-y-auto px-4 py-5 sm:p-8">
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
