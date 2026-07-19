function setHTML(element, html) {
  element.textContent = '';
  const range = document.createRange();
  range.selectNodeContents(element);
  const fragment = range.createContextualFragment(html);
  element.appendChild(fragment);
}

class EditSubcuentaModal {
  constructor() {
    this.csrfToken = this.getCSRFToken();
    this.modal = null;
    this.currentSubcuentaId = null;
    this.init();
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

  static getCSRFToken() {
    const name = 'csrftoken';
    if (document.cookie && document.cookie !== '') {
      const cookie = document.cookie
        .split(';')
        .map(c => c.trim())
        .find(c => c.startsWith(name + '='));
      if (cookie) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }

  init() {
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('[data-toggle="edit-subcuenta-modal"]');
      if (trigger) {
        e.preventDefault();
        const subcuentaId = trigger.dataset.subcuentaId;
        const subcuentaNombre = trigger.dataset.subcuentaNombre;
        const subcuentaTipo = trigger.dataset.subcuentaTipo;
        const subcuentaDescripcion = trigger.dataset.subcuentaDescripcion || '';
        const subcuentaSaldo = trigger.dataset.subcuentaSaldo || '0';
        const tipoSubcuenta = trigger.dataset.tipoSubcuenta || ''; // personal o negocio
        
        this.open(subcuentaId, subcuentaNombre, subcuentaTipo, subcuentaDescripcion, subcuentaSaldo, tipoSubcuenta);
      }
    });
  }

  open(subcuentaId, nombre, tipo, descripcion, saldo, tipoSubcuenta) {
    this.currentSubcuentaId = subcuentaId;
    this.createModal(nombre, tipo, descripcion, saldo, tipoSubcuenta);
    
    setTimeout(() => {
      this.modal.querySelector('.edit-subcuenta-modal-container').style.opacity = '1';
      this.modal.querySelector('.edit-subcuenta-modal-container').style.transform = 'translateY(0)';
    }, 10);
  }

  createModal(nombre, tipo, descripcion, saldo, tipoSubcuenta) {
    const overlay = document.createElement('div');
    overlay.className = 'edit-subcuenta-modal-overlay';
    
    // Escapar inputs para prevenir XSS
    const escapedNombre = this.escapeHTML(nombre);
    const escapedSaldo = this.escapeHTML(saldo);
    const escapedDescripcion = this.escapeHTML(descripcion);
    
    // Icon based on tipo de subcuenta
    const iconPath = tipoSubcuenta === 'personal' 
      ? 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
      : 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z';
    
    const tipoLabel = tipoSubcuenta === 'personal' ? 'Personal' : 'Negocio';
    
    const categories = [
      { value: 'ahorros', display: 'Ahorros' },
      { value: 'emergencia', display: 'Fondo de Emergencia' },
      { value: 'gastos_fijos', display: 'Gastos Fijos' },
      { value: 'gastos_variables', display: 'Gastos Variables' },
      { value: 'entretenimiento', display: 'Entretenimiento' },
      { value: 'viajes', display: 'Viajes' },
      { value: 'educacion', display: 'Educación' },
      { value: 'salud', display: 'Salud' },
      { value: 'familia', display: 'Familia' },
      { value: 'inversion', display: 'Inversiones' },
      { value: 'otros', display: 'Otros' },
      { value: 'tienda_fisica', display: 'Tienda Física' },
      { value: 'tienda_online', display: 'Tienda Online' },
      { value: 'servicios_profesionales', display: 'Servicios Profesionales' },
      { value: 'freelance', display: 'Trabajo Freelance' },
      { value: 'negocio_propio', display: 'Negocio Propio' },
      { value: 'ingresos_pasivos', display: 'Ingresos Pasivos' },
      { value: 'ventas_productos', display: 'Ventas de Productos' },
      { value: 'consultoria', display: 'Consultoría' },
      { value: 'alquiler_propiedades', display: 'Alquiler de Propiedades' }
    ];
    
    const optionsHTML = categories.map(cat => 
      `<option value="${cat.value}" ${tipo === cat.value ? 'selected' : ''}>${cat.display}</option>`
    ).join('\n');

    const modalHTML = `
      <div class="edit-subcuenta-modal-backdrop"></div>
      <div class="edit-subcuenta-modal-container">
        <div class="edit-subcuenta-modal-header">
          <div class="flex items-center gap-3 flex-1">
            <div class="w-9 h-9 bg-[#227C91] bg-opacity-10 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-[#227C91]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </div>
            <div>
              <h2 class="text-xl font-bold text-[#605952]">Editar Subcuenta</h2>
              <p class="text-[#736B5E] text-sm">Actualiza la información de tu subcuenta</p>
            </div>
          </div>
          <button type="button" class="edit-subcuenta-modal-close" aria-label="Cerrar">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
 
        <!-- Info de la subcuenta -->
        <div class="bg-[#F1F0EE] rounded-lg p-4 mb-4 flex items-center gap-3">
          <div class="w-12 h-12 bg-[#227C91] rounded-lg flex items-center justify-center flex-shrink-0">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${iconPath}"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="font-semibold text-[#605952] truncate">${escapedNombre}</h4>
            <p class="text-sm text-[#736B5E]">Saldo actual: <span class="font-semibold text-[#227C91]">${escapedSaldo}</span></p>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-semibold ${tipoSubcuenta === 'personal' ? 'bg-[#227C91] bg-opacity-10 text-[#227C91]' : 'bg-[#605952] bg-opacity-10 text-[#605952]'}">${tipoLabel}</span>
        </div>
 
        <form id="editSubcuentaForm" class="edit-subcuenta-modal-body">
          <div class="space-y-4">
            <div>
              <label for="edit_nombre" class="block text-sm font-medium text-[#605952] mb-1">
                Nombre de la subcuenta <span class="text-red-500">*</span>
              </label>
              <input 
                type="text" 
                id="edit_nombre" 
                name="nombre" 
                value="${escapedNombre}"
                required
                class="w-full px-4 py-2.5 border border-[#E5E1DD] rounded-lg focus:ring-2 focus:ring-[#227C91] focus:border-transparent outline-none text-[#605952]">
            </div>
 
            <div>
              <label for="edit_tipo" class="block text-sm font-medium text-[#605952] mb-1">
                Categoría <span class="text-red-500">*</span>
              </label>
              <select 
                id="edit_tipo" 
                name="tipo" 
                required
                class="w-full px-4 py-2.5 border border-[#E5E1DD] rounded-lg focus:ring-2 focus:ring-[#227C91] focus:border-transparent outline-none text-[#605952]">
                <option value="">Selecciona una categoría</option>
                ${optionsHTML}
              </select>
            </div>
 
            <div>
              <label for="edit_descripcion" class="block text-sm font-medium text-[#605952] mb-1">
                Descripción (opcional)
              </label>
              <textarea 
                id="edit_descripcion" 
                name="descripcion" 
                rows="3"
                class="w-full px-4 py-2.5 border border-[#E5E1DD] rounded-lg focus:ring-2 focus:ring-[#227C91] focus:border-transparent outline-none text-[#605952] resize-none">${escapedDescripcion}</textarea>
            </div>
          </div>
 
          <div class="edit-subcuenta-modal-footer">
            <button type="button" class="edit-subcuenta-modal-btn-secondary">
              Cancelar
            </button>
            <button type="submit" class="edit-subcuenta-modal-btn-primary">
              <span class="edit-subcuenta-modal-btn-text">Guardar Cambios</span>
              <span class="edit-subcuenta-modal-spinner" style="display: none;">
                <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </span>
            </button>
          </div>
        </form>
      </div>
    `;

    setHTML(overlay, modalHTML);
    document.body.appendChild(overlay);
    this.modal = overlay;

    // Event listeners
    this.modal.querySelector('.edit-subcuenta-modal-close').addEventListener('click', () => this.close());
    this.modal.querySelector('.edit-subcuenta-modal-btn-secondary').addEventListener('click', () => this.close());
    this.modal.querySelector('.edit-subcuenta-modal-backdrop').addEventListener('click', () => this.close());
    this.modal.querySelector('#editSubcuentaForm').addEventListener('submit', (e) => this.handleSubmit(e));

    // ESC key
    this.escHandler = (e) => {
      if (e.key === 'Escape') this.close();
    };
    document.addEventListener('keydown', this.escHandler);
  }

  async handleSubmit(e) {
    e.preventDefault();
    
    const submitBtn = this.modal.querySelector('.edit-subcuenta-modal-btn-primary');
    const btnText = submitBtn.querySelector('.edit-subcuenta-modal-btn-text');
    const spinner = submitBtn.querySelector('.edit-subcuenta-modal-spinner');
    
    // Show spinner
    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    submitBtn.disabled = true;

    const formData = new FormData(e.target);
    
    try {
      const response = await fetch(`/cuentas/subcuentas/editar/${this.currentSubcuentaId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      });

      const contentType = response.headers.get('content-type') || '';
      const handlers = {
        'application/json': async (res) => res.json(),
        'text/html': async (res) => res.text(),
        'text/plain': async (res) => res.text()
      };
      const handlerKey = Object.keys(handlers).find(key => contentType.includes(key));
      const result = handlerKey ? await handlers[handlerKey](response) : null;

      if (response.ok && handlerKey) {
        return result;
      }
      return result;
    } catch (error) {
      throw error;
    } finally {
      spinner.style.display = 'none';
      btnText.style.display = '';
      submitBtn.disabled = false;
    }
  }
        
        if (contentType?.includes('application/json')) {
          const data = await response.json();
          if (data.success) {
            this.showSuccess();
          } else {
            throw new Error(data.message || 'Error al actualizar la subcuenta');
          }
        } else {
          // Si es una redirección HTML (éxito)
          this.showSuccess();
        }
      } else {
        throw new Error('Error al actualizar la subcuenta');
      }
    } catch (error) {
      console.error('Error:', error);
      this.showError(error.message);
      
      // Reset button
      btnText.style.display = 'inline-block';
      spinner.style.display = 'none';
      submitBtn.disabled = false;
    }
  }

  showSuccess() {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] flex items-center gap-2';
    const successHTML = `
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
      </svg>
      <span>Subcuenta actualizada exitosamente</span>
    `;
    setHTML(alertDiv, successHTML);
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
      alertDiv.remove();
      this.close();
      window.location.reload();
    }, 1500);
  }

  showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] flex items-center gap-2';
    const escapedMessage = this.escapeHTML(message);
    const errorHTML = `
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
      </svg>
      <span>${escapedMessage}</span>
    `;
    setHTML(alertDiv, errorHTML);
    document.body.appendChild(alertDiv);
    
    setTimeout(() => alertDiv.remove(), 3000);
  }

  close() {
    if (!this.modal) return;
    
    const container = this.modal.querySelector('.edit-subcuenta-modal-container');
    container.style.opacity = '0';
    container.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
      if (this.modal) {
        this.modal.remove();
      }
      this.modal = null;
      document.removeEventListener('keydown', this.escHandler);
    }, 300);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  new EditSubcuentaModal();
});
