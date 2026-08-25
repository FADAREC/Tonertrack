import React from 'react';
import { Menu } from 'lucide-react';

const TopNav: React.FC<{
  darkMode: boolean;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
}> = ({ toggleSidebar }) => {
  return (
    <header className="h-14 border-b border-white/5 bg-[#0a0a0b]/80 backdrop-blur flex items-center px-4 gap-3 shrink-0">
      <button
        type="button"
        onClick={toggleSidebar}
        className="p-2 rounded-lg text-zinc-400 hover:bg-white/5 hover:text-zinc-100"
        aria-label="Toggle menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1" />
      <span className="text-xs text-zinc-600 hidden sm:inline">Single-office pilot</span>
    </header>
  );
};

export default TopNav;
