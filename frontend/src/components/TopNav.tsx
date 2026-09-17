import React from 'react';
import { Link } from 'react-router-dom';
import { Menu } from 'lucide-react';
import BrandMark from './BrandMark';

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
      {/* Logo only on small screens - sidebar already brands desktop */}
      <Link
        to="/"
        className="flex items-center gap-2 min-w-0 hover:opacity-90 md:hidden"
        aria-label="TonerTrack home"
      >
        <BrandMark size={28} wordmarkClassName="tt-display text-base tracking-wide" />
      </Link>
      <div className="flex-1" />
    </header>
  );
};

export default TopNav;
