import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import PrinterList from './components/PrinterList';
import AddPrinter from './components/AddPrinter';
import Settings from './components/Settings';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true); // New: Sidebar toggle state

  const toggleDarkMode = () => setDarkMode(!darkMode);
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen); // New: Toggle function

  return (
    <Router>
      <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark bg-gray-900 text-white' : 'bg-gradient-to-br from-purple-100 via-blue-100 to-indigo-100 text-gray-900'}`}>
        {localStorage.getItem('token') ? (
          <div className="flex h-screen overflow-hidden">
            <Sidebar darkMode={darkMode} isOpen={sidebarOpen} toggleSidebar={toggleSidebar} /> {/* Pass props */}
            <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}> {/* Dynamic margin */}
              <TopNav darkMode={darkMode} toggleDarkMode={toggleDarkMode} toggleSidebar={toggleSidebar} /> {/* Pass toggle to TopNav */}
              <main className="flex-1 overflow-y-auto p-6">
                <Routes>
                  <Route path="/" element={<Dashboard darkMode={darkMode} />} />
                  <Route path="/printers" element={<PrinterList darkMode={darkMode} />} />
                  <Route path="/add-printer" element={<AddPrinter darkMode={darkMode} />} />
                  <Route path="/settings" element={<Settings darkMode={darkMode} toggleDarkMode={toggleDarkMode} />} />
                </Routes>
              </main>
            </div>
          </div>
        ) : (
          <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
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
