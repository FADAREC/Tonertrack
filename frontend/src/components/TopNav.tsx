import React from 'react';
import { Menu } from 'lucide-react';

const TopNav: React.FC<{
  darkMode: boolean;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
}> = ({ toggleSidebar }) => {
  return (
    <header className="h-14 border-b border-white/5 bg-[rgba(11,19,43,0.75)] backdrop-blur-md flex items-center px-3 sm:px-4 gap-3 shrink-0 sticky top-0 z-20">
      <button
        type="button"
        onClick={toggleSidebar}
        className="p-2.5 rounded-xl text-[#8b9bb8] hover:bg-white/5 hover:text-[#f0f4ff] active:scale-95 transition"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate md:hidden">TonerTrack</p>
      </div>
      <span className="text-[11px] text-[#8b9bb8] hidden sm:inline tracking-wide">Single-office pilot</span>
    </header>
  );
};

export default TopNav;
