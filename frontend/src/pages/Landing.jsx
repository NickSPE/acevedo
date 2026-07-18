import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  PiggyBank,
  BarChart2,
  Target,
  Shield,
  Zap,
  Star,
  ChevronRight,
  Coins,
  GraduationCap,
  Bell,
  CheckCircle2,
} from 'lucide-react';

// ── Animated counter hook ────────────────────────────────────────────────────
function useCounter(end, duration = 1800, start = 0) {
  const [count, setCount] = useState(start);
  const startTimeRef = useRef(null);
  const frameRef = useRef(null);

  useEffect(() => {
    const animate = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(start + (end - start) * eased));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [end, duration, start]);

  return count;
}

// ── Feature Card ────────────────────────────────────────────────────────────
const FeatureCard = ({ icon: Icon, title, desc, accent }) => (
  <div className="group relative flex flex-col gap-4 p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 overflow-hidden">
    <div
      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
      style={{ background: `radial-gradient(circle at 20% 20%, ${accent}08 0%, transparent 70%)` }}
    />
    <div
      className="w-11 h-11 rounded-xl flex items-center justify-center shadow-sm"
      style={{ backgroundColor: `${accent}15`, color: accent }}
    >
      <Icon className="w-5 h-5" />
    </div>
    <div>
      <h3 className="text-sm font-black text-[#0f172a] mb-1">{title}</h3>
      <p className="text-xs text-slate-500 leading-relaxed font-medium">{desc}</p>
    </div>
  </div>
);

// ── Stat Card ───────────────────────────────────────────────────────────────
const StatCard = ({ value, suffix, label, color }) => {
  const count = useCounter(value);
  return (
    <div className="text-center">
      <p className="text-4xl font-black tracking-tight" style={{ color }}>
        {count.toLocaleString()}{suffix}
      </p>
      <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mt-1">{label}</p>
    </div>
  );
};

// ── Main Landing Component ───────────────────────────────────────────────────
const Landing = () => {
  const { isAuthenticated, isLoading } = useAuthStore();
  const navigate = useNavigate();

  // If already logged in, go to dashboard
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  const features = [
    {
      icon: PiggyBank,
      title: 'Subcuentas Inteligentes',
      desc: 'Separa tu dinero en categorías personales o de negocio. Controla cada centavo con claridad.',
      accent: '#0f172a',
    },
    {
      icon: Target,
      title: 'Metas de Ahorro',
      desc: 'Define objetivos con plazos y frecuencias de aporte. Sigue tu progreso en tiempo real.',
      accent: '#006c49',
    },
    {
      icon: BarChart2,
      title: 'Reportes & Análisis',
      desc: 'Visualiza tus finanzas con gráficas claras. Entiende tus hábitos y toma mejores decisiones.',
      accent: '#4f46e5',
    },
    {
      icon: Sparkles,
      title: 'Consejos con IA Gemini',
      desc: 'Recibe recomendaciones personalizadas generadas por inteligencia artificial según tu perfil.',
      accent: '#7c3aed',
    },
    {
      icon: Bell,
      title: 'Alertas & Notificaciones',
      desc: 'Mantente al día con recordatorios automáticos de metas próximas a vencer y aportes pendientes.',
      accent: '#d97706',
    },
    {
      icon: GraduationCap,
      title: 'Educación Financiera',
      desc: 'Aprende conceptos clave de finanzas personales con lecciones interactivas y prácticas.',
      accent: '#0891b2',
    },
  ];

  const benefits = [
    'Gestión de ingresos y egresos categorizados',
    'Múltiples cuentas y subcuentas personales o de negocio',
    'Metas de ahorro con progreso visual',
    'Integración con IA para consejos personalizados',
    'Reportes exportables y análisis detallados',
    'Alertas inteligentes y notificaciones en tiempo real',
  ];

  return (
    <div className="min-h-screen bg-[#f8f9ff] font-sans antialiased overflow-x-hidden">

      {/* ── NAVBAR ─────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 shadow-sm">
        <nav className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#0f172a] flex items-center justify-center shadow-sm">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="leading-none">
              <span className="text-base font-black text-[#0f172a] tracking-tight">FinGest</span>
              <p className="text-[8px] uppercase font-black tracking-widest text-[#006c49]">AI Smart Finance</p>
            </div>
          </div>

          {/* CTAs */}
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="px-4 py-2 text-xs font-black text-[#0f172a] hover:bg-slate-50 rounded-lg border border-transparent hover:border-slate-200 transition-all"
            >
              Iniciar Sesión
            </Link>
            <Link
              to="/registro"
              className="px-4 py-2 text-xs font-black text-white bg-[#0f172a] hover:bg-slate-800 rounded-lg transition-all shadow-sm flex items-center gap-1.5"
            >
              Comenzar Gratis
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </nav>
      </header>

      {/* ── HERO ───────────────────────────────────────────────────────────── */}
      <section className="relative max-w-7xl mx-auto px-6 pt-20 pb-24 text-center overflow-hidden">
        {/* Background blobs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-100/50 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-emerald-100/50 rounded-full blur-3xl -z-10" />

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#006c49]/10 border border-[#006c49]/20 rounded-full mb-6">
          <div className="w-1.5 h-1.5 rounded-full bg-[#006c49] animate-pulse" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[#006c49]">
            Potenciado por IA Gemini
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-[#0f172a] leading-tight tracking-tight max-w-4xl mx-auto mb-6">
          Tu{' '}
          <span className="relative inline-block">
            <span className="relative z-10 bg-gradient-to-r from-[#006c49] to-[#0891b2] bg-clip-text text-transparent">
              Inteligencia
            </span>
            <span
              className="absolute bottom-1 left-0 w-full h-3 bg-gradient-to-r from-[#006c49]/20 to-[#0891b2]/20 rounded-full -z-10"
            />
          </span>{' '}
          Financiera Personal
        </h1>

        <p className="text-base text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed font-medium">
          Gestiona tus finanzas, alcanza metas de ahorro y recibe consejos personalizados con IA.
          Todo en una sola plataforma, diseñada para que tomes el control de tu dinero.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
          <Link
            to="/registro"
            className="group flex items-center gap-2 px-8 py-3.5 bg-[#0f172a] hover:bg-slate-800 text-white text-sm font-black rounded-xl transition-all shadow-lg shadow-slate-900/20 hover:shadow-slate-900/30 active:scale-[0.99]"
          >
            <span>Crear Cuenta Gratis</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            to="/login"
            className="flex items-center gap-2 px-8 py-3.5 bg-white hover:bg-slate-50 text-[#0f172a] text-sm font-black rounded-xl border border-slate-200 transition-all shadow-sm hover:shadow-md active:scale-[0.99]"
          >
            <span>Ya tengo cuenta</span>
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </Link>
        </div>

        {/* Social proof */}
        <p className="mt-6 text-[10px] text-slate-400 font-bold uppercase tracking-widest">
          ✓ Gratis para empezar &nbsp;·&nbsp; ✓ Sin tarjeta de crédito &nbsp;·&nbsp; ✓ Datos seguros
        </p>
      </section>

      {/* ── STATS ──────────────────────────────────────────────────────────── */}
      <section className="bg-white border-y border-slate-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          <StatCard value={5000} suffix="+" label="Usuarios activos" color="#0f172a" />
          <StatCard value={98} suffix="%" label="Satisfacción" color="#006c49" />
          <StatCard value={1200000} suffix="+" label="Transacciones" color="#4f46e5" />
          <StatCard value={3} suffix="x" label="Más ahorro promedio" color="#d97706" />
        </div>
      </section>

      {/* ── FEATURES ───────────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <span className="text-[10px] uppercase font-black tracking-widest text-[#006c49]">Funcionalidades</span>
          <h2 className="text-3xl font-black text-[#0f172a] mt-2 tracking-tight">
            Todo lo que necesitas para<br />controlar tu dinero
          </h2>
          <p className="text-sm text-slate-500 mt-3 font-medium max-w-lg mx-auto">
            Desde el seguimiento de gastos hasta metas de ahorro inteligentes, FinGest te da las herramientas para crecer financieramente.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </section>

      {/* ── BENEFITS ───────────────────────────────────────────────────────── */}
      <section className="bg-[#0f172a] text-white">
        <div className="max-w-7xl mx-auto px-6 py-20 grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          {/* Left */}
          <div>
            <span className="text-[10px] uppercase font-black tracking-widest text-[#006c49]">¿Por qué FinGest?</span>
            <h2 className="text-3xl font-black mt-2 mb-4 leading-tight tracking-tight">
              Finanzas simples,<br />resultados extraordinarios
            </h2>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed font-medium">
              FinGest combina simplicidad de uso con herramientas de nivel profesional para que cualquier persona, sin importar su experiencia, pueda gestionar su dinero con confianza.
            </p>
            <ul className="space-y-3">
              {benefits.map((b) => (
                <li key={b} className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-[#006c49] flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-slate-300 font-medium">{b}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Right: Dashboard preview card */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-emerald-500/10 rounded-3xl blur-2xl" />
            <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4 backdrop-blur-sm">
              {/* Mini dashboard */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[9px] uppercase font-black tracking-widest text-slate-400">Balance Total</p>
                  <p className="text-2xl font-black text-white mt-0.5">S/ 12,450.00</p>
                </div>
                <div className="flex items-center gap-1 px-2 py-1 bg-[#006c49]/20 border border-[#006c49]/30 rounded-lg">
                  <TrendingUp className="w-3 h-3 text-[#006c49]" />
                  <span className="text-[10px] font-black text-[#006c49]">+8.2%</span>
                </div>
              </div>

              {/* Progress bars */}
              {[
                { label: 'Meta Viaje Europa', progress: 72, color: '#006c49' },
                { label: 'Fondo de Emergencia', progress: 45, color: '#4f46e5' },
                { label: 'Laptop Nueva', progress: 88, color: '#d97706' },
              ].map((m) => (
                <div key={m.label}>
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">{m.label}</span>
                    <span className="text-[10px] font-black" style={{ color: m.color }}>{m.progress}%</span>
                  </div>
                  <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000"
                      style={{ width: `${m.progress}%`, backgroundColor: m.color }}
                    />
                  </div>
                </div>
              ))}

              {/* Mini stats row */}
              <div className="grid grid-cols-3 gap-3 pt-2">
                {[
                  { label: 'Ingresos', val: 'S/3,200', icon: TrendingUp, color: '#006c49' },
                  { label: 'Gastos', val: 'S/1,850', icon: Coins, color: '#e11d48' },
                  { label: 'Ahorros', val: 'S/1,350', icon: PiggyBank, color: '#4f46e5' },
                ].map((s) => (
                  <div key={s.label} className="bg-white/5 border border-white/10 rounded-lg p-3 text-center">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">{s.label}</p>
                    <p className="text-sm font-black mt-0.5" style={{ color: s.color }}>{s.val}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── AI SECTION ─────────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-20 text-center">
        <div className="max-w-2xl mx-auto">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-500 to-indigo-500 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-indigo-500/25">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-3xl font-black text-[#0f172a] tracking-tight mb-3">
            Consejos financieros con IA Gemini
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed font-medium mb-8">
            FinGest analiza tus hábitos financieros y usa Google Gemini para generar recomendaciones
            personalizadas que te ayudan a ahorrar más y gastar mejor.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
            {[
              { icon: Zap, title: 'Análisis Instantáneo', desc: 'Recibe insights sobre tus patrones de gasto en segundos.' },
              { icon: Star, title: 'Personalizado para ti', desc: 'Los consejos se adaptan a tu perfil y objetivos únicos.' },
              { icon: Shield, title: 'Privacidad garantizada', desc: 'Tus datos financieros nunca se comparten con terceros.' },
            ].map((i) => (
              <div key={i.title} className="flex gap-3 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                  <i.icon className="w-4 h-4 text-indigo-500" />
                </div>
                <div>
                  <p className="text-xs font-black text-[#0f172a]">{i.title}</p>
                  <p className="text-[11px] text-slate-500 font-medium mt-0.5 leading-relaxed">{i.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ──────────────────────────────────────────────────────── */}
      <section className="mx-6 mb-16 rounded-3xl bg-gradient-to-br from-[#0f172a] to-[#1e293b] text-white overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#006c49]/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl" />
        <div className="relative text-center py-16 px-6">
          <h2 className="text-3xl font-black tracking-tight mb-3">
            Comienza hoy. Es completamente gratis.
          </h2>
          <p className="text-sm text-slate-400 font-medium max-w-md mx-auto mb-8">
            Únete a miles de usuarios que ya controlan sus finanzas de manera inteligente con FinGest.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/registro"
              className="group flex items-center justify-center gap-2 px-8 py-3.5 bg-[#006c49] hover:bg-[#005a3c] text-white text-sm font-black rounded-xl transition-all shadow-lg shadow-emerald-900/30 active:scale-[0.99]"
            >
              <span>Crear mi cuenta gratis</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link
              to="/login"
              className="flex items-center justify-center gap-2 px-8 py-3.5 bg-white/10 hover:bg-white/15 text-white text-sm font-black rounded-xl border border-white/20 transition-all active:scale-[0.99]"
            >
              Iniciar Sesión
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-100 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-[#0f172a] flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="text-xs font-black text-[#0f172a]">FinGest</span>
            <span className="text-xs text-slate-400 font-medium">· AI Smart Finance</span>
          </div>
          <p className="text-[10px] text-slate-400 font-medium">
            © 2026 FinGest. Todos los derechos reservados.
          </p>
          <div className="flex gap-4">
            <Link to="/login" className="text-[11px] text-slate-400 hover:text-[#0f172a] font-bold transition-colors">Login</Link>
            <Link to="/registro" className="text-[11px] text-slate-400 hover:text-[#0f172a] font-bold transition-colors">Registro</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
