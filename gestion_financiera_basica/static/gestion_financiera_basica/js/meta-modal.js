/**
 * Modal de Nueva Meta con AJAX
 * Implementa ley de figura-fondo (Gestalt)
 */

class MetaModal {
  constructor(options = {}) {
    this.modalId = 'meta-modal';
    this.csrfToken = this.getCSRFToken();
    this.modal = null;
    this.init();
  }

  getCSRFToken() {
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
        if (e.target.matches('[data-toggle="meta-modal"]') || 
            e.target.closest('[data-toggle="meta-modal"]')) {
          e.preventDefault();
          this.open(e);
        }
      });
    });
  }

  open(event) {
    if (this.modal) {
      this.modal.remove();
    }
    this.createModal();
    document.body.style.overflow = 'hidden';
    
    setTimeout(() => {
      const container = document.querySelector('.meta-modal-container');
      if (container) {
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
      }
    }, 10);

    this.attachEventListeners();
  }

  close() {
    const container = document.querySelector('.meta-modal-container');
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
    overlay.className = 'meta-modal-overlay';
    overlay.innerHTML = this.getModalHTML();
    document.body.appendChild(overlay);
    this.modal = overlay;
  }

  getModalHTML() {
    return `
      <div class="meta-modal-backdrop"></div>
      <div class="meta-modal-container">
        <div class="meta-modal-header">
          <h2 class="meta-modal-title">Nueva Meta de Ahorro</h2>
          <button type="button" class="meta-modal-close" data-action="close">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <form class="meta-form" id="meta-form-ajax">
          <input type="hidden" name="csrfmiddlewaretoken" value="${this.csrfToken}">
          
          <div class="meta-form-alert meta-form-alert-danger" style="display: none;"></div>
          <div class="meta-form-alert meta-form-alert-success" style="display: none;"></div>
          
          <!-- Nombre -->
          <div class="meta-form-group">
            <label class="meta-form-label">Nombre de la meta</label>
            <input type="text" name="nombre" class="meta-form-input" 
                   placeholder="Ej: Vacaciones, Auto nuevo, Fondo emergencia..." required>
          </div>

          <!-- Descripción -->
          <div class="meta-form-group">
            <label class="meta-form-label">Descripción (opcional)</label>
            <textarea name="descripcion" class="meta-form-textarea" rows="2" 
                      placeholder="Describe tu meta de ahorro..."></textarea>
          </div>

          <!-- Monto objetivo y Cuenta -->
          <div class="meta-form-row">
            <div class="meta-form-group">
              <label class="meta-form-label">Monto objetivo</label>
              <div class="meta-form-input-group">
                <span class="meta-form-input-prefix">$</span>
                <input type="number" name="monto_objetivo" class="meta-form-input meta-form-input-with-prefix" 
                       placeholder="0.00" step="0.01" min="0.01" required>
              </div>
            </div>
            <div class="meta-form-group">
              <label class="meta-form-label">Cuenta</label>
              <select name="id_cuenta" class="meta-form-select" required>
                <option value="">Seleccionar</option>
              </select>
            </div>
          </div>

          <!-- Fechas -->
          <div class="meta-form-row">
            <div class="meta-form-group">
              <label class="meta-form-label">Fecha de inicio</label>
              <input type="date" name="fecha_inicio" class="meta-form-input" required>
            </div>
            <div class="meta-form-group">
              <label class="meta-form-label">Fecha límite</label>
              <input type="date" name="fecha_limite" class="meta-form-input" required>
            </div>
          </div>

          <!-- Frecuencia de aporte -->
          <div class="meta-form-group">
            <label class="meta-form-label">Frecuencia de aportes</label>
            <select name="frecuencia_aporte" class="meta-form-select" required>
              <option value="diaria">Diaria</option>
              <option value="semanal">Semanal</option>
              <option value="quincenal">Quincenal</option>
              <option value="mensual" selected>Mensual</option>
              <option value="bimestral">Bimestral</option>
              <option value="trimestral">Trimestral</option>
              <option value="semestral">Semestral</option>
              <option value="anual">Anual</option>
            </select>
          </div>

          <!-- Botones -->
          <div class="meta-form-actions">
            <button type="button" class="meta-btn meta-btn-cancel" data-action="close">
              Cancelar
            </button>
            <button type="submit" class="meta-btn meta-btn-primary">
              <span class="meta-btn-text">Crear Meta</span>
              <span class="meta-btn-spinner" style="display: none;">
                <svg class="meta-spinner" viewBox="0 0 24 24">
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
    const backdrop = this.modal.querySelector('.meta-modal-backdrop');
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

    // Submit form
    const form = this.modal.querySelector('#meta-form-ajax');
    if (form) {
      form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    // Fecha mínima (hoy) para fecha_inicio
    const fechaInicioInput = this.modal.querySelector('input[name="fecha_inicio"]');
    if (fechaInicioInput) {
      const today = new Date();
      fechaInicioInput.value = today.toISOString().split('T')[0];
      fechaInicioInput.min = today.toISOString().split('T')[0];
    }

    // Fecha mínima (mañana) para fecha_limite
    const fechaLimiteInput = this.modal.querySelector('input[name="fecha_limite"]');
    if (fechaLimiteInput) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      fechaLimiteInput.min = tomorrow.toISOString().split('T')[0];
    }
  }

  async handleSubmit(e) {
    e.preventDefault();
    
    this.clearErrors();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.meta-btn-text');
    const btnSpinner = submitBtn.querySelector('.meta-btn-spinner');
    
    // Mostrar spinner
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-flex';
    
    const formData = new FormData(e.target);
    
    try {
      const response = await fetch('/gestion_financiera_basica/metas/agregar/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      });

      if (response.redirected || response.ok) {
        this.showSuccess('Meta de ahorro creada correctamente');
        setTimeout(() => {
          window.location.href = response.url || '/gestion_financiera_basica/savings-goals/';
        }, 1500);
      } else {
        const text = await response.text();
        if (text.includes('error') || text.includes('Error')) {
          this.showError('Error al crear la meta de ahorro');
        } else {
          this.showSuccess('Meta de ahorro creada correctamente');
          setTimeout(() => {
            window.location.href = '/gestion_financiera_basica/savings-goals/';
          }, 1500);
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

  showSuccess(message) {
    const alert = this.modal.querySelector('.meta-form-alert-success');
    if (alert) {
      alert.textContent = message;
      alert.style.display = 'block';
    }
  }

  showError(message) {
    const alert = this.modal.querySelector('.meta-form-alert-danger');
    if (alert) {
      alert.textContent = message;
      alert.style.display = 'block';
    }
  }

  clearErrors() {
    const alerts = this.modal.querySelectorAll('.meta-form-alert');
    alerts.forEach(alert => alert.style.display = 'none');
  }
}

// Inicializar modal
new MetaModal();
