import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutGrid, PlusCircle, Activity, LogOut, X } from 'lucide-react';

const Sidebar: React.FC<{
  darkMode: boolean;
  isOpen: boolean;
  toggleSidebar: () => void;
}> = ({ isOpen, toggleSidebar }) => {
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-3 text-sm font-semibold border-2 transition ${
      isActive
        ? 'bg-[#111] text-[#f4f1ea] border-[#111]'
        : 'bg-white text-[#111] border-transparent hover:border-[#111]'
    }`;

  const nav = (
    <>
      <div className="h-14 px-4 flex items-center justify-between border-b-2 border-[#111]">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 border-2 border-[#111] bg-[#111] text-[#f4f1ea] flex items-center justify-center text-xs font-black">
            T
          </div>
          <span className="font-black tracking-tight text-lg">TonerTrack</span>
        </div>
        <button
          type="button"
          onClick={toggleSidebar}
          className="md:hidden p-2 border-2 border-[#111] bg-white"
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
      <nav className="flex-1 p-3 space-y-2">
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
      <div className="p-3 border-t-2 border-[#111]">
        <button
          type="button"
          className="flex items-center gap-3 px-3 py-3 text-sm font-semibold w-full border-2 border-transparent hover:border-[#111] bg-white"
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
        className={`hidden md:flex flex-col w-64 shrink-0 border-r-2 border-[#111] bg-white ${isOpen ? '' : 'md:hidden'}`}
      >
        {nav}
      </aside>
    </>
  );
};

export default Sidebar;
