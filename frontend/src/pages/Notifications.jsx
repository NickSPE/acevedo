import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useFinanceStore } from '../store/useFinanceStore';
import { useAuthStore } from '../store/useAuthStore';
import { 
  Bell, 
  Settings, 
  Mail, 
  Smartphone, 
  CheckCheck, 
  Info,
  Sparkles,
  Sliders,
  Loader2,
  Send
} from 'lucide-react';

const Notifications = () => {
  const user = useAuthStore(state => state.user);
  const simboloMoneda = user?.id_moneda?.simbolo || '$';
  
  const { 
    notifications, 
    unreadCount, 
    fetchNotifications, 
    markAsRead, 
    markAllAsRead 
  } = useFinanceStore();

  const [activeTab, setActiveTab] = useState('feed'); // 'feed', 'preferences'
  const [showAllNotifs, setShowAllNotifs] = useState(true);
  const [configList, setConfigList] = useState([]);
  const [isConfigLoading, setIsConfigLoading] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [testNotifLoading, setTestNotifLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState({ show: false, success: true, message: '' });

  useEffect(() => {
    fetchNotifications(showAllNotifs);
  }, [showAllNotifs]);

  useEffect(() => {
    if (activeTab === 'preferences') {
      fetchPreferences();
    }
  }, [activeTab]);

  const fetchPreferences = async () => {
    setIsConfigLoading(true);
    try {
      const response = await api.get('alertas-notificaciones/configuracion/');
      setConfigList(response.data || []);
    } catch (err) {
      console.error('Error fetching preferences:', err);
    } finally {
      setIsConfigLoading(false);
    }
  };

  const handlePreferenceToggle = (configId, field) => {
    setConfigList(prev => prev.map(c => {
      if (c.id === configId) {
        return { ...c, [field]: !c[field] };
      }
      return c;
    }));
  };

  const handleThresholdChange = (configId, value) => {
    setConfigList(prev => prev.map(c => {
      if (c.id === configId) {
        return { ...c, umbral_monto: parseFloat(value) || 0 };
      }
      return c;
    }));
  };

  const handleSavePreferences = async (e) => {
    e.preventDefault();
    setIsSavingConfig(true);
    setSaveStatus({ show: false, success: true, message: '' });

    try {
      const payload = {};
      configList.forEach(c => {
        const nombreTipo = c.tipo_notificacion_detalle?.nombre;
        if (nombreTipo) {
          payload[`email_${nombreTipo}`] = c.email_habilitado;
          payload[`push_${nombreTipo}`] = c.push_habilitado;
          payload[`activo_${nombreTipo}`] = c.activo;
          if (c.umbral_monto !== undefined) {
            payload[`umbral_${nombreTipo}`] = c.umbral_monto;
          }
        }
      });

      const response = await api.post('alertas-notificaciones/configuracion/', payload);
      setSaveStatus({
        show: true,
        success: true,
        message: response.data.message || 'Configuraciones guardadas exitosamente.'
      });
      await fetchNotifications(showAllNotifs);
    } catch (err) {
      console.error(err);
      setSaveStatus({
        show: true,
        success: false,
        message: 'Ocurrió un error al guardar las preferencias.'
      });
    } finally {
      setIsSavingConfig(false);
      setTimeout(() => setSaveStatus(prev => ({ ...prev, show: false })), 5000);
    }
  };

  const triggerTestNotification = async () => {
    setTestNotifLoading(true);
    try {
      await api.post('alertas-notificaciones/test/');
      await fetchNotifications(showAllNotifs);
    } catch (err) {
      console.error(err);
    } finally {
      setTestNotifLoading(false);
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'alta':
        return <span className="px-2 py-0.5 text-[9px] bg-rose-50 border border-rose-100 text-rose-600 font-extrabold uppercase rounded-md">Alta</span>;
      case 'media':
        return <span className="px-2 py-0.5 text-[9px] bg-amber-50 border border-amber-100 text-amber-600 font-extrabold uppercase rounded-md">Media</span>;
      default:
        return <span className="px-2 py-0.5 text-[9px] bg-slate-50 border border-slate-200 text-slate-500 font-extrabold uppercase rounded-md">Baja</span>;
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 text-left">
        <div>
          <h2 className="text-lg font-black text-[#0f172a] tracking-tight flex items-center gap-2">
            <Bell className="w-5 h-5 text-[#0f172a]" />
            <span>Alertas y Notificaciones</span>
          </h2>
          <p className="text-xs text-[#64748b] mt-0.5 font-bold">Gestiona tus preferencias de seguridad y actualizaciones financieras en tiempo real.</p>
        </div>
        <button
          onClick={triggerTestNotification}
          disabled={testNotifLoading}
          className="px-4 py-2 bg-white border border-slate-200 hover:border-slate-350 hover:bg-slate-50 rounded-md text-xs font-black uppercase tracking-wider text-[#0f172a] flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-50 shadow-sm"
        >
          {testNotifLoading ? <Loader2 className="w-4 h-4 animate-spin text-[#0f172a]" /> : <Send className="w-4 h-4 text-[#0f172a]" />}
          <span>Probar Alerta Inteligente</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-2">
        <button
          onClick={() => setActiveTab('feed')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'feed' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <Bell className="w-4 h-4" />
          <span>Historial de Alertas</span>
          {unreadCount > 0 && (
            <span className="px-1.5 py-0.5 bg-[#0f172a] text-white font-black text-[9px] rounded-md">
              {unreadCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'preferences' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <Settings className="w-4 h-4" />
          <span>Preferencias de Envío</span>
        </button>
      </div>

      {/* Feed Tab */}
      {activeTab === 'feed' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setShowAllNotifs(true)}
                className={`font-black transition-colors ${showAllNotifs ? 'text-[#0f172a]' : 'text-slate-400 hover:text-[#0f172a]'}`}
              >
                Todas las Alertas
              </button>
              <span className="text-slate-350">|</span>
              <button 
                onClick={() => setShowAllNotifs(false)}
                className={`font-black transition-colors ${!showAllNotifs ? 'text-[#0f172a]' : 'text-slate-400 hover:text-[#0f172a]'}`}
              >
                Últimas 3 Alertas
              </button>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="flex items-center gap-1 font-black text-[#006c49] hover:underline transition-colors uppercase tracking-wider text-[10px]"
              >
                <CheckCheck className="w-4 h-4" />
                <span>Marcar todas como leídas</span>
              </button>
            )}
          </div>

          <div className="space-y-3">
            {notifications.length === 0 ? (
              <div className="p-12 text-center rounded-md bg-white border border-slate-200 text-[#64748b] flex flex-col items-center justify-center gap-2 shadow-sm">
                <Info className="w-7 h-7 text-slate-305" />
                <p className="text-xs font-bold">No tienes alertas o notificaciones pendientes en este momento.</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div 
                  key={notif.id}
                  onClick={() => notif.estado !== 'leida' && markAsRead(notif.id)}
                  className={`
                    p-4 rounded-md border text-left flex gap-4 transition-all hover:bg-slate-50/50 cursor-pointer shadow-sm
                    ${notif.estado !== 'leida' 
                      ? 'bg-[#eff4ff]/60 border-[#c6c6cd] border-l-4 border-l-[#0f172a]' 
                      : 'bg-white border-slate-200'
                    }
                  `}
                >
                  <div className={`
                    w-9 h-9 rounded-md flex items-center justify-center flex-shrink-0
                    ${notif.prioridad === 'alta' 
                      ? 'bg-rose-50 text-rose-500' 
                      : notif.prioridad === 'media'
                      ? 'bg-amber-50 text-amber-500'
                      : 'bg-slate-50 text-slate-450'
                    }
                  `}>
                    <Bell className="w-4.5 h-4.5" />
                  </div>
                  
                  <div className="flex-1 space-y-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h4 className="text-xs font-black text-[#0f172a] flex items-center gap-2">
                        <span>{notif.titulo}</span>
                        {notif.estado !== 'leida' && (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#0f172a]" />
                        )}
                      </h4>
                      <span className="text-[10px] text-slate-450 font-bold">{notif.relative_time || new Date(notif.fecha_creacion).toLocaleDateString()}</span>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed font-bold">{notif.mensaje}</p>
                    <div className="flex items-center gap-3 pt-1">
                      {getPriorityBadge(notif.prioridad)}
                      {notif.categoria && (
                        <span className="text-[9px] text-[#64748b] font-black uppercase tracking-widest">{notif.categoria}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pro Tip */}
          <div className="p-4 rounded-md bg-emerald-50 border border-emerald-100 text-left flex gap-3 relative overflow-hidden shadow-sm">
            <Sparkles className="w-4.5 h-4.5 text-[#006c49] flex-shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <h4 className="text-xs font-black text-[#006c49] uppercase tracking-wider">Tu Perspectiva de Ahorro</h4>
              <p className="text-xs text-[#064e3b] leading-relaxed font-bold">
                ¿Sabías que configurar tu umbral de alerta en <strong className="text-[#006c49]">{simboloMoneda}0</strong> te permite ser notificado de cada centavo gastado? Esto previene fraudes y te mantiene 100% consciente de tus salidas diarias.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="space-y-6">
          {saveStatus.show && (
            <div className={`p-3 rounded-md text-xs font-bold text-left flex items-center gap-2 ${saveStatus.success ? 'bg-emerald-50 border border-emerald-100 text-[#006c49]' : 'bg-rose-50 border border-rose-100 text-rose-600'}`}>
              <Info className="w-4 h-4 flex-shrink-0" />
              <span>{saveStatus.message}</span>
            </div>
          )}

          {isConfigLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-7 h-7 animate-spin text-[#0f172a]" />
            </div>
          ) : (
            <form onSubmit={handleSavePreferences} className="space-y-6 text-left">
              <div className="p-6 rounded-md bg-white border border-slate-200 space-y-6 shadow-sm">
                <div className="flex items-center gap-2 pb-4 border-b border-slate-100">
                  <Sliders className="w-4.5 h-4.5 text-[#0f172a]" />
                  <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Canales y Categorías de Notificaciones</h3>
                </div>

                <div className="divide-y divide-slate-100 space-y-5">
                  {configList.map((config) => (
                    <div key={config.id} className="pt-5 first:pt-0 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                      
                      {/* Name & Desc */}
                      <div className="md:col-span-5 space-y-0.5">
                        <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">
                          {config.tipo_notificacion_detalle?.nombre?.replace(/_/g, ' ') || 'Actualización General'}
                        </h4>
                        <p className="text-[11px] text-[#64748b] leading-relaxed font-bold">
                          {config.tipo_notificacion_detalle?.descripcion || 'Notificaciones del sistema y actualizaciones importantes.'}
                        </p>
                      </div>

                      {/* Toggles */}
                      <div className="md:col-span-4 flex items-center gap-6 justify-start md:justify-center">
                        <label className="flex items-center gap-2 cursor-pointer group">
                          <input 
                            type="checkbox"
                            checked={config.email_habilitado}
                            onChange={() => handlePreferenceToggle(config.id, 'email_habilitado')}
                            className="w-4 h-4 rounded text-[#0f172a] bg-white border-slate-300 focus:ring-[#0f172a]"
                          />
                          <span className="text-[11px] font-black text-[#64748b] group-hover:text-[#0b1c30] flex items-center gap-1">
                            <Mail className="w-3.5 h-3.5 text-slate-400" /> Email
                          </span>
                        </label>

                        <label className="flex items-center gap-2 cursor-pointer group">
                          <input 
                            type="checkbox"
                            checked={config.push_habilitado}
                            onChange={() => handlePreferenceToggle(config.id, 'push_habilitado')}
                            className="w-4 h-4 rounded text-[#0f172a] bg-white border-slate-300 focus:ring-[#0f172a]"
                          />
                          <span className="text-[11px] font-black text-[#64748b] group-hover:text-[#0b1c30] flex items-center gap-1">
                            <Smartphone className="w-3.5 h-3.5 text-slate-400" /> Push (App)
                          </span>
                        </label>
                      </div>

                      {/* Threshold input */}
                      <div className="md:col-span-3 space-y-1">
                        <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Umbral Mínimo ({simboloMoneda})</label>
                        <input
                          type="number"
                          value={config.umbral_monto || 0}
                          onChange={(e) => handleThresholdChange(config.id, e.target.value)}
                          className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 font-bold shadow-sm"
                          placeholder="Monto mínimo..."
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end pt-1">
                <button
                  type="submit"
                  disabled={isSavingConfig}
                  className="px-5 py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50 shadow-sm"
                >
                  {isSavingConfig && <Loader2 className="w-4 h-4 animate-spin text-white" />}
                  <span>Guardar Preferencias</span>
                </button>
              </div>
            </form>
          )}
        </div>
      )}

    </div>
  );
};

export default Notifications;
