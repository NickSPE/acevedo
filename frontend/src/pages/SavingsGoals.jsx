import React, { useEffect, useState } from 'react';
import { useFinanceStore } from '../store/useFinanceStore';
import { useAuthStore } from '../store/useAuthStore';
import { 
  PiggyBank, 
  Plus, 
  ArrowLeftRight, 
  Trash2, 
  AlertCircle, 
  CheckCircle,
  Calendar,
  Sparkles,
  Coins,
  Target,
  Loader2
} from 'lucide-react';
import Modal from '../components/Modal';

const SavingsGoals = () => {
  const user = useAuthStore(state => state.user);
  const { 
    goals, 
    subaccounts, 
    accounts,
    tips,
    fetchGoals, 
    fetchDashboardData,
    createSubaccount,
    deleteSubaccount,
    toggleSubaccount,
    transferBetweenSubaccounts,
    transferPrincipal,
    createGoal,
    addFundToGoal,
    deleteGoal
  } = useFinanceStore();

  const [activeTab, setActiveTab] = useState('subaccounts'); // 'subaccounts' or 'goals'
  const [isLoadingLocal, setIsLoadingLocal] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Modales
  const [showAddSubaccount, setShowAddSubaccount] = useState(false);
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [showTransfer, setShowTransfer] = useState(false);
  const [showAporte, setShowAporte] = useState(false);
  
  // Estado para el modal de Aporte
  const [selectedGoalForAporte, setSelectedGoalForAporte] = useState(null);
  const [montoAporte, setMontoAporte] = useState('');
  const [descAporte, setDescAporte] = useState('');

  // Formulario nueva subcuenta
  const [subNombre, setSubNombre] = useState('');
  const [subTipo, setSubTipo] = useState('otros');
  const [subTipoCat, setSubTipoCat] = useState('personal'); // 'personal' o 'business'
  const [subMetaObjetivo, setSubMetaObjetivo] = useState('');
  const [subFechaMeta, setSubFechaMeta] = useState('');
  
  // Formulario nueva meta de ahorro
  const [goalNombre, setGoalNombre] = useState('');
  const [goalMontoObjetivo, setGoalMontoObjetivo] = useState('');
  const [goalFechaLimite, setGoalFechaLimite] = useState('');
  const [goalDescripcion, setGoalDescripcion] = useState('');
  const [goalCuentaId, setGoalCuentaId] = useState('');
  const [goalFrecuencia, setGoalFrecuencia] = useState('mensual');

  // Formulario transferencias (Subcuentas)
  const [transferMode, setTransferMode] = useState('deposit'); // 'deposit', 'withdraw', 'between'
  const [montoTrans, setMontoTrans] = useState('');
  const [fromSubId, setFromSubId] = useState('');
  const [toSubId, setToSubId] = useState('');
  const [descTrans, setDescTrans] = useState('');

  // Slider de tips con IA
  const [currentTipIdx, setCurrentTipIdx] = useState(0);

  useEffect(() => {
    fetchGoals();
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (accounts.length > 0 && !goalCuentaId) {
      setGoalCuentaId(accounts[0].id);
    }
  }, [accounts]);

  const showSuccess = (msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(''), 4000);
  };

  const showError = (msg) => {
    setErrorMsg(msg);
    setTimeout(() => setErrorMsg(''), 4000);
  };

  // --- Manejo de Subcuentas ---
  const handleCreateSubaccount = async (e) => {
    e.preventDefault();
    if (!subNombre.trim()) {
      showError('El nombre de la subcuenta es requerido.');
      return;
    }

    const payload = {
      nombre: subNombre.trim(),
      tipo: subTipo,
      tipo_subcuenta: subTipoCat,
    };

    if (subMetaObjetivo) {
      payload.meta_objetivo = parseFloat(subMetaObjetivo);
    }
    if (subFechaMeta) {
      payload.fecha_meta = subFechaMeta;
    }

    setIsLoadingLocal(true);
    const res = await createSubaccount(payload);
    setIsLoadingLocal(false);

    if (res.success) {
      setShowAddSubaccount(false);
      setSubNombre('');
      setSubMetaObjetivo('');
      setSubFechaMeta('');
      showSuccess('Subcuenta creada con éxito.');
      fetchDashboardData();
    } else {
      showError(res.error);
    }
  };

  const handleDeleteSub = async (id) => {
    if (window.confirm('¿Estás seguro de que deseas eliminar esta subcuenta? El saldo restante se reintegrará automáticamente a tu cuenta principal.')) {
      setIsLoadingLocal(true);
      const res = await deleteSubaccount(id);
      setIsLoadingLocal(false);
      if (res.success) {
        showSuccess('Subcuenta eliminada y saldo reintegrado.');
        fetchDashboardData();
      } else {
        showError(res.error);
      }
    }
  };

  const handleToggleSub = async (id) => {
    const res = await toggleSubaccount(id);
    if (res.success) {
      showSuccess('Estado de la subcuenta actualizado.');
      fetchDashboardData();
    } else {
      showError(res.error);
    }
  };

  // --- Manejo de Transferencias ---
  const handleTransferSubmit = async (e) => {
    e.preventDefault();
    if (!montoTrans || parseFloat(montoTrans) <= 0) {
      showError('El monto debe ser mayor a 0.');
      return;
    }

    setIsLoadingLocal(true);
    let res;

    if (transferMode === 'deposit') {
      res = await transferPrincipal({
        tipo: 'retiro',
        subcuenta: toSubId,
        monto: parseFloat(montoTrans),
        descripcion: descTrans.trim() || 'Depósito desde cuenta principal'
      });
    } else if (transferMode === 'withdraw') {
      res = await transferPrincipal({
        tipo: 'deposito',
        subcuenta: fromSubId,
        monto: parseFloat(montoTrans),
        descripcion: descTrans.trim() || 'Retiro a cuenta principal'
      });
    } else if (transferMode === 'between') {
      res = await transferBetweenSubaccounts({
        subcuenta_origen: fromSubId,
        subcuenta_destino: toSubId,
        monto: parseFloat(montoTrans),
        descripcion: descTrans.trim() || 'Transferencia entre subcuentas'
      });
    }

    setIsLoadingLocal(false);

    if (res && res.success) {
      showSuccess(res.message || 'Transferencia realizada con éxito.');
      setMontoTrans('');
      setDescTrans('');
      setShowTransfer(false);
      fetchDashboardData();
    } else {
      showError(res ? res.error : 'Ocurrió un error al transferir.');
    }
  };

  // --- Manejo de Metas de Ahorro ---
  const handleCreateGoal = async (e) => {
    e.preventDefault();
    if (!goalNombre.trim() || !goalMontoObjetivo || !goalFechaLimite || !goalCuentaId) {
      showError('Por favor completa todos los campos requeridos.');
      return;
    }

    const payload = {
      nombre: goalNombre.trim(),
      monto_objetivo: parseFloat(goalMontoObjetivo),
      fecha_limite: goalFechaLimite,
      fecha_inicio: new Date().toISOString().split('T')[0],
      descripcion: goalDescripcion.trim() || `Meta para ${goalNombre}`,
      id_cuenta: parseInt(goalCuentaId),
      frecuencia_aporte: goalFrecuencia
    };

    setIsLoadingLocal(true);
    const res = await createGoal(payload);
    setIsLoadingLocal(false);

    if (res.success) {
      setShowAddGoal(false);
      setGoalNombre('');
      setGoalMontoObjetivo('');
      setGoalFechaLimite('');
      setGoalDescripcion('');
      showSuccess('Meta de ahorro creada con éxito.');
      fetchGoals();
      fetchDashboardData();
    } else {
      showError(res.error);
    }
  };

  const handleDeleteGoalItem = async (id) => {
    if (window.confirm('¿Estás seguro de que deseas eliminar esta meta de ahorro?')) {
      setIsLoadingLocal(true);
      const res = await deleteGoal(id);
      setIsLoadingLocal(false);
      if (res.success) {
        showSuccess('Meta de ahorro eliminada.');
        fetchGoals();
        fetchDashboardData();
      } else {
        showError(res.error);
      }
    }
  };

  const handleAporteSubmit = async (e) => {
    e.preventDefault();
    if (!montoAporte || parseFloat(montoAporte) <= 0) {
      showError('El monto del aporte debe ser mayor a 0.');
      return;
    }

    setIsLoadingLocal(true);
    const res = await addFundToGoal({
      id_meta_ahorro: selectedGoalForAporte.id,
      monto: parseFloat(montoAporte),
      descripcion: descAporte.trim() || 'Aporte a meta de ahorro'
    });
    setIsLoadingLocal(false);

    if (res.success) {
      showSuccess(res.message || 'Aporte realizado con éxito.');
      setMontoAporte('');
      setDescAporte('');
      setShowAporte(false);
      fetchGoals();
      fetchDashboardData();
    } else {
      showError(res.error);
    }
  };

  const nextTip = () => {
    if (tips.length > 0) {
      setCurrentTipIdx((currentTipIdx + 1) % tips.length);
    }
  };

  const prevTip = () => {
    if (tips.length > 0) {
      setCurrentTipIdx((currentTipIdx - 1 + tips.length) % tips.length);
    }
  };

  const simboloMoneda = user?.id_moneda?.simbolo || '$';

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-left">
        <div>
          <h2 className="text-lg font-black text-[#0f172a] tracking-tight">Subcuentas & Metas de Ahorro</h2>
          <p className="text-xs text-[#64748b] mt-0.5">Separa tu dinero en subcuentas o programa objetivos de ahorro avanzados.</p>
        </div>
        
        <div className="flex flex-wrap gap-2 w-full sm:w-auto">
          {activeTab === 'subaccounts' ? (
            <>
              <button
                onClick={() => { setSubNombre(''); setSubMetaObjetivo(''); setSubFechaMeta(''); setShowAddSubaccount(true); }}
                className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-3 bg-[#0f172a] hover:bg-slate-800 active:scale-[0.99] text-white rounded-md text-xs font-black uppercase tracking-wider transition-all shadow-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Nueva Subcuenta</span>
              </button>
              
              {subaccounts.length > 0 && (
                <button
                  onClick={() => { setMontoTrans(''); setDescTrans(''); setShowTransfer(true); }}
                  className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-3 bg-white hover:bg-slate-50 active:scale-[0.99] border border-slate-200 text-[#0f172a] rounded-md text-xs font-black uppercase tracking-wider transition-all shadow-sm"
                >
                  <ArrowLeftRight className="w-4 h-4 text-[#0f172a]" />
                  <span>Transferir Fondos</span>
                </button>
              )}
            </>
          ) : (
            <button
              onClick={() => { setGoalNombre(''); setGoalMontoObjetivo(''); setGoalFechaLimite(''); setGoalDescripcion(''); setShowAddGoal(true); }}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3 bg-[#006c49] hover:bg-[#005a3c] active:scale-[0.99] text-white rounded-md text-xs font-black uppercase tracking-wider transition-all shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Nueva Meta de Ahorro</span>
            </button>
          )}
        </div>
      </div>

      {/* Alertas de Feedback */}
      {successMsg && (
        <div className="p-3.5 text-xs font-bold rounded-md bg-emerald-50 border border-emerald-100 text-[#006c49] text-center animate-fade-in flex items-center justify-center gap-2 shadow-sm">
          <CheckCircle className="w-4 h-4" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3.5 text-xs font-bold rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center animate-fade-in flex items-center justify-center gap-2 shadow-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* AI tips / Carrusel Section */}
      {tips.length > 0 && (
        <div className="p-5 rounded-md bg-slate-50 border border-slate-200 shadow-sm relative overflow-hidden text-left">
          <div className="flex gap-3 items-start">
            <div className="p-2 rounded-md bg-slate-200/50 text-[#0f172a] mt-0.5 flex-shrink-0">
              <Sparkles className="w-4.5 h-4.5" />
            </div>
            
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[9px] uppercase font-black tracking-widest text-[#0f172a]">Consejos Financieros de IA Gemini</span>
                <div className="flex gap-2">
                  <button onClick={prevTip} className="p-1 rounded text-slate-500 hover:bg-slate-200 hover:text-[#0b1c30] transition-colors text-xs font-black">‹</button>
                  <span className="text-[10px] text-[#64748b] font-bold">{currentTipIdx + 1} / {tips.length}</span>
                  <button onClick={nextTip} className="p-1 rounded text-slate-500 hover:bg-slate-200 hover:text-[#0b1c30] transition-colors text-xs font-black">›</button>
                </div>
              </div>
              <p className="text-xs font-black text-[#0f172a] flex items-center gap-1.5">
                <span>{tips[currentTipIdx]?.emoji}</span>
                <span>{tips[currentTipIdx]?.titulo}</span>
              </p>
              <p className="text-xs text-slate-500 leading-relaxed font-bold mt-0.5">
                {tips[currentTipIdx]?.mensaje}
              </p>
              {tips[currentTipIdx]?.accion && (
                <p className="text-[10px] text-[#006c49] font-extrabold mt-0.5 italic">
                  → {tips[currentTipIdx]?.accion}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs Selector */}
      <div className="flex p-1 rounded-md bg-slate-100 border border-slate-250/60 max-w-md">
        <button
          onClick={() => setActiveTab('subaccounts')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-black rounded-md transition-all ${activeTab === 'subaccounts' ? 'bg-[#0f172a] text-white shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
        >
          <Coins className="w-4 h-4" />
          <span>Subcuentas ({subaccounts.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('goals')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-black rounded-md transition-all ${activeTab === 'goals' ? 'bg-[#006c49] text-white shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
        >
          <Target className="w-4 h-4" />
          <span>Metas de Ahorro ({goals.length})</span>
        </button>
      </div>

      {/* CONTENIDO DE TABS */}
      {activeTab === 'subaccounts' ? (
        subaccounts.length === 0 ? (
          <div className="p-12 text-center rounded-md bg-white border border-slate-200 text-[#64748b] flex flex-col items-center justify-center gap-2 shadow-sm">
            <PiggyBank className="w-10 h-10 text-slate-350" />
            <div className="space-y-0.5">
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Sin subcuentas</h3>
              <p className="text-xs text-slate-450 max-w-sm font-bold">Crea una subcuenta para guardar fondos apartados para gastos específicos o proyectos profesionales.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-left">
            {subaccounts.map((sub) => {
              const hasMeta = parseFloat(sub.meta_objetivo) > 0;
              const progress = hasMeta ? Math.round(sub.progreso_meta || 0) : 0;
              
              return (
                <div 
                  key={sub.id} 
                  className={`p-6 rounded-md bg-white border transition-all duration-300 flex flex-col justify-between space-y-6 shadow-sm relative group ${sub.activa ? 'border-slate-200 hover:border-[#0f172a]/30' : 'border-slate-100 opacity-60 bg-slate-50/50'}`}
                >
                  <div className="flex justify-between items-start gap-4 z-10">
                    <div className="flex gap-3">
                      <div 
                        className="w-9 h-9 rounded-md flex items-center justify-center shadow-sm text-[#0f172a] font-bold border border-slate-150"
                        style={{ backgroundColor: `${sub.color || '#3b82f6'}15`, color: sub.color || '#3b82f6' }}
                      >
                        <Coins className="w-4.5 h-4.5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">{sub.nombre}</h4>
                          {sub.es_negocio && (
                            <span className="px-1.5 py-0.5 rounded text-[8px] bg-slate-100 text-[#0f172a] border border-slate-200 font-extrabold uppercase">Negocio</span>
                          )}
                        </div>
                        <p className="text-[9px] text-[#64748b] font-black uppercase tracking-widest mt-0.5">{sub.tipo_display_emoji || '📁 Otros'}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleToggleSub(sub.id)}
                        className={`text-[9px] font-black uppercase px-2 py-0.5 rounded border transition-all ${sub.activa ? 'bg-slate-50 text-[#0f172a] border-slate-200' : 'bg-slate-100 text-slate-400 border-slate-150'}`}
                      >
                        {sub.activa ? 'Activa' : 'Pausada'}
                      </button>
                      <button
                        onClick={() => handleDeleteSub(sub.id)}
                        className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Eliminar Subcuenta"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Balance / Saldo actual */}
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-black text-[#64748b] uppercase tracking-widest block">Saldo Disponible</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-xl font-black text-[#0f172a]">
                        {simboloMoneda}{parseFloat(sub.saldo || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                      {hasMeta && (
                        <span className="text-[10px] text-slate-450 font-bold">
                          / {simboloMoneda}{parseFloat(sub.meta_objetivo).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Progress bar meta */}
                  {hasMeta && (
                    <div className="space-y-1.5">
                      <div className="flex justify-between items-center text-[9px] font-bold text-slate-400">
                        <span>Progreso Financiero</span>
                        <span className="font-extrabold text-[#0f172a]">{progress}%</span>
                      </div>
                      
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#0f172a] rounded-full transition-all duration-500"
                          style={{ width: `${progress}%` }}
                        />
                      </div>

                      {sub.dias_restantes_meta !== null && (
                        <p className="text-[9px] font-bold text-slate-450 flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>Quedan {sub.dias_restantes_meta} días</span>
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )
      ) : (
        goals.length === 0 ? (
          <div className="p-12 text-center rounded-md bg-white border border-slate-200 text-[#64748b] flex flex-col items-center justify-center gap-2 shadow-sm">
            <Target className="w-10 h-10 text-slate-350" />
            <div className="space-y-0.5">
              <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Sin metas de ahorro</h3>
              <p className="text-xs text-slate-450 max-w-sm font-bold">Establece objetivos de ahorro con plazos específicos, frecuencias de aporte automáticas e historial de depósitos.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-left">
            {goals.map((goal) => {
              const progress = Math.round(goal.porcentaje_progreso || 0);
              const totalAhorrado = parseFloat(goal.monto_ahorrado || 0);
              const totalObjetivo = parseFloat(goal.monto_objetivo || 0);
              
              return (
                <div 
                  key={goal.id} 
                  className="p-6 rounded-md bg-white border border-slate-200 hover:border-[#006c49]/30 transition-all duration-300 flex flex-col justify-between space-y-5 shadow-sm relative"
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex gap-3">
                      <div className="w-9 h-9 rounded-md flex items-center justify-center bg-emerald-50 text-[#006c49] shadow-sm">
                        <Target className="w-4.5 h-4.5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">{goal.nombre}</h4>
                        <p className="text-[9px] text-[#64748b] font-black uppercase tracking-widest mt-0.5 flex items-center gap-1">
                          <Calendar className="w-2.5 h-2.5 text-slate-400" />
                          <span>Límite: {new Date(goal.fecha_limite).toLocaleDateString()}</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {goal.meta_alcanzada ? (
                        <span className="px-2 py-0.5 bg-emerald-50 text-[#006c49] border border-emerald-100 rounded-md text-[9px] font-black uppercase tracking-wider">Logrado 🎉</span>
                      ) : (
                        <span className="px-2 py-0.5 bg-slate-50 text-slate-500 rounded-md text-[9px] font-black uppercase tracking-wider border border-slate-100">{goal.frecuencia_aporte}</span>
                      )}
                      <button
                        onClick={() => handleDeleteGoalItem(goal.id)}
                        className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Eliminar Meta"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {goal.descripcion && (
                    <p className="text-[11px] text-slate-500 leading-relaxed pl-1 italic font-bold">
                      "{goal.descripcion}"
                    </p>
                  )}

                  {/* Metas balances */}
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-black text-[#64748b] uppercase tracking-widest block">Total Ahorrado</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-xl font-black text-[#006c49]">
                        {simboloMoneda}{totalAhorrado.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                      <span className="text-[10px] text-slate-450 font-bold">
                        / {simboloMoneda}{totalObjetivo.toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between items-center text-[9px] font-bold text-slate-400">
                      <span>Progreso de Meta</span>
                      <span className="font-extrabold text-[#006c49]">{progress}%</span>
                    </div>

                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#006c49] rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  {!goal.meta_alcanzada && (
                    <button
                      onClick={() => { setSelectedGoalForAporte(goal); setMontoAporte(''); setDescAporte(''); setShowAporte(true); }}
                      className="w-full py-2 bg-[#006c49] hover:bg-[#005a3c] active:scale-[0.99] text-white font-black rounded-md text-xs flex items-center justify-center gap-1.5 transition-all shadow-sm uppercase tracking-wider"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Registrar Aporte</span>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )
      )}

      {/* --- MODAL NUEVA SUBCUENTA --- */}
      <Modal
        isOpen={showAddSubaccount}
        onClose={() => setShowAddSubaccount(false)}
        title="Crear Nueva Subcuenta"
      >
        <form onSubmit={handleCreateSubaccount} className="space-y-4 text-left">
          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-450 uppercase tracking-widest pl-0.5">Tipo de Ámbito</label>
            <select
              value={subTipoCat}
              onChange={(e) => setSubTipoCat(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
            >
              <option value="personal">Gestión Personal (Vinculada a Cuenta Principal)</option>
              <option value="business">Negocio / Emprendimiento (Independiente)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Nombre de la Subcuenta</label>
            <input
              type="text"
              required
              placeholder="ej. Caja Chica, Ventas Web, Viaje 2026"
              value={subNombre}
              onChange={(e) => setSubNombre(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Categoría / Tipo</label>
            <select
              value={subTipo}
              onChange={(e) => setSubTipo(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
            >
              {subTipoCat === 'business' ? (
                <>
                  <option value="tienda_online">🛍️ Tienda Online</option>
                  <option value="tienda_fisica">🏪 Tienda Física</option>
                  <option value="servicios_profesionales">💼 Servicios Profesionales</option>
                  <option value="freelance">💻 Trabajo Freelance</option>
                  <option value="negocio_propio">🏢 Negocio Propio</option>
                  <option value="ingresos_pasivos">💸 Ingresos Pasivos</option>
                  <option value="ventas_productos">📦 Ventas de Productos</option>
                  <option value="consultoria">🎯 Consultoría</option>
                  <option value="alquiler_propiedades">🏠 Alquiler de Propiedades</option>
                </>
              ) : (
                <>
                  <option value="ahorro_meta">🎯 Ahorro para Meta</option>
                  <option value="emergencia">🚨 Fondo de Emergencia</option>
                  <option value="inversion">📈 Inversiones</option>
                  <option value="gastos_fijos">🔒 Gastos Fijos</option>
                  <option value="gastos_variables">📊 Gastos Variables</option>
                  <option value="entretenimiento">🎭 Entretenimiento</option>
                  <option value="viajes">✈️ Viajes y Vacaciones</option>
                  <option value="educacion">📚 Educación y Cursos</option>
                  <option value="salud">🏥 Salud y Bienestar</option>
                  <option value="familia">👨‍👩‍👧‍👦 Gastos Familiares</option>
                  <option value="otros">📁 Otros</option>
                </>
              )}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Meta Financiera (Opcional)</label>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={subMetaObjetivo}
                onChange={(e) => setSubMetaObjetivo(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Fecha Meta (Opcional)</label>
              <input
                type="date"
                value={subFechaMeta}
                onChange={(e) => setSubFechaMeta(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoadingLocal}
            className="w-full py-3 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all shadow-sm"
          >
            {isLoadingLocal ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Registrar Subcuenta'}
          </button>
        </form>
      </Modal>

      {/* --- MODAL TRANSFERENCIAS (SUBCUENTAS) --- */}
      <Modal
        isOpen={showTransfer}
        onClose={() => setShowTransfer(false)}
        title="Transferir Fondos"
      >
        <form onSubmit={handleTransferSubmit} className="space-y-4 text-left">
          
          {/* Transfer Mode selector tabs */}
          <div className="flex p-1 rounded-md bg-slate-105 border border-slate-200">
            <button
              type="button"
              onClick={() => setTransferMode('deposit')}
              className={`flex-1 py-1.5 text-[9px] font-black uppercase rounded-md transition-all ${transferMode === 'deposit' ? 'bg-white border border-slate-250 text-[#0f172a] shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
            >
              Depositar Subcuenta
            </button>
            <button
              type="button"
              onClick={() => setTransferMode('withdraw')}
              className={`flex-1 py-1.5 text-[9px] font-black uppercase rounded-md transition-all ${transferMode === 'withdraw' ? 'bg-white border border-slate-250 text-[#0f172a] shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
            >
              Retirar a Principal
            </button>
            <button
              type="button"
              onClick={() => setTransferMode('between')}
              className={`flex-1 py-1.5 text-[9px] font-black uppercase rounded-md transition-all ${transferMode === 'between' ? 'bg-white border border-slate-250 text-[#0f172a] shadow-sm' : 'text-slate-500 hover:text-[#0b1c30]'}`}
            >
              Entre Subcuentas
            </button>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Monto a Transferir</label>
            <input
              type="number"
              step="0.01"
              required
              min="0.01"
              placeholder="0.00"
              value={montoTrans}
              onChange={(e) => setMontoTrans(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Descripción / Motivo</label>
            <input
              type="text"
              placeholder="ej. Reintegro de viáticos, Traspaso mensual"
              value={descTrans}
              onChange={(e) => setDescTrans(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          {/* Dinámico según el modo de transferencia */}
          {transferMode === 'deposit' && (
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Subcuenta Destino</label>
              <select
                required
                value={toSubId}
                onChange={(e) => setToSubId(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              >
                <option value="">Selecciona subcuenta...</option>
                {subaccounts.filter(s => s.activa).map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.nombre} (Saldo: {simboloMoneda}{parseFloat(sub.saldo).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
          )}

          {transferMode === 'withdraw' && (
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Subcuenta Origen</label>
              <select
                required
                value={fromSubId}
                onChange={(e) => setFromSubId(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              >
                <option value="">Selecciona subcuenta...</option>
                {subaccounts.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.nombre} (Disponible: {simboloMoneda}{parseFloat(sub.saldo).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
          )}

          {transferMode === 'between' && (
            <>
              <div className="space-y-1">
                <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Subcuenta Origen</label>
                <select
                  required
                  value={fromSubId}
                  onChange={(e) => setFromSubId(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
                >
                  <option value="">Selecciona subcuenta origen...</option>
                  {subaccounts.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.nombre} (Disponible: {simboloMoneda}{parseFloat(sub.saldo).toLocaleString()})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Subcuenta Destino</label>
                <select
                  required
                  value={toSubId}
                  onChange={(e) => setToSubId(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
                >
                  <option value="">Selecciona subcuenta destino...</option>
                  {subaccounts.filter(s => s.id !== parseInt(fromSubId) && s.activa).map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.nombre} (Saldo actual: {simboloMoneda}{parseFloat(sub.saldo).toLocaleString()})
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={isLoadingLocal}
            className="w-full py-3 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all shadow-sm"
          >
            {isLoadingLocal ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Ejecutar Transferencia'}
          </button>
        </form>
      </Modal>

      {/* --- MODAL NUEVA META DE AHORRO --- */}
      <Modal
        isOpen={showAddGoal}
        onClose={() => setShowAddGoal(false)}
        title="Crear Nueva Meta de Ahorro"
      >
        <form onSubmit={handleCreateGoal} className="space-y-4 text-left">
          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Nombre de la Meta</label>
            <input
              type="text"
              required
              placeholder="ej. Enganche de Auto, Computadora nueva"
              value={goalNombre}
              onChange={(e) => setGoalNombre(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Descripción</label>
            <input
              type="text"
              placeholder="Detalla tu propósito..."
              value={goalDescripcion}
              onChange={(e) => setGoalDescripcion(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Monto Objetivo *</label>
              <input
                type="number"
                step="0.01"
                required
                min="1"
                placeholder="0.00"
                value={goalMontoObjetivo}
                onChange={(e) => setGoalMontoObjetivo(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Fecha Límite *</label>
              <input
                type="date"
                required
                value={goalFechaLimite}
                onChange={(e) => setGoalFechaLimite(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Frecuencia de Aporte</label>
              <select
                value={goalFrecuencia}
                onChange={(e) => setGoalFrecuencia(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              >
                <option value="diaria">Diaria</option>
                <option value="semanal">Semanal</option>
                <option value="quincenal">Quincenal</option>
                <option value="mensual">Mensual</option>
                <option value="bimestral">Bimestral</option>
                <option value="trimestral">Trimestral</option>
                <option value="semestral">Semestral</option>
                <option value="anual">Anual</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Cuenta de Respaldo</label>
              <select
                required
                value={goalCuentaId}
                onChange={(e) => setGoalCuentaId(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              >
                {accounts.map(acc => (
                  <option key={acc.id} value={acc.id}>
                    {acc.nombre} (Disp: {simboloMoneda}{parseFloat(acc.saldo_disponible).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoadingLocal}
            className="w-full py-3 bg-[#006c49] hover:bg-[#005a3c] text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all shadow-sm"
          >
            {isLoadingLocal ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Crear Meta de Ahorro'}
          </button>
        </form>
      </Modal>

      {/* --- MODAL REGISTRAR APORTE A META --- */}
      <Modal
        isOpen={showAporte}
        onClose={() => setShowAporte(false)}
        title={selectedGoalForAporte ? `Aportar a: ${selectedGoalForAporte.nombre}` : 'Registrar Aporte'}
      >
        <form onSubmit={handleAporteSubmit} className="space-y-4 text-left">
          
          <div className="p-4 rounded-md bg-emerald-50 border border-emerald-100 space-y-1 text-left">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest block">Objetivo Restante</span>
            <div className="text-base font-black text-[#006c49]">
              {selectedGoalForAporte && `${simboloMoneda}${parseFloat(selectedGoalForAporte.falta_por_ahorrar).toLocaleString()}`}
            </div>
            <p className="text-[9px] text-[#64748b] font-bold leading-relaxed">
              El aporte se descontará del saldo disponible de la cuenta de respaldo ({selectedGoalForAporte?.cuenta_detalle?.nombre}).
            </p>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Monto del Aporte</label>
            <input
              type="number"
              step="0.01"
              required
              min="0.01"
              placeholder="0.00"
              value={montoAporte}
              onChange={(e) => setMontoAporte(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">Comentario / Nota (Opcional)</label>
            <input
              type="text"
              placeholder="ej. Ahorro quincena de mayo"
              value={descAporte}
              onChange={(e) => setDescAporte(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
            />
          </div>

          <button
            type="submit"
            disabled={isLoadingLocal}
            className="w-full py-3 bg-[#006c49] hover:bg-[#005a3c] text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all shadow-sm"
          >
            {isLoadingLocal ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Confirmar Aporte'}
          </button>
        </form>
      </Modal>

    </div>
  );
};

export default SavingsGoals;
