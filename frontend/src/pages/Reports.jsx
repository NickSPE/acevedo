import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { 
  FileText, 
  Download, 
  Trash2, 
  Calendar, 
  TrendingUp, 
  PieChart as PieIcon, 
  Layers,
  Plus,
  Loader2,
  AlertCircle,
  CheckCircle,
  FileSpreadsheet
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell,
  AreaChart,
  Area
} from 'recharts';

const COLORS = ['#0f172a', '#006c49', '#3b82f6', '#f59e0b', '#8b5cf6', '#14b8a6', '#6366f1'];

const Reports = () => {
  const user = useAuthStore(state => state.user);
  const simboloMoneda = user?.id_moneda?.simbolo || '$';

  // Estados de carga y datos
  const [isLoading, setIsLoading] = useState(false);
  const [statsData, setStatsData] = useState(null);
  const [reportsList, setReportsList] = useState([]);
  
  // Filtros de estadísticas
  const [periodo, setPeriodo] = useState('mes_actual');
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');

  // Creación de reporte
  const [showCreate, setShowCreate] = useState(false);
  const [tipoReporte, setTipoReporte] = useState('gastos_categoria');
  const [tituloReporte, setTituloReporte] = useState('');
  const [repFechaInicio, setRepFechaInicio] = useState('');
  const [repFechaFin, setRepFechaFin] = useState('');
  
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isActionLoading, setIsActionLoading] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchReports();
  }, [periodo, fechaInicio, fechaFin]);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      let url = `analisis-reportes/dashboard/?periodo=${periodo}`;
      if (periodo === 'personalizado' && fechaInicio && fechaFin) {
        url += `&fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
      }
      const res = await api.get(url);
      if (res.data && res.data.success) {
        setStatsData(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      const res = await api.get('analisis-reportes/reportes/');
      setReportsList(res.data.results || res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateReport = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!repFechaInicio || !repFechaFin) {
      setErrorMsg('Las fechas de inicio y fin son obligatorias.');
      return;
    }

    setIsActionLoading(true);
    try {
      const payload = {
        tipo_reporte: tipoReporte,
        titulo: tituloReporte.trim() || `Reporte de ${tipoReporte.replace('_', ' ')}`,
        fecha_inicio: repFechaInicio,
        fecha_fin: repFechaFin
      };

      const res = await api.post('analisis-reportes/reportes/', payload);
      if (res.status === 201 || res.status === 200) {
        setSuccessMsg('Reporte generado exitosamente.');
        setTituloReporte('');
        setShowCreate(false);
        fetchReports();
        setTimeout(() => setSuccessMsg(''), 3000);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.error || 'Error al generar el reporte.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleDeleteReport = async (id) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este reporte?')) return;
    try {
      await api.delete(`analisis-reportes/reportes/${id}/`);
      setReportsList(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDownload = async (id, filename, format) => {
    try {
      const res = await api.get(`analisis-reportes/reportes/${id}/exportar/${format}/`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([res.data], { type: res.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      let fileExt = format;
      if (format === 'excel') fileExt = 'xlsx';
      
      link.setAttribute('download', `${filename.replace(/\s+/g, '_')}_${id}.${fileExt}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Error al descargar el archivo.');
    }
  };

  const getTipoLabel = (tipo) => {
    const tipos = {
      gastos_categoria: 'Gastos por Categoría',
      ingresos_egresos: 'Ingresos vs Egresos',
      subcuentas_analisis: 'Análisis de Subcuentas',
      balance_general: 'Balance General',
      flujo_efectivo: 'Flujo de Efectivo'
    };
    return tipos[tipo] || tipo;
  };

  return (
    <div className="p-6 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="text-left">
          <h2 className="text-lg font-black text-[#0f172a] tracking-tight">Reportes & Estadísticas</h2>
          <p className="text-xs text-[#64748b] mt-0.5 font-bold">Analiza tus métricas financieras, genera reportes históricos y expórtalos.</p>
        </div>

        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-5 py-3 bg-[#0f172a] hover:bg-slate-800 active:scale-[0.99] text-white rounded-md text-xs font-black uppercase tracking-wider shadow-sm transition-all self-stretch sm:self-auto justify-center"
        >
          <Plus className="w-4 h-4" />
          <span>Generar Nuevo Reporte</span>
        </button>
      </div>

      {/* Alertas de Feedback */}
      {successMsg && (
        <div className="p-3 text-xs font-bold rounded-md bg-emerald-50 border border-emerald-100 text-[#006c49] text-center animate-fade-in flex items-center justify-center gap-2 shadow-sm">
          <CheckCircle className="w-4 h-4" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3 text-xs font-bold rounded-md bg-rose-50 border border-rose-100 text-rose-600 text-center animate-fade-in flex items-center justify-center gap-2 shadow-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Formulario de generación rápida (Inline/Desplegable) */}
      {showCreate && (
        <form onSubmit={handleCreateReport} className="p-6 rounded-md bg-white border border-slate-200 space-y-4 animate-slide-up text-left shadow-sm">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Generar Reporte Personalizado</h3>
            <p className="text-[10px] text-[#64748b] font-bold">Completa las variables para compilar y guardar un nuevo reporte exportable.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Título del Reporte</label>
              <input
                type="text"
                placeholder="ej. Balance Primer Trimestre"
                value={tituloReporte}
                onChange={(e) => setTituloReporte(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] font-bold shadow-sm"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Tipo de Análisis</label>
              <select
                value={tipoReporte}
                onChange={(e) => setTipoReporte(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              >
                <option value="gastos_categoria">Gastos por Categoría</option>
                <option value="ingresos_egresos">Ingresos vs Egresos</option>
                <option value="subcuentas_analisis">Análisis de Subcuentas</option>
                <option value="balance_general">Balance General</option>
                <option value="flujo_efectivo">Flujo de Efectivo</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Fecha de Inicio</label>
              <input
                type="date"
                required
                value={repFechaInicio}
                onChange={(e) => setRepFechaInicio(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-[#64748b] uppercase tracking-widest pl-0.5">Fecha de Fin</label>
              <input
                type="date"
                required
                value={repFechaFin}
                onChange={(e) => setRepFechaFin(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none focus:border-[#0f172a] cursor-pointer font-bold shadow-sm"
              />
            </div>
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-150 text-slate-700 rounded-md text-xs font-black uppercase tracking-wider"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isActionLoading}
              className="px-5 py-2 bg-[#0f172a] hover:bg-slate-800 text-white rounded-md text-xs font-black uppercase tracking-wider flex items-center gap-1 active:scale-[0.99] transition-all disabled:opacity-50 shadow-sm"
            >
              {isActionLoading ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : 'Compilar Reporte'}
            </button>
          </div>
        </form>
      )}

      {/* Filtros de Dashboard Estadístico */}
      <div className="p-4 rounded-md bg-white border border-slate-200 flex flex-wrap gap-4 items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <Calendar className="w-4.5 h-4.5 text-[#006c49]" />
          <span className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Período de Análisis</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            className="px-3 py-2 bg-white border border-slate-200 rounded-md text-xs text-[#0f172a] focus:outline-none font-bold cursor-pointer shadow-sm focus:border-[#0f172a]"
          >
            <option value="mes_actual">Mes Actual</option>
            <option value="mes_anterior">Mes Anterior</option>
            <option value="ano_actual">Año Actual</option>
            <option value="personalizado">Rango Personalizado</option>
          </select>

          {periodo === 'personalizado' && (
            <div className="flex items-center gap-2 animate-fade-in">
              <input
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-200 rounded-md text-[11px] text-[#0f172a] focus:outline-none font-bold shadow-sm"
              />
              <span className="text-xs text-slate-400 font-bold">a</span>
              <input
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-200 rounded-md text-[11px] text-[#0f172a] focus:outline-none font-bold shadow-sm"
              />
            </div>
          )}
        </div>
      </div>

      {/* Gráficos y Métricas */}
      {isLoading ? (
        <div className="py-24 text-center flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-[#0f172a]" />
          <span className="text-xs text-slate-455 uppercase tracking-widest font-black">Procesando Estadísticas...</span>
        </div>
      ) : (
        statsData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Gráfico 1: Ingresos vs Egresos */}
            {statsData.ingresos_egresos && (
              <div className="p-6 rounded-md bg-white border border-slate-200 space-y-4 shadow-sm">
                <div className="flex items-center gap-2 text-left">
                  <TrendingUp className="w-4 h-4 text-[#006c49]" />
                  <h3 className="text-[10px] font-black text-[#0f172a] uppercase tracking-widest">Ingresos vs Egresos</h3>
                </div>

                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { name: 'Ingresos', Monto: statsData.ingresos_egresos.ingresos || 0 },
                        { name: 'Egresos', Monto: statsData.ingresos_egresos.egresos || 0 }
                      ]}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `${simboloMoneda}${v}`} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '6px' }} 
                        itemStyle={{ color: '#0f172a', fontSize: '11px', fontWeight: 'bold' }}
                      />
                      <Bar dataKey="Monto" radius={[4, 4, 0, 0]}>
                        <Cell fill="#006c49" />
                        <Cell fill="#0f172a" />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Gráfico 2: Distribución de Gastos */}
            {statsData.gastos_categoria && statsData.gastos_categoria.length > 0 && (
              <div className="p-6 rounded-md bg-white border border-slate-200 space-y-4 shadow-sm">
                <div className="flex items-center gap-2 text-left">
                  <PieIcon className="w-4 h-4 text-[#006c49]" />
                  <h3 className="text-[10px] font-black text-[#0f172a] uppercase tracking-widest">Gastos por Categoría</h3>
                </div>

                <div className="h-64 flex flex-col sm:flex-row items-center gap-6">
                  <div className="flex-1 h-full w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={statsData.gastos_categoria}
                          dataKey="total"
                          nameKey="categoria__nombre"
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={3}
                        >
                          {statsData.gastos_categoria.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '6px' }}
                          itemStyle={{ fontSize: '11px', color: '#0f172a', fontWeight: 'bold' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Legend list */}
                  <div className="flex flex-col gap-2 text-left text-[10px] w-full sm:w-48 overflow-y-auto max-h-56 pr-2">
                    {statsData.gastos_categoria.map((entry, index) => (
                      <div key={index} className="flex justify-between items-center gap-4">
                        <div className="flex items-center gap-1.5 font-bold text-[#64748b]">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                          <span className="truncate max-w-28 capitalize">{entry.categoria__nombre}</span>
                        </div>
                        <span className="font-black text-[#0f172a]">{simboloMoneda}{parseFloat(entry.total).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Gráfico 3: Flujo de Caja Mensual */}
            {statsData.flujo_mensual && statsData.flujo_mensual.length > 0 && (
              <div className="p-6 rounded-md bg-white border border-slate-200 space-y-4 lg:col-span-2 shadow-sm">
                <div className="flex items-center gap-2 text-left">
                  <Layers className="w-4 h-4 text-[#006c49]" />
                  <h3 className="text-[10px] font-black text-[#0f172a] uppercase tracking-widest">Flujo de Efectivo Mensual</h3>
                </div>

                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={statsData.flujo_mensual.map(d => ({
                        Fecha: d.fecha_movimiento__month ? `Mes ${d.fecha_movimiento__month}` : d.fecha_movimiento,
                        Ingresos: d.ingresos || 0,
                        Egresos: d.egresos || 0
                      }))}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <XAxis dataKey="Fecha" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `${simboloMoneda}${v}`} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '6px' }} />
                      <Legend verticalAlign="top" height={36} iconType="circle" fontSize={11} />
                      <Area type="monotone" dataKey="Ingresos" stroke="#006c49" fillOpacity={0.05} fill="#006c49" />
                      <Area type="monotone" dataKey="Egresos" stroke="#0f172a" fillOpacity={0.05} fill="#0f172a" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

          </div>
        )
      )}

      {/* Historial de Reportes Compilados */}
      <div className="p-6 rounded-md bg-white border border-slate-200 space-y-4 text-left shadow-sm">
        <div className="pb-2 border-b border-slate-100">
          <h3 className="text-xs font-black text-[#0f172a] uppercase tracking-wider">Reportes Compilados Guardados</h3>
          <p className="text-[10px] text-[#64748b] font-bold">Historial de análisis financieros generados para su exportación.</p>
        </div>

        <div className="overflow-x-auto rounded-md border border-slate-200">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 font-black uppercase tracking-widest text-[9px] border-b border-slate-200">
                <th className="px-5 py-3">Título</th>
                <th className="px-5 py-3">Tipo</th>
                <th className="px-5 py-3">Rango de Fechas</th>
                <th className="px-5 py-3">Generación</th>
                <th className="px-5 py-3 text-center">Exportar</th>
                <th className="px-5 py-3 text-center">Eliminar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reportsList.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-5 py-8 text-center text-slate-400 font-bold italic">
                    No has compilado ningún reporte personalizado aún.
                  </td>
                </tr>
              ) : (
                reportsList.map((rep) => (
                  <tr key={rep.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-bold text-[#0f172a] flex items-center gap-2">
                      <FileText className="w-4 h-4 text-[#64748b]" />
                      <span>{rep.titulo}</span>
                    </td>
                    <td className="px-5 py-4 text-slate-500 font-bold">{getTipoLabel(rep.tipo_reporte)}</td>
                    <td className="px-5 py-4 text-[#64748b] font-bold">
                      {new Date(rep.fecha_inicio).toLocaleDateString()} al {new Date(rep.fecha_fin).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4 text-slate-400 font-bold">
                      {new Date(rep.fecha_creacion).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          onClick={() => handleDownload(rep.id, rep.titulo, 'pdf')}
                          className="px-2.5 py-1 bg-rose-50 border border-rose-100 text-rose-600 rounded text-[9px] font-black uppercase tracking-wider hover:bg-rose-100 transition-all flex items-center gap-1 shadow-sm"
                          title="Descargar PDF"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>PDF</span>
                        </button>
                        <button
                          onClick={() => handleDownload(rep.id, rep.titulo, 'excel')}
                          className="px-2.5 py-1 bg-emerald-50 border border-emerald-100 text-[#006c49] rounded text-[9px] font-black uppercase tracking-wider hover:bg-emerald-100 transition-all flex items-center gap-1 shadow-sm"
                          title="Descargar Excel"
                        >
                          <FileSpreadsheet className="w-3.5 h-3.5" />
                          <span>EXCEL</span>
                        </button>
                        <button
                          onClick={() => handleDownload(rep.id, rep.titulo, 'csv')}
                          className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-700 rounded text-[9px] font-black uppercase tracking-wider hover:bg-slate-100 transition-all flex items-center gap-1 shadow-sm"
                          title="Descargar CSV"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>CSV</span>
                        </button>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <button
                        onClick={() => handleDeleteReport(rep.id)}
                        className="p-1.5 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Eliminar Reporte"
                      >
                        <Trash2 className="w-4.5 h-4.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

export default Reports;
