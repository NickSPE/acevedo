import { create } from 'zustand';
import api from '../services/api';

export const useFinanceStore = create((set, get) => ({
  accounts: [],
  subaccounts: [],
  transactions: [],
  goals: [],
  dashboardStats: null,
  tips: [],
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  // Cargar estadísticas generales del dashboard y cuentas
  fetchDashboardData: async () => {
    set({ isLoading: true });
    try {
      // 1. Obtener cuentas y balance principal
      const accountsRes = await api.get('cuentas/dashboard/stats/');
      
      // 2. Obtener movimientos recientes
      const movementsRes = await api.get('gestion-financiera/movimientos/?limit=5');
      
      // 3. Obtener metas de ahorro
      const goalsRes = await api.get('gestion-financiera/metas/');

      // 4. Obtener contador de notificaciones no leídas
      const notifCountRes = await api.get('alertas-notificaciones/contador/');

      const cuentasConSub = accountsRes.data.cuentas_con_subcuentas || [];
      const subVinculadas = cuentasConSub.flatMap(c => c.subcuentas || []);
      const subIndep = [
        ...(accountsRes.data.subcuentas_independientes_activas || []),
        ...(accountsRes.data.subcuentas_independientes_inactivas || [])
      ];
      const allSubaccounts = [...subVinculadas, ...subIndep];
      
      const allAccounts = cuentasConSub.map(c => c.cuenta) || [];
      if (accountsRes.data.cuenta_principal) {
        if (!allAccounts.some(c => c.id === accountsRes.data.cuenta_principal.id)) {
          allAccounts.push(accountsRes.data.cuenta_principal);
        }
      }

      set({
        accounts: allAccounts,
        subaccounts: allSubaccounts,
        dashboardStats: accountsRes.data,
        transactions: movementsRes.data.results || movementsRes.data || [],
        goals: goalsRes.data.goals || [],
        tips: goalsRes.data.tips_dinamicos || [],
        unreadCount: notifCountRes.data.count || 0,
        isLoading: false
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      set({ isLoading: false });
    }
  },

  // Cargar lista completa de transacciones (con filtros)
  fetchTransactions: async (filters = {}) => {
    set({ isLoading: true });
    try {
      const { filter = 'all', search = '', sort = 'newest' } = filters;
      const response = await api.get(`gestion-financiera/movimientos/?filter=${filter}&search=${search}&sort=${sort}`);
      set({ 
        transactions: response.data.results || response.data || [],
        isLoading: false 
      });
    } catch (error) {
      console.error('Error fetching transactions:', error);
      set({ isLoading: false });
    }
  },

  // Cargar metas de ahorro y consejos
  fetchGoals: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get('gestion-financiera/metas/');
      set({
        goals: response.data.goals || [],
        tips: response.data.tips_dinamicos || [],
        isLoading: false
      });
    } catch (error) {
      console.error('Error fetching goals:', error);
      set({ isLoading: false });
    }
  },

  // Crear transacción (Movimiento)
  createTransaction: async (transactionData) => {
    try {
      const response = await api.post('gestion-financiera/movimientos/', transactionData);
      // Recargar datos para actualizar saldos
      await get().fetchDashboardData();
      return { success: true, transaction: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'No se pudo registrar el movimiento.'
      };
    }
  },

  // Crear una nueva subcuenta
  createSubaccount: async (subaccountData) => {
    try {
      const response = await api.post('cuentas/subcuentas/', subaccountData);
      await get().fetchDashboardData();
      return { success: true, subaccount: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Error al crear la subcuenta.'
      };
    }
  },

  // Activar/Desactivar subcuenta
  toggleSubaccount: async (id) => {
    try {
      await api.post(`cuentas/subcuentas/${id}/activar/`);
      await get().fetchDashboardData();
      return { success: true };
    } catch (error) {
      return { success: false, error: 'No se pudo cambiar el estado de la subcuenta.' };
    }
  },

  // Eliminar subcuenta
  deleteSubaccount: async (id) => {
    try {
      await api.delete(`cuentas/subcuentas/${id}/`);
      await get().fetchDashboardData();
      return { success: true };
    } catch (error) {
      return { success: false, error: 'No se pudo eliminar la subcuenta.' };
    }
  },

  // Transferencia entre subcuentas
  transferBetweenSubaccounts: async (transferData) => {
    try {
      const response = await api.post('cuentas/transferencias/entre-subcuentas/', transferData);
      await get().fetchDashboardData();
      return { success: true, message: response.data.message };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Error al procesar la transferencia.'
      };
    }
  },

  // Transferencia con cuenta principal (Depósito / Retiro de subcuenta)
  transferPrincipal: async (transferData) => {
    try {
      const response = await api.post('cuentas/transferencias/cuenta-principal/', transferData);
      await get().fetchDashboardData();
      return { success: true, message: response.data.message };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Error al transferir con la cuenta principal.'
      };
    }
  },

  // Crear una nueva meta de ahorro
  createGoal: async (goalData) => {
    try {
      const response = await api.post('gestion-financiera/metas/', goalData);
      await get().fetchGoals();
      await get().fetchDashboardData();
      return { success: true, goal: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Error al crear la meta.'
      };
    }
  },

  // Aporte a una meta de ahorro
  addFundToGoal: async (aporteData) => {
    try {
      const response = await api.post('gestion-financiera/metas/aporte/', aporteData);
      await get().fetchGoals();
      await get().fetchDashboardData();
      return { success: true, message: response.data.message };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Error al realizar el aporte.'
      };
    }
  },

  // Eliminar una meta de ahorro
  deleteGoal: async (id) => {
    try {
      await api.delete(`gestion-financiera/metas/${id}/`);
      await get().fetchGoals();
      await get().fetchDashboardData();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Error al eliminar la meta.'
      };
    }
  },

  // Cargar historial de notificaciones
  fetchNotifications: async (showAll = false) => {
    try {
      const response = await api.get(`alertas-notificaciones/historial/?show_all=${showAll}`);
      set({ 
        notifications: response.data.notifications || response.data.results || [],
      });
      // Actualizar contador
      const countRes = await api.get('alertas-notificaciones/contador/');
      set({ unreadCount: countRes.data.count || 0 });
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  },

  // Marcar notificación como leída
  markAsRead: async (id) => {
    try {
      await api.post(`alertas-notificaciones/notificaciones/${id}/leer/`);
      const updated = get().notifications.map(n => n.id === id ? { ...n, read: true } : n);
      set(state => ({
        notifications: updated,
        unreadCount: Math.max(0, state.unreadCount - 1)
      }));
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  },

  // Marcar todas como leídas
  markAllAsRead: async () => {
    try {
      await api.post('alertas-notificaciones/notificaciones/leer-todas/');
      const updated = get().notifications.map(n => ({ ...n, read: true }));
      set({ notifications: updated, unreadCount: 0 });
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  }
}));
