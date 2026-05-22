import React, { useEffect, useState } from 'react';
import { useFinanceStore } from '../store/useFinanceStore';
import { useAuthStore } from '../store/useAuthStore';
import { 
  ArrowUpRight, 
  Search, 
  Filter, 
  ArrowUpDown, 
  Plus, 
  Calendar, 
  Tag, 
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { TableSkeleton } from '../components/LoadingSkeleton';
import Modal from '../components/Modal';

const Transactions = () => {
  const user = useAuthStore(state => state.user);
  const { 
    transactions, 
    subaccounts,
    fetchTransactions, 
    createTransaction, 
    isLoading 
  } = useFinanceStore();

  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all'); // 'all', 'INGRESO', 'EGRESO'
  const [sort, setSort] = useState('newest'); // 'newest', 'oldest', 'amount_desc', 'amount_asc'

  const [showAddTransaction, setShowAddTransaction] = useState(false);
  const [transactionType, setTransactionType] = useState('EGRESO');
  const [monto, setMonto] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [categoria, setCategoria] = useState('Alimentación');
  const [subcuentaId, setSubcuentaId] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchTransactions({ search, filter, sort });
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [search, filter, sort]);

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
      fetchTransactions({ search, filter, sort });
    } else {
      setErrorMessage(res.error);
    }
  };

  const simboloMoneda = user?.id_moneda?.simbolo || '$';

  return (
    <div className="p-6 space-y-6">
      
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-left">
        <div>
          <h2 className="text-lg font-black text-[#0f172a] tracking-tight">Historial de Transacciones</h2>
          <p className="text-xs text-[#64748b] mt-0.5">Explora, filtra y añade movimientos financieros en tu cuenta.</p>
        </div>
        
        <button
          onClick={() => { setTransactionType('EGRESO'); setShowAddTransaction(true); }}
          className="flex items-center gap-2 px-5 py-3 bg-[#0f172a] hover:bg-slate-800 active:scale-[0.99] text-white rounded-md text-xs font-black uppercase tracking-wider transition-all self-stretch sm:self-auto text-center justify-center shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Nuevo Movimiento</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center text-left">
        {/* Search */}
        <div className="md:col-span-2 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por descripción o categoría..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 transition-all font-bold shadow-sm"
          />
        </div>

        {/* Filter Type */}
        <div className="relative">
          <Filter className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 transition-all font-black cursor-pointer appearance-none shadow-sm"
          >
            <option value="all">Todos los Movimientos</option>
            <option value="INGRESO">Solo Ingresos</option>
            <option value="EGRESO">Solo Egresos</option>
          </select>
        </div>

        {/* Sorting */}
        <div className="relative">
          <ArrowUpDown className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] focus:ring-1 focus:ring-[#0f172a]/20 transition-all font-black cursor-pointer appearance-none shadow-sm"
          >
            <option value="newest">Más Recientes primero</option>
            <option value="oldest">Más Antiguos primero</option>
            <option value="amount_desc">Monto Mayor primero</option>
            <option value="amount_asc">Monto Menor primero</option>
          </select>
        </div>
      </div>

      {/* Main Table / List Card */}
      {isLoading ? (
        <TableSkeleton />
      ) : (
        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm overflow-hidden">
          <div className="divide-y divide-slate-100">
            {transactions.length === 0 ? (
              <div className="py-12 text-center text-slate-400 flex flex-col items-center justify-center gap-2">
                <p className="text-xs font-bold">No se encontraron movimientos con los filtros aplicados.</p>
                <button 
                  onClick={() => { setSearch(''); setFilter('all'); setSort('newest'); }}
                  className="text-xs text-[#006c49] font-black hover:underline"
                >
                  Restablecer filtros
                </button>
              </div>
            ) : (
              transactions.map((trans) => (
                <div key={trans.id} className="py-4 flex justify-between items-center group transition-colors text-left">
                  <div className="flex items-center gap-4">
                    
                    {/* Icon indicator */}
                    <div className={`
                      w-9 h-9 rounded-md flex items-center justify-center shadow-sm
                      ${trans.tipo === 'INGRESO' ? 'bg-[#f0fdf4] text-[#006c49]' : 'bg-slate-50 text-[#64748b]'}
                    `}>
                      {trans.tipo === 'INGRESO' ? (
                        <TrendingUp className="w-4.5 h-4.5" />
                      ) : (
                        <TrendingDown className="w-4.5 h-4.5" />
                      )}
                    </div>

                    {/* Metadata details */}
                    <div className="text-left space-y-1">
                      <p className="text-xs font-bold text-[#0f172a] group-hover:text-[#006c49] transition-colors">
                        {trans.descripcion}
                      </p>
                      
                      <div className="flex flex-wrap items-center gap-2.5 text-[10px] text-slate-450 font-bold">
                        {/* Categoria Badge */}
                        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-extrabold uppercase">
                          <Tag className="w-3 h-3 text-slate-400" />
                          <span>{trans.categoria}</span>
                        </span>
                        
                        {/* Fecha */}
                        <span className="flex items-center gap-1 font-bold">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>{new Date(trans.fecha || trans.fecha_creacion).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Amount colored dynamically */}
                  <span className={`text-sm font-black ${trans.tipo === 'INGRESO' ? 'text-[#006c49]' : 'text-[#0f172a]'}`}>
                    {trans.tipo === 'INGRESO' ? '+' : '-'}{simboloMoneda}{parseFloat(trans.monto).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>

                </div>
              ))
            )}
          </div>
        </div>
      )}

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

export default Transactions;
