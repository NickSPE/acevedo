import React, { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { Sparkles, Eye, EyeOff, Lock, Mail, ArrowRight, Loader2, KeyRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const Login = () => {
  const login = useAuthStore(state => state.login);
  const loginWithPin = useAuthStore(state => state.loginWithPin);
  const isLoading = useAuthStore(state => state.isLoading);
  const navigate = useNavigate();

  const [loginMode, setLoginMode] = useState('standard'); // 'standard' o 'pin'
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [pinDigits, setPinDigits] = useState(new Array(6).fill(''));
  const [error, setError] = useState('');

  // Estados para recuperación de contraseña
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetStep, setResetStep] = useState(1); // 1: email, 2: code & new pass
  const [resetSuccessMessage, setResetSuccessMessage] = useState('');
  const [resetError, setResetError] = useState('');
  const [isResetLoading, setIsResetLoading] = useState(false);

  const handleStandardSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!correo || !password) {
      setError('Por favor, ingresa tu correo y contraseña.');
      return;
    }

    const res = await login(correo, password);
    if (res.success) {
      navigate('/');
    } else {
      setError(res.error);
    }
  };

  const handlePinChange = (element, index) => {
    if (isNaN(element.value)) return false;

    const newPinDigits = [...pinDigits];
    newPinDigits[index] = element.value;
    setPinDigits(newPinDigits);

    // Auto-focus next input
    if (element.nextSibling && element.value !== '') {
      element.nextSibling.focus();
    }
  };

  const handlePinKeyDown = (e, index) => {
    if (e.key === 'Backspace' && !pinDigits[index] && e.target.previousSibling) {
      e.target.previousSibling.focus();
    }
  };

  const handlePinSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const pin = pinDigits.join('');
    if (pin.length !== 6) {
      setError('Por favor, introduce los 6 dígitos de tu PIN.');
      return;
    }

    const res = await loginWithPin(pin);
    if (res.success) {
      navigate('/');
    } else {
      setError(res.error);
    }
  };

  // Enviar código de recuperación
  const handleSendResetCode = async (e) => {
    e.preventDefault();
    setResetError('');
    setIsResetLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/usuarios/password-reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail, action: 'send_code' })
      });
      const data = await response.json();

      if (data.success) {
        setResetStep(2);
      } else {
        setResetError(data.message || 'Error al enviar el código de recuperación.');
      }
    } catch (err) {
      setResetError('Error de red al solicitar la recuperación.');
    } finally {
      setIsResetLoading(false);
    }
  };

  // Restablecer contraseña con código
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setResetError('');
    setIsResetLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/usuarios/password-reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: resetEmail, 
          codigo: resetCode, 
          nueva_password: resetNewPassword,
          action: 'reset_password' 
        })
      });
      const data = await response.json();

      if (data.success) {
        setResetSuccessMessage('Contraseña restablecida con éxito. Ya puedes iniciar sesión.');
        setTimeout(() => {
          setShowResetModal(false);
          setResetStep(1);
          setResetEmail('');
          setResetCode('');
          setResetNewPassword('');
          setResetSuccessMessage('');
        }, 3000);
      } else {
        setResetError(data.message || 'Código de recuperación inválido.');
      }
    } catch (err) {
      setResetError('Error de red al actualizar la contraseña.');
    } finally {
      setIsResetLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 relative overflow-hidden">
      
      {/* Main Container */}
      <div className="w-full max-w-md rounded-md bg-white border border-slate-200 shadow-lg p-8 space-y-6 relative z-10 text-left">
        
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-[#0f172a] text-white shadow-sm mb-1">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-black tracking-tight text-[#0f172a]">
            Bienvenido a FinGest
          </h2>
          <p className="text-xs text-[#64748b] font-bold">
            Gestiona tus finanzas de forma segura con IA
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex p-1 rounded-md bg-slate-100 border border-slate-200">
          <button
            onClick={() => { setLoginMode('standard'); setError(''); }}
            className={`flex-1 py-2 text-xs font-black rounded-md transition-all ${loginMode === 'standard' ? 'bg-[#0f172a] text-white shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
          >
            Acceso Estándar
          </button>
          <button
            onClick={() => { setLoginMode('pin'); setError(''); }}
            className={`flex-1 py-2 text-xs font-black rounded-md transition-all ${loginMode === 'pin' ? 'bg-[#0f172a] text-white shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
          >
            PIN Rápido
          </button>
        </div>

        {/* Errors Alert */}
        {error && (
          <div className="p-3 text-xs font-bold rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center animate-fade-in">
            {error}
          </div>
        )}

        {/* Form Standard */}
        {loginMode === 'standard' ? (
          <form onSubmit={handleStandardSubmit} className="space-y-4">
            <div className="space-y-1 text-left">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="email"
                  placeholder="ejemplo@correo.com"
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none transition-all font-bold shadow-sm"
                />
              </div>
            </div>

            <div className="space-y-1 text-left">
              <div className="flex justify-between items-center px-0.5">
                <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest">
                  Contraseña
                </label>
                <button
                  type="button"
                  onClick={() => setShowResetModal(true)}
                  className="text-[10px] text-[#64748b] hover:text-[#0f172a] font-bold hover:underline"
                >
                  ¿La olvidaste?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-11 py-2.5 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none transition-all font-bold shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#0f172a] transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider active:scale-[0.99] transition-all disabled:opacity-50 disabled:pointer-events-none shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="w-4.5 h-4.5 animate-spin" />
              ) : (
                <>
                  <span>Ingresar a la Plataforma</span>
                  <ArrowRight className="w-4.5 h-4.5" />
                </>
              )}
            </button>
          </form>
        ) : (
          /* Form PIN Login */
          <form onSubmit={handlePinSubmit} className="space-y-6">
            <div className="space-y-3 text-center">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">
                Introduce tu PIN de 6 dígitos
              </label>
              <div className="flex justify-center gap-2">
                {pinDigits.map((digit, index) => (
                  <input
                    key={index}
                    type="password"
                    maxLength="1"
                    value={digit}
                    onChange={(e) => handlePinChange(e.target, index)}
                    onKeyDown={(e) => handlePinKeyDown(e, index)}
                    onFocus={(e) => e.target.select()}
                    className="w-11 h-12 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 text-center rounded-md text-lg font-black text-[#0f172a] focus:outline-none transition-all shadow-sm"
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="w-4.5 h-4.5 animate-spin" />
              ) : (
                <>
                  <span>Verificar PIN e Ingresar</span>
                  <ArrowRight className="w-4.5 h-4.5" />
                </>
              )}
            </button>
          </form>
        )}

        {/* Register Redirect footer */}
        <div className="pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500 font-bold">
            ¿No tienes una cuenta aún?{' '}
            <Link to="/registro" className="text-[#006c49] font-black hover:underline">
              Crea una aquí
            </Link>
          </p>
        </div>
      </div>

      {/* Password Reset Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setShowResetModal(false)} />
          <div className="relative w-full max-w-sm rounded-md bg-white border border-slate-200 p-6 shadow-2xl z-10 animate-slide-up space-y-4">
            <div className="flex items-center gap-2.5 pb-2 border-b border-slate-100">
              <KeyRound className="w-4.5 h-4.5 text-[#0f172a]" />
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Recuperar Contraseña</h3>
            </div>

            {resetError && (
              <div className="p-2 text-[10px] rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center font-bold">
                {resetError}
              </div>
            )}
            {resetSuccessMessage && (
              <div className="p-2 text-[10px] rounded-md bg-emerald-50 border border-emerald-100 text-[#006c49] text-center font-bold">
                {resetSuccessMessage}
              </div>
            )}

            {resetStep === 1 ? (
              <form onSubmit={handleSendResetCode} className="space-y-4">
                <p className="text-[11px] text-[#64748b] leading-relaxed font-bold">
                  Introduce tu correo electrónico. Si coincide con una cuenta activa, te enviaremos un código de 6 dígitos.
                </p>
                <div className="space-y-1">
                  <input
                    type="email"
                    required
                    placeholder="ejemplo@correo.com"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isResetLoading}
                  className="w-full py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-50 shadow-sm"
                >
                  {isResetLoading ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Enviar Código'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleResetPassword} className="space-y-4">
                <p className="text-[11px] text-[#64748b] leading-relaxed font-bold">
                  Hemos enviado el código a <strong>{resetEmail}</strong>. Introdúcelo abajo junto con tu nueva contraseña.
                </p>
                <div className="space-y-3">
                  <div>
                    <input
                      type="text"
                      required
                      placeholder="Código de 6 dígitos"
                      value={resetCode}
                      onChange={(e) => setResetCode(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-mono tracking-widest text-center font-bold"
                    />
                  </div>
                  <div>
                    <input
                      type="password"
                      required
                      placeholder="Nueva Contraseña"
                      value={resetNewPassword}
                      onChange={(e) => setResetNewPassword(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setResetStep(1)}
                    className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-150 text-slate-700 rounded-md text-xs font-black uppercase tracking-wider"
                  >
                    Atrás
                  </button>
                  <button
                    type="submit"
                    disabled={isResetLoading}
                    className="flex-1 py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-50 shadow-sm"
                  >
                    {isResetLoading ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Restablecer'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Login;
