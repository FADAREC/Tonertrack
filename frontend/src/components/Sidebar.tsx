import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutGrid, PlusCircle, Activity, LogOut, X } from 'lucide-react';

const Sidebar: React.FC<{
  darkMode: boolean;
  isOpen: boolean;
  toggleSidebar: () => void;
}> = ({ isOpen, toggleSidebar }) => {
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition ${
      isActive
        ? 'bg-[rgba(57,255,136,0.12)] text-[#39ff88] shadow-[inset_0_0_0_1px_rgba(57,255,136,0.2)]'
        : 'text-[#8b9bb8] hover:text-[#f0f4ff] hover:bg-white/5'
    }`;

  const nav = (
    <>
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div
            className="h-8 w-8 rounded-xl flex items-center justify-center text-xs font-bold text-[#0b132b]"
            style={{ background: '#39ff88', boxShadow: '0 0 20px rgba(57,255,136,0.35)' }}
          >
            T
          </div>
          <span className="font-semibold tracking-tight">TonerTrack</span>
        </div>
        <button
          type="button"
          onClick={toggleSidebar}
          className="md:hidden p-2 rounded-lg text-[#8b9bb8] hover:bg-white/5"
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
          <Activity className="h-4 w-4" /> Office helper
        </NavLink>
      </nav>
      <div className="p-3 border-t border-white/5">
        <button
          type="button"
          className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-[#8b9bb8] hover:text-[#f0f4ff] hover:bg-white/5 w-full"
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
      {/* Mobile backdrop */}
      {isOpen && (
        <button
          type="button"
          className="tt-backdrop md:hidden"
          aria-label="Close menu"
          onClick={toggleSidebar}
        />
      )}
      {/* Mobile drawer */}
      <aside
        className={`tt-drawer md:hidden flex flex-col ${isOpen ? 'tt-drawer-open' : ''}`}
        aria-hidden={!isOpen}
      >
        {nav}
      </aside>
      {/* Desktop rail */}
      <aside
        className={`hidden md:flex flex-col w-64 shrink-0 border-r border-white/5 bg-[rgba(11,19,43,0.9)] backdrop-blur-xl ${
          isOpen ? '' : 'md:hidden'
        }`}
      >
        {nav}
      </aside>
    </>
  );
};

export default Sidebar;
