/**
 * Toast Notification System
 * Usage: Toast.show('Mensagem', 'success', 20000);
 */
class Toast {
  static duration = 20000; // 20 seconds default

  static show(message, type = 'info', duration = null) {
    const container = this.getContainer();
    const toast = this.createToast(message, type);
    container.appendChild(toast);

    const timeToLive = duration || this.duration;
    setTimeout(() => this.remove(toast), timeToLive);
  }

  static success(message, duration = null) {
    this.show(message, 'success', duration);
  }

  static error(message, duration = null) {
    this.show(message, 'error', duration);
  }

  static warning(message, duration = null) {
    this.show(message, 'warning', duration);
  }

  static info(message, duration = null) {
    this.show(message, 'info', duration);
  }

  static getContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  static createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ',
    };

    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || '•'}</div>
      <div class="toast-message">${this.escapeHtml(message)}</div>
      <button class="toast-close" aria-label="Fechar notificação">×</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
      this.remove(toast);
    });

    return toast;
  }

  static remove(toast) {
    if (toast && toast.parentNode) {
      toast.style.animation = 'slideOut 0.3s ease-in forwards';
      setTimeout(() => toast.parentNode?.removeChild(toast), 300);
    }
  }

  static escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Helper para AJAX com feedback automático
class ApiRequest {
  static async post(url, data = {}, successMessage = null, errorMessage = null) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (!response.ok) {
        const message = errorMessage || result.error || result.message || 'Ops, algo deu errado. Tente novamente.';
        Toast.error(message);
        throw new Error(message);
      }

      if (successMessage || result.message) {
        Toast.success(successMessage || result.message);
      }

      return result;
    } catch (error) {
      if (!(error instanceof Error)) {
        Toast.error(errorMessage || 'Erro ao processar requisição.');
      }
      throw error;
    }
  }

  static async get(url) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        Toast.error('Erro ao carregar dados.');
        throw new Error('Network response was not ok');
      }
      return await response.json();
    } catch (error) {
      Toast.error('Erro ao carregar dados.');
      throw error;
    }
  }
}
