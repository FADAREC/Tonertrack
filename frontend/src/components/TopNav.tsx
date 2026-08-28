import React from 'react';
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
        className="p-2.5 rounded-md text-[#9aa0a8] hover:bg-white/5 hover:text-[#e8eaed]"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1 min-w-0">
        <p className="tt-display text-base tracking-wide truncate md:hidden">TonerTrack</p>
      </div>
      <span className="text-[11px] font-medium uppercase tracking-wider text-[#9aa0a8] hidden sm:inline">
        Fleet
      </span>
    </header>
  );
};

export default TopNav;
