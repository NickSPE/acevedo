/**
 * Transfer Modal - Ley de Figura Fondo
 * Maneja modales AJAX de transferencia entre subcuentas
 * Implementación Senior: sin dependencies externas, vanilla JS
 */

class TransferModal {
    constructor(options = {}) {
        this.modalId = options.modalId || 'transferModal';
        this.formId = options.formId || 'transferForm';
        this.apiUrl = options.apiUrl || '/cuentas/subcuentas/transferir-ajax/';
        this.csrfToken = this.getCsrfToken();
        this.isOpen = false;
        
        this.init();
    }

    /**
     * Extrae token CSRF de cookies
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === name + '=') {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Inicializa event listeners
     */
    init() {
        // Click en botones de abrir modal
        document.querySelectorAll('[data-toggle="transfer-modal"]').forEach(btn => {
            btn.addEventListener('click', (e) => this.open(e));
        });

        // Click en overlay o cerrar
        document.addEventListener('click', (e) => {
            if (e.target.id === this.modalId) {
                this.close();
            }
            if (e.target.closest('[data-dismiss="modal"]')) {
                this.close();
            }
        });

        // Tecla ESC para cerrar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Submit del formulario
        const form = document.getElementById(this.formId);
        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }

    /**
     * Abre el modal con efecto figura-fondo
     */
    open(event) {
        event.preventDefault();
        
        let modal = document.getElementById(this.modalId);
        
        if (!modal) {
            modal = this.createModal();
            document.body.appendChild(modal);
        }

        // Agregar clase para mostrar (CSS transition)
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        this.isOpen = true;
        
        // Trigger reflow para activar animación
        void modal.offsetHeight;
        
        // Focus en el formulario
        const form = document.getElementById(this.formId);
        if (form) {
            const firstInput = form.querySelector('input, select, textarea');
            if (firstInput) firstInput.focus();
        }
    }

    /**
     * Cierra el modal con efecto transición
     */
    close() {
        const modal = document.getElementById(this.modalId);
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => {
                document.body.style.overflow = '';
            }, 300);
        }
        this.isOpen = false;
    }

    /**
     * Crea la estructura HTML del modal
     */
    createModal() {
        const modal = document.createElement('div');
        modal.id = this.modalId;
        modal.className = 'transfer-modal-overlay';
        const cleanHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(this.getModalHTML()) : this.getModalHTML();
        modal.innerHTML = cleanHTML;
        return modal;
    }

    /**
     * Retorna HTML del modal
     */
    getModalHTML() {
        return `
            <div class="transfer-modal-backdrop"></div>
            <div class="transfer-modal-container">
                <div class="transfer-modal-header">
                    <h2 class="transfer-modal-title">
                        <svg class="transfer-modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
                        </svg>
                        Transferir Entre Subcuentas
                    </h2>
                    <button type="button" class="transfer-modal-close" data-dismiss="modal" aria-label="Cerrar">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                
                <div class="transfer-modal-body">
                    <form id="${this.escapeHTML(this.formId)}" class="transfer-form">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${this.escapeHTML(this.csrfToken)}">
                        
                        <!-- Subcuenta Origen -->
                        <div class="transfer-form-group">
                            <label for="id_subcuenta_origen" class="transfer-form-label">
                                Subcuenta Origen
                                <span class="transfer-form-required">*</span>
                            </label>
                            <select id="id_subcuenta_origen" name="subcuenta_origen" class="transfer-form-select" required>
                                <option value="">Selecciona una subcuenta...</option>
                            </select>
                            <span class="transfer-form-help" id="help-origen"></span>
                            <span class="transfer-form-error" id="error-subcuenta_origen"></span>
                        </div>

                        <!-- Flecha visual -->
                        <div class="transfer-form-arrow">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
                            </svg>
                        </div>

                        <!-- Subcuenta Destino -->
                        <div class="transfer-form-group">
                            <label for="id_subcuenta_destino" class="transfer-form-label">
                                Subcuenta Destino
                                <span class="transfer-form-required">*</span>
                            </label>
                            <select id="id_subcuenta_destino" name="subcuenta_destino" class="transfer-form-select" required>
                                <option value="">Selecciona una subcuenta...</option>
                            </select>
                            <span class="transfer-form-help" id="help-destino"></span>
                            <span class="transfer-form-error" id="error-subcuenta_destino"></span>
                        </div>

                        <!-- Monto -->
                        <div class="transfer-form-group">
                            <label for="id_monto" class="transfer-form-label">
                                Monto a Transferir
                                <span class="transfer-form-required">*</span>
                            </label>
                            <input 
                                type="number" 
                                id="id_monto" 
                                name="monto" 
                                class="transfer-form-input" 
                                placeholder="0.00"
                                step="0.01"
                                min="0.01"
                                required
                            >
                            <span class="transfer-form-error" id="error-monto"></span>
                        </div>

                        <!-- Descripción -->
                        <div class="transfer-form-group">
                            <label for="id_descripcion" class="transfer-form-label">
                                Concepto (Opcional)
                            </label>
                            <textarea 
                                id="id_descripcion" 
                                name="descripcion" 
                                class="transfer-form-textarea"
                                rows="2"
                                placeholder="Motivo de la transferencia..."
                            ></textarea>
                            <span class="transfer-form-error" id="error-descripcion"></span>
                        </div>

                        <!-- Mensaje de error general -->
                        <div id="transfer-form-alert" class="transfer-form-alert" style="display: none;"></div>
                        
                        <!-- Botones -->
                        <div class="transfer-modal-footer">
                            <button 
                                type="button" 
                                class="transfer-btn transfer-btn-cancel" 
                                data-dismiss="modal"
                            >
                                Cancelar
                            </button>
                            <button 
                                type="submit" 
                                class="transfer-btn transfer-btn-primary"
                                id="transfer-submit-btn"
                            >
                                <span class="transfer-btn-text">Transferir Fondos</span>
                                <span class="transfer-btn-spinner" style="display: none;">
                                    <span class="spinner"></span>
                                </span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }

    /**
     * Maneja el submit del formulario
     */
    handleSubmit(e) {
        e.preventDefault();
        
        const form = document.getElementById(this.formId);
        const submitBtn = document.getElementById('transfer-submit-btn');
        const btnText = submitBtn.querySelector('.transfer-btn-text');
        const spinner = submitBtn.querySelector('.transfer-btn-spinner');
        
        // Deshabilitar botón
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'inline-block';
        
        // Limpiar errores previos
        this.clearErrors();
        
        const formData = new FormData(form);
        
        fetch(this.apiUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSuccess(data.message);
                
                // Reset del formulario
                form.reset();
                
                // Cerrar modal después de 1.5s
                setTimeout(() => {
                    this.close();
                    // Disparar evento para actualizar la página si es necesario
                    window.dispatchEvent(new CustomEvent('transferComplete', {
                        detail: {
                            origen: data.origen,
                            destino: data.destino
                        }
                    }));
                }, 1500);
            } else {
                if (data.errors) {
                    this.showFieldErrors(data.errors);
                } else {
                    this.showError(data.error || 'Error al procesar la transferencia');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showError('Error de conexión. Intenta nuevamente.');
        })
        .finally(() => {
            // Restaurar botón
            submitBtn.disabled = false;
            btnText.style.display = 'inline';
            spinner.style.display = 'none';
        });
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHTML(str) {
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

    /**
     * Muestra mensaje de éxito
     */
    showSuccess(message) {
        const alert = document.getElementById('transfer-form-alert');
        alert.className = 'transfer-form-alert transfer-form-alert-success';
        const escapedMessage = this.escapeHTML(message);
        const successHTML = `
            <div class="transfer-alert-content">
                <svg class="transfer-alert-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <span>${escapedMessage}</span>
            </div>
        `;
        alert.innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(successHTML) : successHTML;
        alert.style.display = 'block';
    }

    /**
     * Muestra mensaje de error general
     */
    showError(message) {
        const alert = document.getElementById('transfer-form-alert');
        alert.className = 'transfer-form-alert transfer-form-alert-danger';
        const escapedMessage = this.escapeHTML(message);
        const errorHTML = `
            <div class="transfer-alert-content">
                <svg class="transfer-alert-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                </svg>
                <span>${escapedMessage}</span>
            </div>
        `;
        alert.innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(errorHTML) : errorHTML;
        alert.style.display = 'block';
    }

    /**
     * Muestra errores de campos específicos
     */
    showFieldErrors(errors) {
        for (const [field, message] of Object.entries(errors)) {
            const errorElement = document.getElementById(`error-${field}`);
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.style.display = 'block';
            }
        }
    }

    /**
     * Limpia mensajes de error
     */
    clearErrors() {
        document.querySelectorAll('.transfer-form-error').forEach(el => {
            el.textContent = '';
            el.style.display = 'none';
        });
        
        const alert = document.getElementById('transfer-form-alert');
        if (alert) {
            alert.style.display = 'none';
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    if (typeof TransferModal !== 'undefined') {
        window.transferModal = new TransferModal({
            modalId: 'transferModal',
            formId: 'transferForm',
            apiUrl: '/cuentas/subcuentas/transferir-ajax/'
        });
    }
});
