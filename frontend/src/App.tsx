import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Auth from './components/auth';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';

function App() {
  const [darkMode, setDarkMode] = useState(true); // Default dark for drippy vibe

  const toggleDarkMode = () => setDarkMode(!darkMode);

  return (
    <Router>
      <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark bg-gray-900 text-white' : 'bg-gradient-to-br from-purple-100 via-blue-100 to-indigo-100 text-gray-900'}`}>
        {localStorage.getItem('token') ? (
          <div className="flex h-screen overflow-hidden">
            <Sidebar darkMode={darkMode} />
            <div className="flex-1 flex flex-col overflow-hidden">
              <TopNav darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
              <main className="flex-1 overflow-y-auto p-6">
                <Routes>
                  <Route path="/" element={<Dashboard darkMode={darkMode} />} />
                </Routes>
              </main>
            </div>
          </div>
        ) : (
          <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
            {/* Animated glassy background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-indigo-900/20 animate-pulse" />
            <div className="w-full max-w-md p-8 relative z-10">
              <Auth darkMode={darkMode} />
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;