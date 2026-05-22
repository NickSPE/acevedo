import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { useFinanceStore } from '../store/useFinanceStore';
import { 
  User, 
  Lock, 
  KeyRound, 
  Bell, 
  Save, 
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Mail,
  Phone
} from 'lucide-react';

const Profile = () => {
  const { user, updateProfile } = useAuthStore();
  const { notifications, fetchNotifications, markAsRead, markAllAsRead } = useFinanceStore();

  const [activeTab, setActiveTab] = useState('profile'); // 'profile', 'security', 'notifications'
  
  // Datos personales
  const [nombres, setNombres] = useState(user?.nombres || '');
  const [correo, setCorreo] = useState(user?.correo || '');
  const [telefono, setTelefono] = useState(user?.telefono || '');
  
  // Seguridad (Contraseña)
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPass, setShowPass] = useState(false);

  // Seguridad (PIN)
  const [newPin, setNewPin] = useState('');
  
  // Feedback
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchNotifications(true); // Cargar todas
  }, []);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setIsLoading(true);

    const payload = {
      nombres,
      correo,
      telefono: telefono ? parseInt(telefono) : null
    };

    const res = await updateProfile(payload);
    if (res.success) {
      setSuccessMsg('Perfil actualizado con éxito.');
      setTimeout(() => setSuccessMsg(''), 3000);
    } else {
      setErrorMsg(res.error);
    }
    setIsLoading(false);
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (newPassword !== confirmPassword) {
      setErrorMsg('Las contraseñas no coinciden.');
      return;
    }

    setIsLoading(true);
    try {
      await fetch('http://localhost:8000/api/usuarios/profile/', {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${useAuthStore.getState().token || ''}`
        },
        body: JSON.stringify({
          password: newPassword
        })
      });
      setSuccessMsg('Contraseña actualizada con éxito.');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      setErrorMsg('No se pudo cambiar la contraseña.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePin = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!/^\d{6}$/.test(newPin)) {
      setErrorMsg('El PIN debe tener exactamente 6 dígitos numéricos.');
      return;
    }

    setIsLoading(true);
    const res = await updateProfile({ pin_acceso_rapido: newPin });
    setIsLoading(false);

    if (res.success) {
      setSuccessMsg('PIN de acceso rápido actualizado con éxito.');
      setNewPin('');
      setTimeout(() => setSuccessMsg(''), 3000);
    } else {
      setErrorMsg(res.error);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="text-left">
        <h2 className="text-lg font-black text-[#0f172a] tracking-tight">Mi Perfil & Ajustes</h2>
        <p className="text-xs text-[#64748b] mt-0.5 font-bold">Gestiona tus datos de contacto, PIN de acceso rápido y seguridad.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-2">
        <button
          onClick={() => setActiveTab('profile')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'profile' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <User className="w-4 h-4" />
          <span>Datos Personales</span>
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'security' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <Lock className="w-4 h-4" />
          <span>Seguridad & PIN</span>
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'notifications' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <Bell className="w-4 h-4" />
          <span>Notificaciones</span>
        </button>
      </div>

      {/* Feedback alerts */}
      {successMsg && (
        <div className="p-3 text-xs font-bold rounded-md bg-emerald-50 border border-emerald-100 text-[#006c49] text-center animate-fade-in flex items-center justify-center gap-2">
          <CheckCircle className="w-4 h-4" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3 text-xs font-bold rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center animate-fade-in flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Tab Content: Profile Data */}
      {activeTab === 'profile' && (
        <form onSubmit={handleUpdateProfile} className="p-6 rounded-md bg-white border border-slate-200 space-y-4 text-left shadow-sm">
          <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider pb-2 border-b border-slate-100">Datos de Contacto</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Nombres</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  required
                  value={nombres}
                  onChange={(e) => setNombres(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none font-bold shadow-sm"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Correo Electrónico</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  required
                  disabled
                  value={correo}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-400 cursor-not-allowed focus:outline-none font-bold"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Teléfono Movil</label>
              <div className="relative">
                <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="tel"
                  placeholder="ej. 987654321"
                  value={telefono}
                  onChange={(e) => setTelefono(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none font-bold shadow-sm"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
          >
            <Save className="w-4 h-4" />
            <span>Guardar Cambios</span>
          </button>
        </form>
      )}

      {/* Tab Content: Security */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          {/* PIN Acceso Rápido Form */}
          <form onSubmit={handleUpdatePin} className="p-6 rounded-md bg-white border border-slate-200 space-y-4 text-left shadow-sm">
            <div className="pb-2 border-b border-slate-100">
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">PIN de Acceso Rápido</h3>
              <p className="text-[10px] text-[#64748b] mt-0.5 font-bold">Define un código numérico de 6 dígitos para iniciar sesión de manera rápida.</p>
            </div>
            
            <div className="space-y-1 max-w-xs">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Nuevo PIN (6 Dígitos)</label>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  maxLength="6"
                  placeholder="••••••"
                  value={newPin}
                  onChange={(e) => setNewPin(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none tracking-widest text-center font-black shadow-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
            >
              <Save className="w-4 h-4" />
              <span>Actualizar PIN</span>
            </button>
          </form>

          {/* Password Form */}
          <form onSubmit={handleChangePassword} className="p-6 rounded-md bg-white border border-slate-200 space-y-4 text-left shadow-sm">
            <div className="pb-2 border-b border-slate-100">
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Cambiar Contraseña</h3>
              <p className="text-[10px] text-[#64748b] mt-0.5 font-bold">Mantén tu cuenta protegida renovando tu contraseña de forma periódica.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Nueva Contraseña</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type={showPass ? 'text' : 'password'}
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none font-bold shadow-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#0f172a]"
                  >
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Confirmar Nueva Contraseña</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type={showPass ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none font-bold shadow-sm"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
            >
              <Save className="w-4 h-4" />
              <span>Establecer Contraseña</span>
            </button>
          </form>
        </div>
      )}

      {/* Tab Content: Notifications History */}
      {activeTab === 'notifications' && (
        <div className="p-6 rounded-md bg-white border border-slate-200 space-y-4 text-left shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Historial de Notificaciones</h3>
              <p className="text-[10px] text-[#64748b] mt-0.5 font-bold">Bitácora completa de alertas de la cuenta.</p>
            </div>
            {notifications.length > 0 && (
              <button 
                onClick={markAllAsRead}
                className="text-[10px] font-black text-[#006c49] hover:underline transition-colors uppercase tracking-wider"
              >
                Marcar todo leido
              </button>
            )}
          </div>

          <div className="divide-y divide-slate-100">
            {notifications.length === 0 ? (
              <div className="py-12 text-center text-slate-455 text-xs font-bold">
                No tienes notificaciones registradas en tu historial.
              </div>
            ) : (
              notifications.map((notif) => (
                <div 
                  key={notif.id}
                  onClick={() => !notif.read && markAsRead(notif.id)}
                  className={`
                    py-3.5 flex justify-between items-start gap-4 transition-colors cursor-pointer rounded-md px-2 -mx-2
                    ${notif.read ? 'opacity-70 hover:bg-slate-50' : 'bg-[#eff4ff]/60 hover:bg-[#eff4ff]'}
                  `}
                >
                  <div className="space-y-0.5 text-left">
                    <p className="text-xs font-black text-[#0f172a]">{notif.title}</p>
                    <p className="text-xs text-slate-500 font-bold">{notif.message}</p>
                    <span className="text-[9px] text-[#64748b] block font-black uppercase tracking-wider mt-1">
                      {new Date(notif.timestamp || notif.fecha_creacion).toLocaleString()}
                    </span>
                  </div>
                  {!notif.read && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[#0f172a] flex-shrink-0 animate-pulse mt-1.5" />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default Profile;
