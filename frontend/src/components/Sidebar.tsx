import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutGrid, PlusCircle, Activity, LogOut, X } from 'lucide-react';

const Sidebar: React.FC<{
  darkMode: boolean;
  isOpen: boolean;
  toggleSidebar: () => void;
}> = ({ isOpen, toggleSidebar }) => {
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-md transition ${
      isActive
        ? 'bg-[#2c3036] text-[#e8eaed] border border-white/10'
        : 'text-[#9aa0a8] hover:text-[#e8eaed] hover:bg-white/5 border border-transparent'
    }`;

  const nav = (
    <>
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/10">
        <NavLink to="/" end className="flex items-center gap-2.5 min-w-0" onClick={() => window.innerWidth < 768 && toggleSidebar()}>
          <img src="/logo.svg" alt="" className="h-8 w-8 rounded-md" width={32} height={32} />
          <span className="tt-display text-lg tracking-wide">TonerTrack</span>
        </NavLink>
        <button
          type="button"
          onClick={toggleSidebar}
          className="md:hidden p-2 text-[#9aa0a8]"
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        <NavLink to="/" end className={linkCls} onClick={() => window.innerWidth < 768 && toggleSidebar()}>
          <LayoutGrid className="h-4 w-4" /> Fleet
        </NavLink>
        <NavLink to="/add-printer" className={linkCls} onClick={() => window.innerWidth < 768 && toggleSidebar()}>
          <PlusCircle className="h-4 w-4" /> Add printer
        </NavLink>
        <NavLink to="/helper" className={linkCls} onClick={() => window.innerWidth < 768 && toggleSidebar()}>
          <Activity className="h-4 w-4" /> Office checker
        </NavLink>
      </nav>
      <div className="p-3 border-t border-white/10">
        <button
          type="button"
          className="flex items-center gap-3 px-3 py-3 text-sm font-medium w-full text-[#9aa0a8] hover:text-[#e8eaed] rounded-md hover:bg-white/5"
          onClick={() => {
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            localStorage.removeItem('trust_mode');
            window.location.href = '/';
          }}
        >
          <LogOut className="h-4 w-4" /> Sign out
        </button>
      </div>
    </>
  );

  return (
    <>
      {isOpen && (
        <button type="button" className="tt-backdrop md:hidden" aria-label="Close menu" onClick={toggleSidebar} />
      )}
      <aside className={`tt-drawer md:hidden flex flex-col ${isOpen ? 'tt-drawer-open' : ''}`} aria-hidden={!isOpen}>
        {nav}
      </aside>
      <aside
        className={`hidden md:flex flex-col w-60 shrink-0 border-r border-white/10 bg-[#24272b] ${isOpen ? '' : 'md:hidden'}`}
      >
        {nav}
      </aside>
    </>
  );
};

export default Sidebar;
