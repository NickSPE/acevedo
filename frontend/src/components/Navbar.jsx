import React, { useState, useEffect, useRef } from 'react';
import { Menu, Bell, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useFinanceStore } from '../store/useFinanceStore';
import { Link } from 'react-router-dom';

const Navbar = ({ toggleSidebar }) => {
  const user = useAuthStore(state => state.user);
  const { notifications, unreadCount, fetchNotifications, markAsRead, markAllAsRead } = useFinanceStore();
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef(null);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(() => fetchNotifications(), 30000); // Refrescar notificaciones cada 30 segundos
    return () => clearInterval(interval);
  }, []);

  // Cerrar notificaciones al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Formatear la fecha relativa
  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours} hr`;
    return date.toLocaleDateString();
  };

  const getNotifIcon = (priority) => {
    switch (priority) {
      case 'alta':
        return <AlertTriangle className="w-4 h-4 text-rose-500" />;
      case 'media':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <header className="flex items-center justify-between px-6 h-20 bg-white border-b border-slate-200 sticky top-0 z-30">
      {/* Left side: Hamburger (mobile) & Welcome message */}
      <div className="flex items-center gap-4 text-left">
        <button 
          onClick={toggleSidebar}
          className="p-2 rounded-md text-slate-500 hover:bg-slate-50 hover:text-[#0b1c30] lg:hidden transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="text-left">
          <h2 className="text-sm font-black text-[#0f172a]">
            ¡Hola, {user?.nombres || 'Usuario'}! 👋
          </h2>
          <p className="text-[11px] text-[#64748b] hidden sm:block font-bold">
            Bienvenido de vuelta a tu centro financiero inteligente.
          </p>
        </div>
      </div>

      {/* Right side: Quick Info & Notifications */}
      <div className="flex items-center gap-4">
        {/* Moneda e Info Rápida */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 border border-slate-200 text-[11px] font-bold text-[#64748b]">
          <span>Moneda principal:</span>
          <span className="text-[#006c49] font-black">
            {user?.id_moneda?.simbolo || '$'} ({user?.id_moneda?.codigo || 'USD'})
          </span>
        </div>

        {/* Notificaciones Dropdown */}
        <div className="relative" ref={notifRef}>
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-md bg-slate-50 text-[#64748b] hover:text-[#0b1c30] border border-slate-200 hover:bg-slate-100 hover:border-slate-350 transition-all relative shadow-sm"
          >
            <Bell className="w-4.5 h-4.5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex items-center justify-center h-4.5 min-w-[18px] px-1 rounded-full bg-[#0f172a] text-[9px] font-black text-white border-2 border-white shadow-sm">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Tray Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 sm:w-96 rounded-md bg-white border border-slate-200 shadow-xl overflow-hidden z-50 animate-fade-in">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
                <span className="text-xs font-black text-[#0b1c30]">Notificaciones Recientes</span>
                {unreadCount > 0 && (
                  <button 
                    onClick={markAllAsRead}
                    className="text-[10px] font-black text-[#006c49] hover:underline transition-colors uppercase tracking-wider"
                  >
                    Marcar todo leído
                  </button>
                )}
              </div>

              {/* Items List */}
              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                    <CheckCircle2 className="w-7 h-7 mb-1.5 text-slate-300" />
                    <p className="text-[11px] font-bold">Estás al día. Sin notificaciones.</p>
                  </div>
                ) : (
                  notifications.map((notif) => {
                    const isLeida = notif.estado === 'leida';
                    return (
                      <div 
                        key={notif.id} 
                        onClick={() => !isLeida && markAsRead(notif.id)}
                        className={`
                          p-4 flex gap-3 text-left transition-colors cursor-pointer
                          ${isLeida ? 'bg-white hover:bg-slate-50/50' : 'bg-[#eff4ff]/60 hover:bg-[#eff4ff] border-l-2 border-l-[#0f172a]'}
                        `}
                      >
                        <div className="mt-0.5 flex-shrink-0">
                          {getNotifIcon(notif.prioridad)}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex justify-between items-start">
                            <p className={`text-xs font-bold ${isLeida ? 'text-slate-500' : 'text-[#0f172a]'}`}>
                              {notif.titulo}
                            </p>
                            <span className="text-[9px] text-slate-400 flex-shrink-0 font-bold ml-2">
                              {formatTime(notif.fecha_creacion)}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 leading-relaxed font-bold">
                            {notif.mensaje}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 text-center">
                <Link 
                  to="/alertas" 
                  onClick={() => setShowNotifications(false)}
                  className="text-[10px] font-black text-slate-500 hover:text-[#0b1c30] transition-colors uppercase tracking-wider"
                >
                  Ver todas las alertas
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* User Mini Avatar */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-md bg-[#0f172a] flex items-center justify-center text-white font-black text-xs shadow-sm">
            {user?.nombres?.charAt(0).toUpperCase() || 'U'}
          </div>
          <span className="text-xs font-black text-[#0f172a] hidden md:block">
            {user?.nombres}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
