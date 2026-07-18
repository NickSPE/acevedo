import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './store/useAuthStore';
import { Sparkles, Loader2 } from 'lucide-react';

// Páginas
import Login from './pages/Login';
import Register from './pages/Register';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';
import Transactions from './pages/Transactions';
import SavingsGoals from './pages/SavingsGoals';
import Profile from './pages/Profile';
import Education from './pages/Education';
import Reports from './pages/Reports';
import Notifications from './pages/Notifications';


// Componentes
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';

// Ruta protegida base
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, user, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-200 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        <span className="text-xs font-semibold tracking-wider text-slate-500 uppercase">Cargando FinGest...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Si no ha completado el onboarding y no está en la página de onboarding, forzar redirección
  if (user && !user.onboarding_completed && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
};

// Ruta pública que previene acceso a login/registro si ya está logueado
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-200 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        <span className="text-xs font-semibold tracking-wider text-slate-550 uppercase">Cargando...</span>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Layout base para la sección interna protegida
const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  return (
    <div className="flex min-h-screen bg-[#f8f9ff] text-[#0b1c30] overflow-hidden font-sans antialiased selection:bg-brand-500/20">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Navbar */}
        <Navbar toggleSidebar={toggleSidebar} />

        {/* Dynamic Page Router */}
        <main className="flex-1 overflow-y-auto bg-[#f8f9ff]">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

const AppContent = () => {
  const checkAuth = useAuthStore(state => state.checkAuth);
  const isLoading = useAuthStore(state => state.isLoading);

  useEffect(() => {
    checkAuth();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-250 gap-4">
        <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-xl shadow-brand-500/10">
          <Sparkles className="w-8 h-8 animate-pulse text-white" />
        </div>
        <div className="space-y-1 text-center">
          <h2 className="text-sm font-bold text-white tracking-wide">FinGest Inteligencia Financiera</h2>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-black">Validando Credenciales...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Rutas Públicas */}
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } 
      />
      <Route 
        path="/registro" 
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        } 
      />

      {/* Rutas Protegidas de Onboarding */}
      <Route 
        path="/onboarding" 
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        } 
      />

      {/* Página de Inicio (Pública para todos) */}
      <Route path="/" element={<Landing />} />

      {/* Rutas Protegidas en Main Layout */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <Dashboard />
            </MainLayout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/transacciones" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <Transactions />
            </MainLayout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/metas" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <SavingsGoals />
            </MainLayout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/aprender" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <Education />
            </MainLayout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/reportes" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <Reports />
            </MainLayout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/perfil" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <Profile />
            </MainLayout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/alertas" 
        element={
          <ProtectedRoute>
            <MainLayout>
              <Notifications />
            </MainLayout>
          </ProtectedRoute>
        } 
      />


      {/* Redirección por defecto */}
      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
  );
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
