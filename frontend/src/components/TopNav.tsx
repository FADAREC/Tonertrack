import React from 'react';
import { Link } from 'react-router-dom';
import { Menu } from 'lucide-react';

const TopNav: React.FC<{
  darkMode: boolean;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
}> = ({ toggleSidebar }) => {
  return (
    <header className="h-14 border-b border-white/10 bg-[#24272b] flex items-center px-3 sm:px-4 gap-3 shrink-0 sticky top-0 z-20">
      <button
        type="button"
        onClick={toggleSidebar}
        className="p-2.5 rounded-md text-[#9aa0a8] hover:bg-white/5 hover:text-[#e8eaed] md:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <Link
        to="/"
        className="flex items-center gap-2 min-w-0 hover:opacity-90"
        aria-label="TonerTrack home — fleet board"
      >
        <span className="h-7 w-7 rounded-md bg-[#e8eaed] text-[#1a1c1f] flex items-center justify-center text-xs font-bold shrink-0">
          T
        </span>
        <span className="tt-display text-base tracking-wide truncate">TonerTrack</span>
      </Link>
      <div className="flex-1" />
      <Link
        to="/"
        className="text-[11px] font-medium uppercase tracking-wider text-[#9aa0a8] hover:text-[#e8eaed] hidden sm:inline"
      >
        Fleet board
      </Link>
    </header>
  );
};

export default TopNav;
