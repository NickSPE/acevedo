import React, { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { Sparkles, Wallet, KeyRound, Phone, ArrowRight, Loader2, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Onboarding = () => {
  const { completeOnboarding } = useAuthStore();
  const navigate = useNavigate();

  const [step, setStep] = useState(1); // 1: Saldo Inicial, 2: PIN de Seguridad, 3: Teléfono
  const [saldoInicial, setSaldoInicial] = useState('1000');
  const [nombreCuenta, setNombreCuenta] = useState('Mi Cuenta Principal');
  
  const [pin, setPin] = useState(new Array(6).fill(''));
  const [telefono, setTelefono] = useState('');
  
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePinChange = (element, index) => {
    if (isNaN(element.value)) return false;

    const newPin = [...pin];
    newPin[index] = element.value;
    setPin(newPin);

    // Auto-focus next input
    if (element.nextSibling && element.value !== '') {
      element.nextSibling.focus();
    }
  };

  const handlePinKeyDown = (e, index) => {
    if (e.key === 'Backspace' && !pin[index] && e.target.previousSibling) {
      e.target.previousSibling.focus();
    }
  };

  const handleSkip = async () => {
    setIsLoading(true);
    const res = await completeOnboarding({ skipped: true });
    setIsLoading(false);
    if (res.success) {
      navigate('/');
    } else {
      setError(res.error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const pinString = pin.join('');
    if (pinString.length > 0 && pinString.length !== 6) {
      setError('El PIN de seguridad debe tener exactamente 6 dígitos.');
      return;
    }

    const payload = {
      saldo_inicial: saldoInicial,
      nombre_cuenta: nombreCuenta,
      pin_acceso_rapido: pinString,
      telefono: telefono
    };

    setIsLoading(true);
    const res = await completeOnboarding(payload);
    setIsLoading(false);

    if (res.success) {
      navigate('/');
    } else {
      setError(res.error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4 relative overflow-hidden text-left">
      {/* Decorative Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl -z-10 animate-pulse-subtle" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10 animate-pulse-subtle" />

      {/* Main Container */}
      <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-8 space-y-6 relative z-10">
        
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-450 text-white shadow-xl shadow-brand-500/15 mb-1">
            <Sparkles className="w-6 h-6 animate-spin-slow" />
          </div>
          <h2 className="text-xl font-extrabold tracking-tight text-white">
            Configura tu Espacio
          </h2>
          <p className="text-xs text-slate-455">
            Personaliza tu experiencia de FinGest en 3 rápidos pasos.
          </p>
        </div>

        {/* Step progress dots */}
        <div className="flex justify-center gap-1.5 py-1">
          {[1, 2, 3].map((s) => (
            <div 
              key={s} 
              className={`h-1.5 rounded-full transition-all duration-300 ${step === s ? 'w-6 bg-brand-500' : 'w-2 bg-slate-800'}`}
            />
          ))}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 text-xs font-semibold rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-center animate-fade-in">
            {error}
          </div>
        )}

        {/* Form Body */}
        <div className="space-y-4">
          
          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 rounded-2xl bg-brand-600/5 border border-brand-500/10 flex gap-3 text-xs text-slate-350">
                <Wallet className="w-5 h-5 text-brand-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-bold text-white mb-0.5">Saldo de Bienvenida</h4>
                  <p className="leading-relaxed">Establece el balance inicial de tu cuenta de débito principal para iniciar tus presupuestos.</p>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-450 uppercase tracking-wider pl-1">Nombre de Cuenta</label>
                <input
                  type="text"
                  value={nombreCuenta}
                  onChange={(e) => setNombreCuenta(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 focus:border-brand-500/50 rounded-xl text-xs text-white focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-450 uppercase tracking-wider pl-1">Saldo Disponible Inicial</label>
                <input
                  type="number"
                  value={saldoInicial}
                  onChange={(e) => setSaldoInicial(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 focus:border-brand-500/50 rounded-xl text-xs text-white focus:outline-none font-bold"
                />
              </div>

              <button
                onClick={() => setStep(2)}
                className="w-full flex items-center justify-center gap-2 py-3 bg-brand-600 hover:bg-brand-550 text-white rounded-xl text-xs font-bold active:scale-[0.99] transition-all"
              >
                <span>Siguiente Paso</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 rounded-2xl bg-brand-600/5 border border-brand-500/10 flex gap-3 text-xs text-slate-350">
                <KeyRound className="w-5 h-5 text-brand-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-bold text-white mb-0.5">PIN de Acceso Rápido</h4>
                  <p className="leading-relaxed">Establece una clave numérica de 6 dígitos para iniciar sesión velozmente desde cualquier dispositivo móvil.</p>
                </div>
              </div>

              <div className="space-y-3 text-center">
                <div className="flex justify-center gap-2">
                  {pin.map((digit, index) => (
                    <input
                      key={index}
                      type="password"
                      maxLength="1"
                      value={digit}
                      onChange={(e) => handlePinChange(e.target, index)}
                      onKeyDown={(e) => handlePinKeyDown(e, index)}
                      onFocus={(e) => e.target.select()}
                      className="w-10 h-12 bg-slate-950 border border-slate-850 focus:border-brand-500/50 text-center rounded-lg text-lg font-bold text-white focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition-all"
                    />
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 py-3 bg-slate-800 hover:bg-slate-750 text-slate-300 rounded-xl text-xs font-bold transition-all"
                >
                  Atrás
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-[2] py-3 bg-brand-600 hover:bg-brand-550 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1 transition-all"
                >
                  <span>Configurar Teléfono</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 rounded-2xl bg-brand-600/5 border border-brand-500/10 flex gap-3 text-xs text-slate-350">
                <Phone className="w-5 h-5 text-brand-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-bold text-white mb-0.5">Número de Teléfono</h4>
                  <p className="leading-relaxed">Ingresa tu número celular para recibir notificaciones importantes y alertas críticas directamente.</p>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-450 uppercase tracking-wider pl-1">Número de Celular</label>
                <input
                  type="tel"
                  placeholder="ej. 987654321"
                  value={telefono}
                  onChange={(e) => setTelefono(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 focus:border-brand-500/50 rounded-xl text-xs text-white focus:outline-none"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 py-3 bg-slate-800 hover:bg-slate-750 text-slate-300 rounded-xl text-xs font-bold transition-all"
                >
                  Atrás
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isLoading}
                  className="flex-[2] py-3 bg-gradient-to-r from-brand-600 to-emerald-500 hover:from-brand-550 hover:to-emerald-450 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1 transition-all disabled:opacity-50"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <span>Finalizar Onboarding</span>
                      <CheckCircle className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Skip button */}
        <div className="pt-2 text-center">
          <button 
            onClick={handleSkip} 
            disabled={isLoading}
            className="text-[10px] font-black text-slate-500 hover:text-slate-300 uppercase tracking-widest transition-colors"
          >
            Saltar configuración por ahora
          </button>
        </div>

      </div>
    </div>
  );
};

export default Onboarding;
