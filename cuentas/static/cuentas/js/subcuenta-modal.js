/**
 * Modal de Nueva Subcuenta con AJAX
 * Implementa ley de figura-fondo (Gestalt)
 */

class SubcuentaModal {
  modalId = 'subcuenta-modal';

  constructor() {
    this.csrfToken = this.getCSRFToken();
    this.modal = null;
    this.init();
  }

  static getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') return value;
    }
    return '';
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      document.addEventListener('click', (e) => {
        if (e.target.matches('[data-toggle="subcuenta-modal"]') || 
            e.target.closest('[data-toggle="subcuenta-modal"]')) {
          e.preventDefault();
          this.open(e);
        }
      });
    });
  }

  open() {
    if (this.modal) {
      this.modal.remove();
    }
    this.createModal();
    document.body.style.overflow = 'hidden';
    
    setTimeout(() => {
      const container = document.querySelector('.subcuenta-modal-container');
      if (container) {
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
      }
    }, 10);

    this.attachEventListeners();
  }

  close() {
    const container = document.querySelector('.subcuenta-modal-container');
    if (container) {
      container.style.opacity = '0';
      container.style.transform = 'translateY(-20px)';
    }
    
    setTimeout(() => {
      if (this.modal) {
        this.modal.remove();
        this.modal = null;
      }
      document.body.style.overflow = '';
    }, 300);
  }

  createModal() {
    const overlay = document.createElement('div');
    overlay.className = 'subcuenta-modal-overlay';
    overlay.textContent = '';
    overlay.insertAdjacentHTML('beforeend', this.getModalHTML());
    document.body.appendChild(overlay);
    this.modal = overlay;
  }

  getModalHTML() {
    return `
      <div class="subcuenta-modal-backdrop"></div>
      <div class="subcuenta-modal-container">
        <div class="subcuenta-modal-header">
          <h2 class="subcuenta-modal-title">Crear Subcuenta</h2>
          <button type="button" class="subcuenta-modal-close" data-action="close">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <form class="subcuenta-form" id="subcuenta-form-ajax">
          <input type="hidden" name="csrfmiddlewaretoken" value="${this.csrfToken}">
          
          <div class="subcuenta-form-alert subcuenta-form-alert-danger" style="display: none;"></div>
          <div class="subcuenta-form-alert subcuenta-form-alert-success" style="display: none;"></div>
          
          <!-- Tipo de subcuenta -->
          <div class="subcuenta-form-group">
            <label class="subcuenta-form-label">¿Qué tipo de subcuenta necesitas?</label>
            <div class="subcuenta-form-type-group">
              <label class="subcuenta-form-type-card subcuenta-type-selected">
                <input type="radio" name="tipo_subcuenta" value="personal" checked required>
                <div class="subcuenta-type-content">
                  <svg class="w-8 h-8 subcuenta-type-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  </svg>
                  <h6 class="subcuenta-type-title">Personal</h6>
                  <p class="subcuenta-type-desc">Usa el dinero de tu cuenta principal</p>
                </div>
              </label>
              <label class="subcuenta-form-type-card">
                <input type="radio" name="tipo_subcuenta" value="business" required>
                <div class="subcuenta-type-content">
                  <svg class="w-8 h-8 subcuenta-type-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                  </svg>
                  <h6 class="subcuenta-type-title">Negocio</h6>
                  <p class="subcuenta-type-desc">Cuenta independiente con su propio saldo</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Nombre -->
          <div class="subcuenta-form-group">
            <label class="subcuenta-form-label">Nombre de la subcuenta</label>
            <input type="text" name="nombre" class="subcuenta-form-input" 
                   placeholder="Ej: Ahorros, Emergencia, Vacaciones..." required>
          </div>

          <!-- Categoría -->
          <div class="subcuenta-form-group">
            <label class="subcuenta-form-label">Categoría</label>
            <select name="tipo" class="subcuenta-form-select" required>
              <option value="">Seleccionar categoría</option>
              <option value="ahorros">Ahorros</option>
              <option value="emergencia">Fondo de Emergencia</option>
              <option value="gastos_fijos">Gastos Fijos</option>
              <option value="gastos_variables">Gastos Variables</option>
              <option value="entretenimiento">Entretenimiento</option>
              <option value="viajes">Viajes</option>
              <option value="educacion">Educación</option>
              <option value="salud">Salud</option>
              <option value="familia">Familia</option>
              <option value="inversion">Inversiones</option>
              <option value="otros">Otros</option>
              <option value="tienda_fisica">Tienda Física</option>
              <option value="tienda_online">Tienda Online</option>
              <option value="servicios_profesionales">Servicios Profesionales</option>
              <option value="freelance">Trabajo Freelance</option>
              <option value="negocio_propio">Negocio Propio</option>
              <option value="ingresos_pasivos">Ingresos Pasivos</option>
              <option value="ventas_productos">Ventas de Productos</option>
              <option value="consultoria">Consultoría</option>
              <option value="alquiler_propiedades">Alquiler de Propiedades</option>
            </select>
          </div>

          <!-- Descripción -->
          <div class="subcuenta-form-group">
            <label class="subcuenta-form-label">Descripción (opcional)</label>
            <textarea name="descripcion" class="subcuenta-form-textarea" rows="3" 
                      placeholder="Describe el propósito de esta subcuenta..."></textarea>
          </div>

          <!-- Info para negocios -->
          <div class="subcuenta-form-info" id="business-info" style="display: none;">
            <svg class="w-5 h-5 text-[#227C91]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
              <p class="font-medium">Subcuenta de negocio independiente</p>
              <ul class="text-sm mt-1 space-y-1">
                <li>• Empezará con $0.00</li>
                <li>• No usará el dinero de tu cuenta personal</li>
                <li>• Podrás agregar dinero después cuando quieras</li>
              </ul>
            </div>
          </div>

          <!-- Botones -->
          <div class="subcuenta-form-actions">
            <button type="button" class="subcuenta-btn subcuenta-btn-cancel" data-action="close">
              Cancelar
            </button>
            <button type="submit" class="subcuenta-btn subcuenta-btn-primary">
              <span class="subcuenta-btn-text">Crear Subcuenta</span>
              <span class="subcuenta-btn-spinner" style="display: none;">
                <svg class="subcuenta-spinner" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </span>
            </button>
          </div>
        </form>
      </div>
    `;
  }

  attachEventListeners() {
    // Cerrar modal
    this.modal.querySelectorAll('[data-action="close"]').forEach(btn => {
      btn.addEventListener('click', () => this.close());
    });

    // Cerrar al hacer clic en backdrop
    const backdrop = this.modal.querySelector('.subcuenta-modal-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', () => this.close());
    }

    // Cerrar con ESC
    const escHandler = (e) => {
      if (e.key === 'Escape' && this.modal) {
        this.close();
        document.removeEventListener('keydown', escHandler);
      }
    };
    document.addEventListener('keydown', escHandler);

    // Cambio de tipo
    const typeInputs = this.modal.querySelectorAll('input[name="tipo_subcuenta"]');
    typeInputs.forEach(input => {
      input.addEventListener('change', (e) => {
        // Actualizar selección visual
        this.modal.querySelectorAll('.subcuenta-form-type-card').forEach(card => {
          card.classList.remove('subcuenta-type-selected');
        });
        const selectedCard = input.closest('.subcuenta-form-type-card');
        if (selectedCard) {
          selectedCard.classList.add('subcuenta-type-selected');
        }

        // Mostrar/ocultar info de negocio
        const businessInfo = this.modal.querySelector('#business-info');
        if (businessInfo) {
          businessInfo.style.display = e.target.value === 'business' ? 'flex' : 'none';
        }
      });
    });

    // Submit form
    const form = this.modal.querySelector('#subcuenta-form-ajax');
    if (form) {
      form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
  }

  async handleSubmit(e) {
    e.preventDefault();
    
    this.clearErrors();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.subcuenta-btn-text');
    const btnSpinner = submitBtn.querySelector('.subcuenta-btn-spinner');
    
    // Mostrar spinner
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-flex';
    
    const formData = new FormData(e.target);
    
    try {
      const response = await fetch('/cuentas/subcuentas/crear/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      });

      const outcomes = {
        successRedirect: () => {
          this.showSuccess('Subcuenta creada correctamente');
          setTimeout(() => {
            window.location.href = this.getSafeRedirectUrl(response.url, '/cuentas/subcuentas/');
          }, 1500);
        },
        successStatic: () => {
          this.showSuccess('Subcuenta creada correctamente');
          setTimeout(() => {
            window.location.href = '/cuentas/subcuentas/';
          }, 1500);
        },
        error: () => {
          this.showError('Error al crear la subcuenta');
        }
      };

      let key;
      if (response.redirected || response.ok) {
        key = 'successRedirect';
      } else {
        const text = await response.text();
        key = /error/i.test(text) ? 'error' : 'successStatic';
      }
      outcomes[key]();
    } catch (error) {
      console.error('Error:', error);
      this.showError('Error de conexión. Intenta nuevamente.');
    } finally {
      submitBtn.disabled = false;
      btnText.style.display = 'inline';
      btnSpinner.style.display = 'none';
    }
  }

  static getSafeRedirectUrl(url, fallback) {
    if (!url) return fallback;
    const handlers = [
      {
        match: u => u.startsWith('http://') || u.startsWith('https://'),
        handle: u => {
          const parsedUrl = new URL(u);
          return parsedUrl.origin === window.location.origin ? u : fallback;
        }
      },
      {
        match: u => u.startsWith('/') && !u.startsWith('//'),
        handle: u => u
      }
    ];
    try {
      for (const { match, handle } of handlers) {
        if (match(url)) {
          return handle(url);
        }
      }
    } catch {
      return fallback;
    }
    return fallback;
  }

  showSuccess(message) {
    const alert = this.modal.querySelector('.subcuenta-form-alert-success');
    if (alert) {
      alert.textContent = message;
      alert.style.display = 'block';
    }
  }

  showError(message) {
    const alert = this.modal.querySelector('.subcuenta-form-alert-danger');
    if (alert) {
      alert.textContent = message;
      alert.style.display = 'block';
    }
  }

  clearErrors() {
    const alerts = this.modal.querySelectorAll('.subcuenta-form-alert');
    alerts.forEach(alert => { alert.style.display = 'none'; });
  }
}

// Inicializar modal
new SubcuentaModal();
