import React, { useEffect, useState } from 'react';
import { useFinanceStore } from '../store/useFinanceStore';
import { useAuthStore } from '../store/useAuthStore';
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  PiggyBank, 
  Plus, 
  ArrowRightLeft, 
  ArrowUpRight,
  ChevronRight,
  AlertCircle
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { CardSkeleton, ChartSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import Modal from '../components/Modal';
import { Link } from 'react-router-dom';

const COLORS = ['#0f172a', '#10b981', '#6366f1', '#f59e0b', '#3b82f6', '#ec4899'];

const Dashboard = () => {
  const user = useAuthStore(state => state.user);
  const { 
    dashboardStats, 
    transactions, 
    goals, 
    subaccounts,
    fetchDashboardData, 
    createTransaction, 
    isLoading 
  } = useFinanceStore();

  const [showAddTransaction, setShowAddTransaction] = useState(false);
  const [transactionType, setTransactionType] = useState('EGRESO');
  const [monto, setMonto] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [categoria, setCategoria] = useState('Alimentación');
  const [subcuentaId, setSubcuentaId] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleCreateTransaction = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!monto || parseFloat(monto) <= 0) {
      setErrorMessage('El monto debe ser mayor a 0.');
      return;
    }

    const payload = {
      tipo: transactionType,
      monto: parseFloat(monto),
      descripcion: descripcion || (transactionType === 'INGRESO' ? 'Depósito' : 'Gasto'),
      categoria: categoria
    };

    if (transactionType === 'EGRESO' && subcuentaId) {
      payload.subcuenta_id = subcuentaId;
    }

    const res = await createTransaction(payload);
    if (res.success) {
      setShowAddTransaction(false);
      setMonto('');
      setDescripcion('');
      setSubcuentaId('');
    } else {
      setErrorMessage(res.error);
    }
  };

  if (isLoading && !dashboardStats) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2"><ChartSkeleton /></div>
          <div><TableSkeleton /></div>
        </div>
      </div>
    );
  }

  const chartData = dashboardStats?.grafico_flujo_efectivo || [
    { name: 'Ene', ingresos: 400, egresos: 240 },
    { name: 'Feb', ingresos: 300, egresos: 139 },
    { name: 'Mar', ingresos: 200, egresos: 380 },
    { name: 'Abr', ingresos: 278, egresos: 390 },
    { name: 'May', ingresos: 189, egresos: 480 },
    { name: 'Jun', ingresos: 239, egresos: 380 },
  ];

  const categoryData = dashboardStats?.grafico_gastos_categoria?.map((item) => ({
    name: item.categoria,
    value: parseFloat(item.total)
  })) || [];

  const balanceTotal = dashboardStats?.balance_total || 0;
  const balancePrincipal = dashboardStats?.balance_principal || 0;
  const balanceSubcuentas = dashboardStats?.balance_subcuentas || 0;
  const ingresosMes = dashboardStats?.ingresos_mes || 0;
  const egresosMes = dashboardStats?.egresos_mes || 0;
  const simboloMoneda = user?.id_moneda?.simbolo || '$';

  return (
    <div className="p-6 space-y-6">
      
      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Balance Total Card */}
        <div className="p-6 rounded-md bg-[#0f172a] border border-[#0f172a] text-white shadow-sm relative overflow-hidden group text-left">
          <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white/5 rounded-full blur-xl transition-colors" />
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Balance Total</span>
            <div className="p-2 rounded-md bg-white/10 text-white">
              <Wallet className="w-4.5 h-4.5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-black text-white tracking-tight">
              {simboloMoneda}{balanceTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-slate-300 mt-2 flex items-center gap-1.5 font-bold">
              <span>Principal: <strong>{simboloMoneda}{balancePrincipal.toLocaleString()}</strong></span>
              <span className="text-slate-500">•</span>
              <span>Subcuentas: <strong>{simboloMoneda}{balanceSubcuentas.toLocaleString()}</strong></span>
            </p>
          </div>
        </div>

        {/* Ingresos Mes Card */}
        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm relative overflow-hidden group text-left">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Ingresos del Mes</span>
            <div className="p-2 rounded-md bg-emerald-50 text-[#006c49]">
              <TrendingUp className="w-4.5 h-4.5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-black text-[#0f172a] tracking-tight">
              {simboloMoneda}{ingresosMes.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-[#006c49] mt-2 flex items-center gap-1 font-bold">
              <span className="inline-block px-1.5 py-0.5 rounded bg-emerald-50 font-black text-[9px] uppercase tracking-wider">
                Activo
              </span>
              <span className="text-slate-450">Total recibido en el periodo.</span>
            </p>
          </div>
        </div>

        {/* Egresos Mes Card */}
        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm relative overflow-hidden group text-left">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Egresos del Mes</span>
            <div className="p-2 rounded-md bg-rose-50 text-rose-600">
              <TrendingDown className="w-4.5 h-4.5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-black text-[#0f172a] tracking-tight">
              {simboloMoneda}{egresosMes.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-rose-600 mt-2 flex items-center gap-1 font-bold">
              <span className="inline-block px-1.5 py-0.5 rounded bg-rose-50 font-black text-[9px] uppercase tracking-wider">
                Controlado
              </span>
              <span className="text-slate-450">Gastos y aportes ejecutados.</span>
            </p>
          </div>
        </div>

        {/* Metas Ahorro Card */}
        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm relative overflow-hidden group text-left">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Metas Activas</span>
            <div className="p-2 rounded-md bg-[#eff4ff] text-[#0f172a]">
              <PiggyBank className="w-4.5 h-4.5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-black text-[#0f172a] tracking-tight">
              {goals.length}
            </h3>
            <p className="text-[11px] text-[#64748b] mt-2 font-bold">
              Progreso acumulado: <strong className="text-[#0f172a]">
                {goals.length > 0 ? `${Math.round(goals.reduce((acc, curr) => acc + (curr.porcentaje_progreso || 0), 0) / goals.length)}%` : '0%'}
              </strong>
            </p>
          </div>
        </div>
      </div>

      {/* Quick Action Buttons */}
      <div className="flex flex-wrap gap-4 items-center">
        <button
          onClick={() => { setTransactionType('EGRESO'); setShowAddTransaction(true); }}
          className="flex items-center gap-2 px-5 py-3 bg-[#0f172a] hover:bg-slate-800 active:scale-[0.99] text-white rounded-md text-xs font-black uppercase tracking-wider transition-all shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Registrar Gasto</span>
        </button>
        <button
          onClick={() => { setTransactionType('INGRESO'); setShowAddTransaction(true); }}
          className="flex items-center gap-2 px-5 py-3 bg-white hover:bg-slate-50 active:scale-[0.99] border border-slate-200 text-[#0f172a] rounded-md text-xs font-black uppercase tracking-wider transition-all shadow-sm"
        >
          <Plus className="w-4 h-4 text-[#006c49]" />
          <span>Registrar Ingreso</span>
        </button>
        <Link
          to="/metas"
          className="flex items-center gap-2 px-5 py-3 bg-white hover:bg-slate-50 active:scale-[0.99] border border-slate-200 text-[#0f172a] rounded-md text-xs font-black uppercase tracking-wider transition-all shadow-sm"
        >
          <ArrowRightLeft className="w-4 h-4 text-[#0f172a]" />
          <span>Manejar Subcuentas</span>
        </Link>
      </div>

      {/* Main Charts & Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Double Bar Chart */}
        <div className="lg:col-span-2 p-6 rounded-md bg-white border border-slate-200 shadow-sm space-y-4 text-left">
          <div className="flex justify-between items-center">
            <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Flujo de Efectivo Mensual</h4>
            <span className="text-[10px] uppercase font-black tracking-widest text-slate-400">Últimos meses</span>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '6px' }}
                  labelStyle={{ color: '#0f172a', fontSize: '11px', fontWeight: 'bold' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Bar dataKey="ingresos" name="Ingresos" fill="#0f172a" radius={[2, 2, 0, 0]} />
                <Bar dataKey="egresos" name="Egresos" fill="#10b981" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Expenses Pie Chart */}
        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between text-left">
          <div>
            <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Gastos por Categoría</h4>
            <p className="text-xs text-[#64748b] font-bold">Distribución de egresos mensuales</p>
          </div>
          
          {categoryData.length === 0 ? (
            <div className="flex flex-col items-center justify-center flex-1 py-10 text-slate-400">
              <AlertCircle className="w-7 h-7 mb-1.5 text-slate-350" />
              <p className="text-xs font-bold">Sin gastos registrados en el periodo.</p>
            </div>
          ) : (
            <>
              <div className="h-44 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '6px' }}
                      itemStyle={{ fontSize: '12px', color: '#0f172a' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend List */}
              <div className="grid grid-cols-2 gap-2 text-xs overflow-y-auto max-h-32 pt-2 border-t border-slate-100">
                {categoryData.slice(0, 6).map((item, idx) => (
                  <div key={item.name} className="flex items-center gap-1.5 truncate">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                    <span className="text-[#64748b] font-bold truncate">{item.name}</span>
                    <span className="text-[#0f172a] font-black ml-auto">{simboloMoneda}{item.value}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Bottom Section: Recent Movements */}
      <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm space-y-4 text-left">
        <div className="flex justify-between items-center">
          <div>
            <h4 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Actividad y Movimientos Recientes</h4>
            <p className="text-xs text-[#64748b] font-bold">Últimas transacciones registradas</p>
          </div>
          <Link 
            to="/transacciones" 
            className="text-xs text-[#006c49] hover:underline font-black flex items-center gap-0.5 transition-colors uppercase tracking-wider"
          >
            <span>Ver todo</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Transactions list */}
        <div className="divide-y divide-slate-100">
          {transactions.length === 0 ? (
            <div className="py-8 text-center text-slate-400 text-xs font-bold">
              No tienes movimientos registrados aún. ¡Prueba a crear uno arriba!
            </div>
          ) : (
            transactions.slice(0, 5).map((trans) => (
              <div key={trans.id} className="py-3.5 flex justify-between items-center group">
                <div className="flex items-center gap-3">
                  <div className={`
                    w-8 h-8 rounded-md flex items-center justify-center shadow-sm
                    ${trans.tipo === 'INGRESO' ? 'bg-[#f0fdf4] text-[#006c49]' : 'bg-slate-50 text-[#64748b]'}
                  `}>
                    <ArrowUpRight className={`w-4 h-4 ${trans.tipo === 'INGRESO' ? 'rotate-0' : 'rotate-90'}`} />
                  </div>
                  <div className="text-left">
                    <p className="text-xs font-bold text-[#0f172a] group-hover:text-[#006c49] transition-colors">
                      {trans.descripcion}
                    </p>
                    <div className="flex gap-2 text-[10px] text-slate-450 items-center font-bold">
                      <span className="px-1 rounded bg-slate-100 text-slate-500 uppercase">{trans.categoria}</span>
                      <span>•</span>
                      <span>{new Date(trans.fecha || trans.fecha_creacion).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                
                <span className={`text-sm font-black ${trans.tipo === 'INGRESO' ? 'text-[#006c49]' : 'text-[#0f172a]'}`}>
                  {trans.tipo === 'INGRESO' ? '+' : '-'}{simboloMoneda}{parseFloat(trans.monto).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Transaction Modal */}
      <Modal 
        isOpen={showAddTransaction} 
        onClose={() => { setShowAddTransaction(false); setErrorMessage(''); }}
        title={transactionType === 'INGRESO' ? 'Registrar Ingreso' : 'Registrar Gasto'}
      >
        <form onSubmit={handleCreateTransaction} className="space-y-4 text-left">
          
          {errorMessage && (
            <div className="p-3 text-xs font-bold rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center">
              {errorMessage}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-450 uppercase tracking-widest pl-0.5">
              Monto ({simboloMoneda})
            </label>
            <input
              type="number"
              step="0.01"
              required
              min="0.01"
              placeholder="0.00"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">
              Descripción
            </label>
            <input
              type="text"
              required
              placeholder={transactionType === 'INGRESO' ? 'ej. Sueldo quincenal' : 'ej. Compra supermercado'}
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5">
              Categoría
            </label>
            <select
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold"
            >
              {transactionType === 'INGRESO' ? (
                <>
                  <option value="Sueldo">Sueldo / Salario</option>
                  <option value="Negocio">Negocios</option>
                  <option value="Inversiones">Inversiones</option>
                  <option value="Otros Ingresos">Otros Ingresos</option>
                </>
              ) : (
                <>
                  <option value="Alimentación">Alimentación</option>
                  <option value="Transporte">Transporte / Vehículo</option>
                  <option value="Vivienda">Vivienda / Alquiler</option>
                  <option value="Servicios">Servicios (Agua, Luz, Internet)</option>
                  <option value="Educación">Educación</option>
                  <option value="Entretenimiento">Entretenimiento / Ocio</option>
                  <option value="Otros Gastos">Otros Gastos</option>
                </>
              )}
            </select>
          </div>

          {transactionType === 'EGRESO' && subaccounts.length > 0 && (
            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-455 uppercase tracking-widest pl-0.5 flex items-center justify-between">
                <span>Vincular a Subcuenta / Meta (Opcional)</span>
                <span className="text-[9px] text-slate-400 font-semibold lowercase">(Descuenta de meta)</span>
              </label>
              <select
                value={subcuentaId}
                onChange={(e) => setSubcuentaId(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold"
              >
                <option value="">Ninguna - Retirar de Cuenta Principal</option>
                {subaccounts.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.nombre} (Disponible: {simboloMoneda}{parseFloat(sub.saldo || 0).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            type="submit"
            className="w-full py-3 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider active:scale-[0.99] transition-all flex items-center justify-center gap-1.5"
          >
            <span>Confirmar Registro</span>
          </button>
        </form>
      </Modal>

    </div>
  );
};

export default Dashboard;
