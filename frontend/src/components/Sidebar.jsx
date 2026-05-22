import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  ArrowLeftRight, 
  PiggyBank, 
  GraduationCap, 
  User, 
  Bell, 
  LogOut,
  Sparkles,
  BarChart2
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useFinanceStore } from '../store/useFinanceStore';

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const location = useLocation();
  const logout = useAuthStore(state => state.logout);
  const unreadCount = useFinanceStore(state => state.unreadCount);

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Transacciones', path: '/transacciones', icon: ArrowLeftRight },
    { name: 'Subcuentas & Metas', path: '/metas', icon: PiggyBank },
    { name: 'Reportes & Análisis', path: '/reportes', icon: BarChart2 },
    { name: 'Aprender', path: '/aprender', icon: GraduationCap },
    { name: 'Alertas', path: '/alertas', icon: Bell },
    { name: 'Mi Perfil', path: '/perfil', icon: User },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar Container */}
      <aside className={`
        fixed top-0 bottom-0 left-0 z-50 flex flex-col w-64 bg-white border-r border-slate-200 transition-transform duration-300 lg:translate-x-0 lg:static lg:h-screen
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Brand Header */}
        <div className="flex items-center gap-2.5 px-6 h-20 border-b border-slate-100 text-left">
          <div className="flex items-center justify-center w-9 h-9 rounded-md bg-[#0f172a] text-white shadow-sm">
            <Sparkles className="w-4.5 h-4.5" />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-[#0f172a]">
              FinGest
            </h1>
            <p className="text-[9px] uppercase font-black tracking-widest text-[#006c49]">
              AI Smart Finance
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => { if (isOpen) toggleSidebar(); }} // On mobile close on click if needed

                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-md font-bold text-xs transition-all duration-200 group text-left
                  ${isActive 
                    ? 'bg-[#eff4ff] text-[#0f172a] border border-[#e5eeff] shadow-sm' 
                    : 'text-[#64748b] hover:bg-slate-50 hover:text-[#0b1c30] border border-transparent'
                  }
                `}
              >
                <Icon className={`w-4 h-4 transition-transform duration-200 group-hover:scale-105 ${isActive ? 'text-[#0f172a]' : 'text-[#64748b] group-hover:text-[#0b1c30]'}`} />
                <span>{item.name}</span>
                {item.name === 'Dashboard' && unreadCount > 0 && (
                  <span className="ml-auto flex h-2 w-2 rounded-full bg-[#006c49] animate-pulse" />
                )}
                {item.name === 'Alertas' && unreadCount > 0 && (
                  <span className="ml-auto bg-[#0f172a] text-white text-[9px] font-black px-2 py-0.5 rounded-full animate-bounce">
                    {unreadCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Logout Footer */}
        <div className="p-4 border-t border-slate-100">
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-md font-bold text-xs text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-100 transition-all duration-200 group text-left"
          >
            <LogOut className="w-4 h-4 text-rose-650 transition-transform duration-200 group-hover:translate-x-0.5" />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
