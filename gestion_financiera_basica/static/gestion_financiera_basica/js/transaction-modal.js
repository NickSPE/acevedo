/**
 * Modal de Nueva Transacción con AJAX
 * Implementa ley de figura-fondo (Gestalt)
 */

class TransactionModal {
  constructor() {
    this.modalId = 'transaction-modal';
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

  static escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[tag] || tag)
    );
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      document.addEventListener('click', (e) => {
        if (e.target.matches('[data-toggle="transaction-modal"]') || 
            e.target.closest('[data-toggle="transaction-modal"]')) {
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
      const container = document.querySelector('.transaction-modal-container');
      if (container) {
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
      }
    }, 10);

    this.attachEventListeners();
  }

  close() {
    const container = document.querySelector('.transaction-modal-container');
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
    overlay.className = 'transaction-modal-overlay';
    overlay.textContent = '';
    overlay.insertAdjacentHTML('beforeend', this.getModalHTML());
    document.body.appendChild(overlay);
    this.modal = overlay;
  }

  getModalHTML() {
    return `
      <div class="transaction-modal-backdrop"></div>
      <div class="transaction-modal-container">
        <div class="transaction-modal-header">
          <h2 class="transaction-modal-title">Nueva Transacción</h2>
          <button type="button" class="transaction-modal-close" data-action="close">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <form class="transaction-form" id="transaction-form-ajax">
          <input type="hidden" name="csrfmiddlewaretoken" value="${this.escapeHTML(this.csrfToken)}">
          
          <div class="transaction-form-alert transaction-form-alert-danger" style="display: none;"></div>
          <div class="transaction-form-alert transaction-form-alert-success" style="display: none;"></div>
          
          <!-- Tipo -->
          <div class="transaction-form-group">
            <label class="transaction-form-label">Tipo de transacción</label>
            <div class="transaction-form-radio-group">
              <label class="transaction-form-radio">
                <input type="radio" name="tipo" value="ingreso" required>
                <div class="transaction-form-radio-card">
                  <div class="transaction-form-icon transaction-form-icon-ingreso">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12"/>
                    </svg>
                  </div>
                  <div>
                    <span class="transaction-form-radio-title">Ingreso</span>
                    <p class="transaction-form-radio-desc">Dinero que entra</p>
                  </div>
                </div>
              </label>
              <label class="transaction-form-radio">
                <input type="radio" name="tipo" value="egreso" required>
                <div class="transaction-form-radio-card">
                  <div class="transaction-form-icon transaction-form-icon-egreso">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6"/>
                    </svg>
                  </div>
                  <div>
                    <span class="transaction-form-radio-title">Gasto</span>
                    <p class="transaction-form-radio-desc">Dinero que sale</p>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Descripción -->
          <div class="transaction-form-group">
            <label class="transaction-form-label">Descripción</label>
            <input type="text" name="nombre" class="transaction-form-input" 
                   placeholder="Ej: Salario, Supermercado, Cine..." required>
          </div>

          <!-- Monto y Cuenta -->
          <div class="transaction-form-row">
            <div class="transaction-form-group">
              <label class="transaction-form-label">Monto</label>
              <div class="transaction-form-input-group">
                <span class="transaction-form-input-prefix">$</span>
                <input type="number" name="monto" class="transaction-form-input transaction-form-input-with-prefix" 
                       placeholder="0.00" step="0.01" min="0" required>
              </div>
            </div>
            <div class="transaction-form-group">
              <label class="transaction-form-label">Cuenta</label>
              <select name="id_cuenta" class="transaction-form-select" required>
                <option value="">Seleccionar</option>
              </select>
            </div>
          </div>

          <!-- Categoría -->
          <div class="transaction-form-group">
            <label class="transaction-form-label">Categoría (opcional)</label>
            <select name="categoria" class="transaction-form-select">
              <option value="">Seleccionar categoría</option>
              <option value="alimentacion">Alimentación</option>
              <option value="transporte">Transporte</option>
              <option value="entretenimiento">Entretenimiento</option>
              <option value="salud">Salud</option>
              <option value="educacion">Educación</option>
              <option value="compras">Compras</option>
              <option value="servicios">Servicios</option>
              <option value="vivienda">Vivienda</option>
              <option value="trabajo">Trabajo</option>
              <option value="otros">Otros</option>
            </select>
          </div>

          <!-- Fecha -->
          <div class="transaction-form-group">
            <label class="transaction-form-label">Fecha</label>
            <input type="date" name="fecha_movimiento" class="transaction-form-input" required>
          </div>

          <!-- Descripción adicional -->
          <div class="transaction-form-group">
            <label class="transaction-form-label">Notas adicionales (opcional)</label>
            <textarea name="descripcion" class="transaction-form-textarea" rows="3" 
                      placeholder="Información adicional sobre esta transacción..."></textarea>
          </div>

          <!-- Botones -->
          <div class="transaction-form-actions">
            <button type="button" class="transaction-btn transaction-btn-cancel" data-action="close">
              Cancelar
            </button>
            <button type="submit" class="transaction-btn transaction-btn-primary">
              <span class="transaction-btn-text">Guardar Transacción</span>
              <span class="transaction-btn-spinner" style="display: none;">
                <svg class="transaction-spinner" viewBox="0 0 24 24">
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
    const backdrop = this.modal.querySelector('.transaction-modal-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', () => this.close());
    }

    // Cerrar con ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal) {
        this.close();
      }
    });

    // Submit form
    const form = this.modal.querySelector('#transaction-form-ajax');
    if (form) {
      form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    // Fecha por defecto (hoy)
    const fechaInput = this.modal.querySelector('input[name="fecha_movimiento"]');
    if (fechaInput && !fechaInput.value) {
      const today = new Date().toISOString().split('T')[0];
      fechaInput.value = today;
    }
  }

  async handleSubmit(e) {
    e.preventDefault();
    
    this.clearErrors();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.transaction-btn-text');
    const btnSpinner = submitBtn.querySelector('.transaction-btn-spinner');
    
    // Mostrar spinner
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-flex';
    
    const formData = new FormData(e.target);
    
    try {
      const response = await fetch(e.target.action || '/gestion_financiera_basica/movimientos/agregar/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      });

      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        
        if (data.success) {
          this.showSuccess(data.message || 'Transacción guardada correctamente');
          setTimeout(() => {
            this.close();
            window.location.reload();
          }, 1500);
        } else {
          this.showError(data.message || 'Error al guardar la transacción');
          if (data.errors) {
            this.showFieldErrors(data.errors);
          }
        }
      } else {
        // Si la respuesta es redirect o HTML (vista normal)
        if (response.redirected || response.ok) {
          this.showSuccess('Transacción guardada correctamente');
          setTimeout(() => {
            window.location.href = this.getSafeRedirectUrl(response.url, '/gestion_financiera_basica/transactions/');
          }, 1500);
        } else {
          const text = await response.text();
          if (text.includes('error') || text.includes('Error')) {
            this.showError('Error al procesar la transacción');
          } else {
            this.showSuccess('Transacción guardada correctamente');
            setTimeout(() => {
              window.location.href = '/gestion_financiera_basica/transactions/';
            }, 1500);
          }
        }
      }
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
    const handlers = {
      'http://': (u) => {
        const parsedUrl = new URL(u);
        return parsedUrl.origin === window.location.origin ? u : fallback;
      },
      'https://': (u) => {
        const parsedUrl = new URL(u);
        return parsedUrl.origin === window.location.origin ? u : fallback;
      },
      '/': (u) => (!u.startsWith('//') ? u : fallback)
    };
    const entry = Object.entries(handlers).find(([prefix]) => url.startsWith(prefix));
    if (!entry) return fallback;
    const handler = entry[1];
    try {
      return handler(url);
    } catch (_e) {
      return fallback;
    }
  }

  showSuccess(message) {
    const alert = this.modal.querySelector('.transaction-form-alert-success');
    if (alert) {
      alert.textContent = message;
      alert.style.display = 'block';
      setTimeout(() => {
        if (alert) alert.style.display = 'none';
      }, 3000);
    }
  }

  showError(message) {
    const alert = this.modal.querySelector('.transaction-form-alert-danger');
    if (alert) {
      alert.textContent = message;
      alert.style.display = 'block';
    }
  }

  showFieldErrors(errors) {
    Object.keys(errors).forEach(field => {
      const input = this.modal.querySelector(`[name="${field}"]`);
      if (input) {
        const group = input.closest('.transaction-form-group');
        if (group) {
          let errorDiv = group.querySelector('.transaction-field-error');
          if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'transaction-field-error';
            group.appendChild(errorDiv);
          }
          errorDiv.textContent = errors[field];
          input.classList.add('transaction-input-error');
        }
      }
    });
  }

  clearErrors() {
    const alerts = this.modal.querySelectorAll('.transaction-form-alert');
    alerts.forEach(alert => { alert.style.display = 'none'; });
    
    const fieldErrors = this.modal.querySelectorAll('.transaction-field-error');
    fieldErrors.forEach(error => { error.remove(); });
    
    const errorInputs = this.modal.querySelectorAll('.transaction-input-error');
    errorInputs.forEach(input => { input.classList.remove('transaction-input-error'); });
  }
}

// Inicializar modal
new TransactionModal();
