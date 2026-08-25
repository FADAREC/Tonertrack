import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutGrid, PlusCircle, Activity, LogOut, ChevronLeft } from 'lucide-react';

const Sidebar: React.FC<{
  darkMode: boolean;
  isOpen: boolean;
  toggleSidebar: () => void;
}> = ({ isOpen, toggleSidebar }) => {
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
      isActive ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/5'
    }`;

  if (!isOpen) return null;

  return (
    <aside className="fixed inset-y-0 left-0 z-30 w-64 border-r border-white/5 bg-[#0a0a0b] flex flex-col">
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-blue-600 flex items-center justify-center text-xs font-bold">T</div>
          <span className="font-semibold tracking-tight">TonerTrack</span>
        </div>
        <button type="button" onClick={toggleSidebar} className="p-1.5 rounded-lg text-zinc-500 hover:bg-white/5">
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        <NavLink to="/" end className={linkCls}>
          <LayoutGrid className="h-4 w-4" /> Fleet
        </NavLink>
        <NavLink to="/add-printer" className={linkCls}>
          <PlusCircle className="h-4 w-4" /> Add printer
        </NavLink>
        <NavLink to="/helper" className={linkCls}>
          <Activity className="h-4 w-4" /> Office helper
        </NavLink>
      </nav>
      <div className="p-3 border-t border-white/5">
        <button
          type="button"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-zinc-400 hover:text-zinc-100 hover:bg-white/5 w-full"
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
    </aside>
  );
};

export default Sidebar;
