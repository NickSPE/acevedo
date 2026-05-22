import axios from 'axios';

// Crear instancia de Axios con la URL base de nuestro Backend de Django
const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  withCredentials: true, // Permitir envío automático de cookies HttpOnly (refresh_token)
  headers: {
    'Content-Type': 'application/json',
  }
});

// Referencia en memoria al token de acceso
let inMemoryToken = null;

export const setInMemoryToken = (token) => {
  inMemoryToken = token;
};

export const getInMemoryToken = () => {
  return inMemoryToken;
};

// Interceptor de Solicitudes: Adjuntar el token de acceso en memoria
api.interceptors.request.use(
  (config) => {
    if (inMemoryToken) {
      config.headers['Authorization'] = `Bearer ${inMemoryToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de Respuestas: Manejo automático de token expirado (401)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Si es un 401 y no hemos reintentado esta petición aún
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Intentar refrescar el token de acceso llamando a nuestro endpoint personalizado
        // que leerá el Refresh Token de la cookie HttpOnly
        const refreshResponse = await axios.post(
          'http://localhost:8000/api/usuarios/token/refresh/',
          {},
          { withCredentials: true }
        );

        if (refreshResponse.data && refreshResponse.data.access_token) {
          const newAccessToken = refreshResponse.data.access_token;
          
          // Actualizar en memoria
          setInMemoryToken(newAccessToken);
          
          // Opcional: Actualizar el Zustand store si está inicializado
          // (Lo haremos a través del Hook/Store para mantener React reactivo)
          
          // Reintentar la petición original con el nuevo token
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si el refresco silencioso falla (refresh token expirado/inválido),
        // limpiar estado local y propagar el error para forzar logout
        setInMemoryToken(null);
        
        // Disparar evento personalizado para que Zustand limpie la sesión
        window.dispatchEvent(new Event('auth-expired'));
        
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
