import React from 'react';
import { Menu } from 'lucide-react';

const TopNav: React.FC<{
  darkMode: boolean;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
}> = ({ toggleSidebar }) => {
  return (
    <header className="h-14 border-b-2 border-[#111] bg-[#f4f1ea] flex items-center px-3 sm:px-4 gap-3 shrink-0 sticky top-0 z-20">
      <button
        type="button"
        onClick={toggleSidebar}
        className="p-2 border-2 border-[#111] bg-white shadow-[2px_2px_0_#111] active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold tracking-tight truncate md:hidden">TonerTrack</p>
      </div>
      <span className="text-[11px] font-semibold uppercase tracking-wide text-[#5c5c5c] hidden sm:inline">
        Fleet board
      </span>
    </header>
  );
};

export default TopNav;
