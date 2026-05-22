import { create } from 'zustand';
import api, { setInMemoryToken, getInMemoryToken } from '../services/api';

export const useAuthStore = create((set, get) => {
  // Escuchar evento global de expiración de sesión
  if (typeof window !== 'undefined') {
    window.addEventListener('auth-expired', () => {
      set({ user: null, isAuthenticated: false, pinVerified: false });
    });
  }

  return {
    user: null,
    isAuthenticated: false,
    isLoading: true,
    pinVerified: false,

    // Verificar si el usuario ya está autenticado (Refresco silencioso al cargar)
    checkAuth: async () => {
      set({ isLoading: true });
      try {
        // Intentar refrescar token
        const refreshResponse = await api.post('usuarios/token/refresh/');
        if (refreshResponse.data && refreshResponse.data.access_token) {
          setInMemoryToken(refreshResponse.data.access_token);
          
          // Obtener perfil del usuario
          const profileResponse = await api.get('usuarios/profile/');
          set({
            user: profileResponse.data,
            isAuthenticated: true,
            pinVerified: false, // Forzar verificación de PIN para mayor seguridad
            isLoading: false,
          });
          return true;
        }
      } catch (error) {
        set({ user: null, isAuthenticated: false, pinVerified: false, isLoading: false });
      }
      set({ isLoading: false });
      return false;
    },

    // Iniciar sesión
    login: async (correo, password) => {
      set({ isLoading: true });
      try {
        const response = await api.post('usuarios/login/', { correo, password });
        if (response.data && response.data.access_token) {
          setInMemoryToken(response.data.access_token);
          set({
            user: response.data.usuario,
            isAuthenticated: true,
            pinVerified: false,
            isLoading: false,
          });
          return { success: true };
        }
      } catch (error) {
        set({ isLoading: false });
        return {
          success: false,
          error: error.response?.data?.error || 'Error al iniciar sesión. Intenta de nuevo.'
        };
      }
    },

    // Iniciar sesión con PIN
    loginWithPin: async (pinInput) => {
      set({ isLoading: true });
      try {
        const response = await api.post('usuarios/login/pin/', { pin_input: pinInput });
        if (response.data && response.data.access_token) {
          setInMemoryToken(response.data.access_token);
          set({
            user: response.data.usuario,
            isAuthenticated: true,
            pinVerified: true, // El PIN ya ha sido verificado al loguearse con él
            isLoading: false,
          });
          return { success: true };
        }
      } catch (error) {
        set({ isLoading: false });
        return {
          success: false,
          error: error.response?.data?.error || 'PIN incorrecto. Intenta de nuevo.'
        };
      }
    },

    // Registrarse

    register: async (registerData) => {
      set({ isLoading: true });
      try {
        const response = await api.post('usuarios/register/', registerData);
        set({ isLoading: false });
        return { success: true, message: response.data.message };
      } catch (error) {
        set({ isLoading: false });
        return {
          success: false,
          error: error.response?.data?.error || 'Error en el registro. Verifica los campos.'
        };
      }
    },

    // Validar PIN de acceso rápido
    verifyPin: async (pinInput) => {
      try {
        const response = await api.post('usuarios/acceso-rapido/validate/', { pin_input: pinInput });
        if (response.data && response.data.success) {
          set({ pinVerified: true });
          return { success: true };
        }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || 'PIN incorrecto. Intenta de nuevo.'
        };
      }
    },

    // Cerrar sesión
    logout: async () => {
      try {
        await api.post('usuarios/logout/');
      } catch (error) {
        // Ignorar error al desloguear y limpiar estado local de todas formas
      }
      setInMemoryToken(null);
      set({ user: null, isAuthenticated: false, pinVerified: false });
    },

    // Actualizar perfil
    updateProfile: async (profileData) => {
      try {
        const response = await api.put('usuarios/profile/', profileData);
        set({ user: response.data });
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || 'Error al actualizar el perfil.'
        };
      }
    },

    // Completar onboarding
    completeOnboarding: async (onboardingData) => {
      try {
        const response = await api.post('usuarios/onboarding/', onboardingData);
        if (response.data && response.data.success) {
          // Refrescar perfil del usuario
          const profileResponse = await api.get('usuarios/profile/');
          set({ user: profileResponse.data });
          return { success: true };
        }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || 'Error al guardar onboarding.'
        };
      }
    }
  };
});
