import React, { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { Sparkles, Mail, Lock, User, Loader2, ArrowRight, ArrowLeft, ShieldCheck } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const Register = () => {
  const register = useAuthStore(state => state.register);
  const isLoading = useAuthStore(state => state.isLoading);
  const navigate = useNavigate();

  const [step, setStep] = useState(1); // 1: Datos principales y código, 2: Validación final
  const [nombres, setNombres] = useState('');
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Enviar código de verificación de correo
  const handleSendCode = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!nombres || !correo) {
      setError('Por favor, completa tu nombre y correo.');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/usuarios/register/send-code/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombres, correo })
      });
      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess('¡Código de verificación enviado! Revisa tu bandeja de entrada.');
        setStep(2);
      } else {
        setError(data.error || 'Error al enviar el código de verificación.');
      }
    } catch (err) {
      setError('Error de red al intentar enviar el código.');
    }
  };

  // Enviar el formulario completo de registro
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!verificationCode || !password) {
      setError('Por favor, ingresa el código y define tu contraseña.');
      return;
    }

    const registerData = {
      nombres,
      correo,
      password,
      codigo_verificacion: verificationCode
    };

    const res = await register(registerData);
    if (res.success) {
      setSuccess(res.message || '¡Registro completado con éxito!');
      setTimeout(() => {
        navigate('/login');
      }, 2500);
    } else {
      setError(res.error || 'Ocurrió un error al registrar tu usuario.');
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
            Crea tu Cuenta
          </h2>
          <p className="text-xs text-[#64748b] font-bold">
            Regístrate en pocos segundos y comienza a ahorrar inteligentemente
          </p>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="p-3 text-xs font-bold rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center animate-fade-in">
            {error}
          </div>
        )}
        {success && (
          <div className="p-3 text-xs font-bold rounded-md bg-emerald-50 border border-emerald-100 text-[#006c49] text-center animate-fade-in">
            {success}
          </div>
        )}

        {/* Form Step 1: Nombres, Correo, Enviar Código */}
        {step === 1 ? (
          <form onSubmit={handleSendCode} className="space-y-4">
            <div className="space-y-1 text-left">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">
                Nombre Completo
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="text"
                  required
                  placeholder="Tu nombre completo"
                  value={nombres}
                  onChange={(e) => setNombres(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none transition-all font-bold shadow-sm"
                />
              </div>
            </div>

            <div className="space-y-1 text-left">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="email"
                  required
                  placeholder="ejemplo@correo.com"
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none transition-all font-bold shadow-sm"
                />
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
                  <span>Enviar Código al Correo</span>
                  <ArrowRight className="w-4.5 h-4.5" />
                </>
              )}
            </button>
          </form>
        ) : (
          /* Form Step 2: Ingresar Código y Contraseña */
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            <p className="text-[11px] text-[#64748b] text-center leading-relaxed font-bold">
              Introduce el código de 6 dígitos que te enviamos y define tu nueva contraseña.
            </p>

            <div className="space-y-1 text-left">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">
                Código de Verificación
              </label>
              <div className="relative">
                <ShieldCheck className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="text"
                  required
                  maxLength="6"
                  placeholder="123456"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none transition-all font-mono tracking-widest text-center text-sm font-bold shadow-sm"
                />
              </div>
            </div>

            <div className="space-y-1 text-left">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">
                Contraseña Segura
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="password"
                  required
                  placeholder="Define tu contraseña"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 rounded-md text-xs text-[#0f172a] focus:outline-none transition-all font-bold shadow-sm"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => { setStep(1); setError(''); }}
                className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-150 text-slate-700 rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1 active:scale-[0.99] transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Atrás</span>
              </button>
              
              <button
                type="submit"
                disabled={isLoading}
                className="flex-[2] py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Completar Registro'}
              </button>
            </div>
          </form>
        )}

        {/* Login Redirect Footer */}
        <div className="pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500 font-bold">
            ¿Ya tienes una cuenta registrada?{' '}
            <Link to="/login" className="text-[#006c49] font-black hover:underline">
              Inicia sesión aquí
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
