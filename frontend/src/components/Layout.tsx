import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Calendar, Trophy, Settings } from 'lucide-react';
import clsx from 'clsx';

const SidebarItem = ({ to, icon: Icon, label }: { to: string; icon: any; label: string }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      clsx(
        'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
        isActive
          ? 'bg-blue-600 text-white'
          : 'text-gray-400 hover:bg-gray-800 hover:text-white'
      )
    }
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </NavLink>
);

export const Layout = () => {
  return (
    <div className="flex h-screen bg-[#121212] text-white font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-[#1E1E1E] border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Trophy className="text-blue-500" />
            NFL Monte Carlo
          </h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <SidebarItem to="/" icon={LayoutDashboard} label="Standings" />
          <SidebarItem to="/schedule" icon={Calendar} label="Schedule" />
          <SidebarItem to="/simulation" icon={Settings} label="Simulation" />
        </nav>
        
        <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
          v0.1.0
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  );
};

