import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { 
  Sparkles, 
  MessageSquare, 
  Calculator, 
  BookOpen, 
  Send, 
  Loader2, 
  Info,
  TrendingUp,
  ArrowRight,
  Star
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

const Education = () => {
  const user = useAuthStore(state => state.user);
  const [activeTab, setActiveTab] = useState('courses'); // 'courses' as default to match Stitch first view!
  const simboloMoneda = user?.id_moneda?.simbolo || '$';

  // Chat de IA
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', text: '¡Hola! Soy tu asesor financiero inteligente impulsado por IA Gemini. Pregúntame sobre presupuestos, inversiones, deudas o ahorro.' }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Calculadora
  const [initial, setInitial] = useState('1000');
  const [monthly, setMonthly] = useState('100');
  const [rate, setRate] = useState('8');
  const [years, setYears] = useState('10');
  const [calcResult, setCalcResult] = useState(null);
  const [calcAiExplanation, setCalcAiExplanation] = useState('');
  const [isCalcLoading, setIsCalcLoading] = useState(false);

  // Cursos & Tips
  const [courses, setCourses] = useState([]);
  const [tipsTab, setTipsTab] = useState('savings');
  const [tips, setTips] = useState([]);
  const [isDataLoading, setIsDataLoading] = useState(false);

  // Fallbacks exactos de Stitch
  const stitchLessonsInProgress = [
    {
      id: 'stitch-l1',
      titulo: 'Inversión en Bolsa: Nivel 1',
      descripcion: 'Entendiendo los fundamentos del mercado de valores y los índices globales.',
      proveedor: 'Fingest Academy',
      progreso: 65,
      duracion: '2.5 horas'
    },
    {
      id: 'stitch-l2',
      titulo: 'Ahorro para el Retiro',
      descripcion: 'Estrategias de interés compuesto y diversificación de fondos de pensiones.',
      proveedor: 'Wealth Management',
      progreso: 40,
      duracion: '3 horas'
    },
    {
      id: 'stitch-l3',
      titulo: 'Crédito Inteligente',
      descripcion: 'Cómo mejorar tu score crediticio y negociar mejores tasas de interés.',
      proveedor: 'Fingest Partners',
      progreso: 90,
      duracion: '1.5 horas'
    }
  ];

  const stitchExploreCourses = [
    {
      id: 'stitch-ec1',
      titulo: 'Psicología del Dinero',
      descripcion: 'Descubre cómo tus sesgos cognitivos afectan tus decisiones financieras y cómo reprogramar tu mente para el éxito.',
      proveedor: 'Behavioral Finance',
      duracion: '4 horas',
      categoria: 'Mente y Riqueza'
    },
    {
      id: 'stitch-ec2',
      titulo: 'Impuestos para Mortales',
      descripcion: 'Aprende a declarar y optimizar tus impuestos sin complicaciones legales.',
      proveedor: 'Tax Solutions',
      duracion: '3 horas',
      categoria: 'Leyes y Tributos'
    },
    {
      id: 'stitch-ec3',
      titulo: 'Crypto 101',
      descripcion: 'Más allá del hype: entendiendo blockchain y activos digitales de forma segura.',
      proveedor: 'Digital Assets',
      duracion: '2 horas',
      categoria: 'Criptomonedas'
    }
  ];

  const stitchPopularCourses = [
    {
      id: 'stitch-pop1',
      titulo: 'ETF vs Acciones Individuales',
      descripcion: 'Estrategias de inversión pasiva para construir un portafolio de bajo costo.',
      categoria: 'Estrategias de inversión pasiva'
    },
    {
      id: 'stitch-pop2',
      titulo: 'Finanzas en Pareja',
      descripcion: 'Comunicación, presupuestos conjuntos y metas metas compartidas sin discusiones.',
      categoria: 'Comunicación y metas compartidas'
    },
    {
      id: 'stitch-pop3',
      titulo: 'Inmuebles para Rentistas',
      descripcion: 'Cómo incursionar en la inversión de real estate y generar rentas recurrentes.',
      categoria: 'Inversión en real estate'
    }
  ];

  useEffect(() => {
    fetchCoursesAndTips();
  }, [tipsTab]);

  const fetchCoursesAndTips = async () => {
    setIsDataLoading(true);
    try {
      const coursesRes = await api.get('educacion-financiera/cursos/');
      const apiCoursesList = coursesRes.data.results || coursesRes.data || [];
      setCourses(apiCoursesList);

      const tipsRes = await api.get(`educacion-financiera/tips/?tab=${tipsTab}&ai=true`);
      setTips(tipsRes.data.tips || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDataLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isChatLoading) return;

    const userMsg = userInput.trim();
    setChatMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setUserInput('');
    setIsChatLoading(true);

    try {
      const response = await api.post('educacion-financiera/chat-ia/', { message: userMsg });
      if (response.data && response.data.success) {
        setChatMessages(prev => [...prev, { role: 'assistant', text: response.data.response }]);
      } else {
        setChatMessages(prev => [...prev, { role: 'assistant', text: 'Lo siento, no pude procesar la consulta.' }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', text: 'Error al conectar con el servidor de inteligencia artificial.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleCalculate = async (e) => {
    e.preventDefault();
    setIsCalcLoading(true);
    try {
      const response = await api.post('educacion-financiera/calculadora/', {
        tab: 'savings',
        initial: parseFloat(initial) || 0,
        monthly: parseFloat(monthly) || 0,
        rate: parseFloat(rate) || 0,
        years: parseInt(years) || 1
      });
      setCalcResult(response.data.result);
      setCalcAiExplanation(response.data.ai_explanation);
    } catch (err) {
      console.error(err);
    } finally {
      setIsCalcLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="text-left space-y-1">
        <h2 className="text-lg font-black text-[#0f172a] tracking-tight">
          Masteriza tus finanzas personales.
        </h2>
        <p className="text-xs text-[#64748b] font-bold">
          Aprende de expertos con lecciones dinámicas diseñadas para ayudarte a alcanzar la libertad financiera y construir un patrimonio sólido.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-2">
        <button
          onClick={() => setActiveTab('courses')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'courses' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Lecciones e Info</span>
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'chat' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>Consejero Financiero IA</span>
        </button>
        <button
          onClick={() => setActiveTab('calculator')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-black border-b-2 transition-all ${activeTab === 'calculator' ? 'border-[#0f172a] text-[#0f172a]' : 'border-transparent text-slate-400 hover:text-[#0b1c30]'}`}
        >
          <Calculator className="w-4 h-4" />
          <span>Interés Compuesto</span>
        </button>
      </div>

      {/* Courses Tab */}
      {activeTab === 'courses' && (
        <div className="space-y-8">
          
          {/* Section 1: Lecciones en curso */}
          <div className="space-y-4 text-left">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Lecciones en curso</h3>
              <span className="text-[10px] font-black text-[#006c49] cursor-pointer hover:underline flex items-center gap-1">
                Ver todo <ArrowRight className="w-3 h-3" />
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {stitchLessonsInProgress.map((lesson) => (
                <div key={lesson.id} className="p-5 rounded-md bg-white border border-slate-200 hover:border-slate-350 transition-all flex flex-col justify-between space-y-4 relative overflow-hidden group shadow-sm">
                  <div className="absolute top-0 right-0 p-2.5">
                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400/20" />
                  </div>
                  <div className="space-y-1 text-left">
                    <span className="text-[9px] uppercase font-black text-[#006c49] tracking-wider block">{lesson.proveedor}</span>
                    <h4 className="text-xs font-bold text-[#0f172a] group-hover:text-[#006c49] transition-colors">{lesson.titulo}</h4>
                    <p className="text-[11px] text-[#64748b] leading-relaxed font-bold line-clamp-2">{lesson.descripcion}</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[9px] text-slate-450 font-black uppercase">
                      <span>Progreso</span>
                      <span>{lesson.progreso}%</span>
                    </div>
                    <div className="w-full h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-[#006c49] rounded-full" style={{ width: `${lesson.progreso}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Explorar Cursos */}
          <div className="space-y-4 text-left">
            <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Explorar Cursos</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {stitchExploreCourses.map((course) => (
                <div key={course.id} className="p-5 rounded-md bg-white border border-slate-200 hover:border-slate-350 transition-all flex flex-col justify-between space-y-4 group shadow-sm">
                  <div className="space-y-1 text-left">
                    <span className="text-[9px] uppercase font-black text-slate-450 tracking-widest block">{course.categoria}</span>
                    <h4 className="text-xs font-bold text-[#0f172a] group-hover:text-[#006c49] transition-colors">{course.titulo}</h4>
                    <p className="text-[11px] text-[#64748b] leading-relaxed font-bold">{course.descripcion}</p>
                  </div>
                  <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                    <span className="text-[9px] text-slate-450 font-black tracking-wider uppercase">{course.duracion}</span>
                    <button className="text-[10px] font-black text-[#006c49] hover:underline flex items-center gap-1 uppercase tracking-wider">
                      <span>Empezar</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Cursos Populares esta Semana & Pro Academy */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-left items-stretch">
            
            {/* Populares */}
            <div className="lg:col-span-2 p-6 rounded-md bg-white border border-slate-200 space-y-4 shadow-sm">
              <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-widest flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[#006c49]" />
                <span>Cursos Populares esta Semana</span>
              </h4>

              <div className="divide-y divide-slate-100 space-y-4">
                {stitchPopularCourses.map((pop) => (
                  <div key={pop.id} className="pt-4 first:pt-0 flex items-center justify-between gap-4">
                    <div>
                      <h5 className="text-xs font-bold text-[#0f172a]">{pop.titulo}</h5>
                      <p className="text-[10px] text-slate-450 font-black uppercase tracking-wider mt-0.5">{pop.categoria}</p>
                    </div>
                    <button className="px-3 py-1.5 bg-slate-50 border border-slate-200 hover:border-slate-350 rounded-md text-[10px] font-black text-[#0f172a] hover:bg-slate-100 transition-all shadow-sm">
                      Unirse
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Pro Academy */}
            <div className="p-6 rounded-md bg-gradient-to-tr from-[#0f172a] to-[#006c49] text-white flex flex-col justify-between space-y-4 shadow-md relative overflow-hidden">
              <div className="absolute -bottom-10 -right-10 w-36 h-36 bg-white/5 rounded-full blur-xl pointer-events-none" />
              <div className="space-y-2 relative text-left">
                <div className="w-8 h-8 rounded-md bg-white/10 flex items-center justify-center">
                  <Star className="w-4 h-4 text-white fill-white" />
                </div>
                <h4 className="text-xs font-black uppercase tracking-wider">Pro Academy</h4>
                <p className="text-[11px] text-slate-200 leading-relaxed font-bold">
                  Accede a contenido exclusivo, análisis de carteras de inversión premium y mentorías financieras 1:1 con asesores certificados.
                </p>
              </div>
              <button className="w-full py-2.5 bg-white text-slate-900 rounded-md text-[10px] font-black uppercase tracking-wider hover:bg-slate-50 transition-all shadow-sm active:scale-[0.99] relative">
                Adquirir Membresía
              </button>
            </div>

          </div>

          {/* Dinamic Tips Section */}
          <div className="space-y-4 text-left">
            <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Consejos Inteligentes IA</h3>
            
            <div className="flex flex-wrap p-1 rounded-md bg-slate-100 border border-slate-200 gap-1 self-start inline-flex">
              {['savings', 'investment', 'budget', 'debt', 'retirement'].map((t) => (
                <button
                  key={t}
                  onClick={() => setTipsTab(t)}
                  className={`px-3 py-1.5 text-[10px] font-black rounded-md transition-all capitalize ${tipsTab === t ? 'bg-[#0f172a] text-white' : 'text-slate-455 hover:text-[#0b1c30]'}`}
                >
                  {t}
                </button>
              ))}
            </div>

            {isDataLoading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-6 h-6 animate-spin text-[#0f172a]" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {tips.slice(0, 4).map((tip) => (
                  <div key={tip.id} className="p-4 rounded-md bg-white border border-slate-200 flex gap-3 text-left shadow-sm">
                    <Sparkles className="w-4.5 h-4.5 text-[#006c49] flex-shrink-0 mt-0.5 animate-pulse" />
                    <div>
                      <h4 className="text-xs font-bold text-[#0f172a]">{tip.titulo}</h4>
                      <p className="text-[11px] text-[#64748b] leading-relaxed font-bold mt-0.5">{tip.descripcion}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}

      {/* Chatbot Tab */}
      {activeTab === 'chat' && (
        <div className="rounded-md bg-white border border-slate-200 shadow-sm h-[600px] flex flex-col overflow-hidden relative">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-[#006c49] animate-pulse" />
            <div className="text-left">
              <span className="text-xs font-black text-[#0f172a] block">Asesor Inteligente Gemini</span>
              <span className="text-[9px] text-slate-450 uppercase font-black tracking-widest">Consejería Activa</span>
            </div>
          </div>

          <div className="flex-1 p-6 overflow-y-auto space-y-4 flex flex-col">
            {chatMessages.map((msg, i) => (
              <div 
                key={i} 
                className={`
                  flex gap-3 max-w-[80%] rounded-md p-4 text-xs leading-relaxed text-left
                  ${msg.role === 'assistant' 
                    ? 'bg-slate-50 text-slate-700 border border-slate-100 self-start' 
                    : 'bg-[#eff4ff] text-[#0f172a] border border-[#e5eeff] self-end font-bold'
                  }
                `}
              >
                {msg.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-md bg-[#0f172a] text-white flex items-center justify-center flex-shrink-0 font-black text-[9px] shadow-sm">
                    IA
                  </div>
                )}
                <div className="space-y-1">
                  <p className="whitespace-pre-line">{msg.text}</p>
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="flex gap-3 max-w-[80%] rounded-md p-4 bg-slate-50 text-slate-400 border border-slate-100 self-start text-xs font-bold">
                <Loader2 className="w-4 h-4 animate-spin text-[#006c49]" />
                <span>Pensando respuesta financiera...</span>
              </div>
            )}
          </div>

          <form onSubmit={handleSendMessage} className="p-4 bg-slate-50 border-t border-slate-200 flex gap-2">
            <input
              type="text"
              required
              placeholder="Pregúntame algo: ¿Qué es una tasa de interés? ¿Cómo armo un fondo de emergencia?"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              className="flex-1 px-4 py-3 bg-white border border-slate-200 focus:border-[#0f172a] rounded-md text-xs text-[#0f172a] focus:outline-none focus:ring-1 focus:ring-[#0f172a]/20 font-bold shadow-sm"
            />
            <button
              type="submit"
              disabled={isChatLoading || !userInput.trim()}
              className="px-5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1 active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </form>
        </div>
      )}

      {/* Calculator Tab */}
      {activeTab === 'calculator' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start text-left">
          <form onSubmit={handleCalculate} className="lg:col-span-1 p-6 rounded-md bg-white border border-slate-200 space-y-4 shadow-sm">
            <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider pb-2 border-b border-slate-100">Variables de Ahorro</h3>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Capital Inicial ({simboloMoneda})</label>
              <input
                type="number"
                required
                value={initial}
                onChange={(e) => setInitial(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 font-bold"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Aporte Mensual ({simboloMoneda})</label>
              <input
                type="number"
                required
                value={monthly}
                onChange={(e) => setMonthly(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 font-bold"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Tasa Anual Estimada (%)</label>
              <input
                type="number"
                step="0.1"
                required
                value={rate}
                onChange={(e) => setRate(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 font-bold"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Periodo (Años)</label>
              <input
                type="number"
                required
                value={years}
                onChange={(e) => setYears(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 font-bold"
              />
            </div>

            <button
              type="submit"
              disabled={isCalcLoading}
              className="w-full py-2.5 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider shadow flex items-center justify-center gap-1 active:scale-[0.99] disabled:opacity-50"
            >
              {isCalcLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Calcular Crecimiento'}
            </button>
          </form>

          <div className="lg:col-span-2 space-y-6">
            {calcResult ? (
              <>
                <div className="p-6 rounded-md bg-white border border-slate-200 grid grid-cols-3 gap-4 text-center shadow-sm">
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Total Acumulado</span>
                    <p className="text-lg font-black text-[#006c49]">{simboloMoneda}{parseFloat(calcResult.future_value).toLocaleString()}</p>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Aportes Propios</span>
                    <p className="text-lg font-black text-[#0f172a]">{simboloMoneda}{parseFloat(calcResult.total_contributed).toLocaleString()}</p>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Intereses Generados</span>
                    <p className="text-lg font-black text-[#006c49]">{simboloMoneda}{parseFloat(calcResult.interest_earned).toLocaleString()}</p>
                  </div>
                </div>

                {calcAiExplanation && (
                  <div className="p-5 rounded-md bg-[#eff4ff]/60 border border-[#c6c6cd] text-left space-y-2 relative overflow-hidden shadow-sm">
                    <div className="flex gap-2 items-center">
                      <Sparkles className="w-4.5 h-4.5 text-[#0f172a] animate-pulse" />
                      <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Análisis de la IA</h4>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line font-bold italic">
                      {calcAiExplanation}
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="p-12 text-center rounded-md bg-white border border-slate-200 text-[#64748b] flex flex-col items-center justify-center gap-2 shadow-sm">
                <Info className="w-7 h-7 text-slate-300" />
                <p className="text-xs font-bold">Introduce tus variables a la izquierda y presiona Calcular para proyectar tu futuro financiero.</p>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default Education;
