/**
 * Chat - BolãoFácil
 * Módulo para funcionalidades de chat
 */

class ChatModule {
    constructor() {
        this.messages = [];
        this.init();
    }

    /**
     * Inicializa o módulo
     */
    init() {
        this.setupEventListeners();
        this.loadMessages();
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        const form = document.getElementById('message-form');
        if (form) {
            form.addEventListener('submit', (e) => this.sendMessage(e));
        }
    }

    /**
     * Envia uma mensagem
     */
    sendMessage(event) {
        event.preventDefault();
        
        const input = document.getElementById('message-input');
        const message = input.value.trim();

        if (!message) return;

        // TODO: Enviar mensagem via API
        console.log('Enviando mensagem:', message);

        input.value = '';
    }

    /**
     * Carrega mensagens da API
     */
    loadMessages() {
        // TODO: Carregar mensagens do servidor
        console.log('Carregando mensagens...');
    }

    /**
     * Adiciona uma mensagem à tela
     */
    addMessage(message, isOwn = false) {
        const messagesArea = document.getElementById('messages');
        if (!messagesArea) return;

        const messageEl = document.createElement('div');
        messageEl.className = `message ${isOwn ? 'own' : 'other'}`;
        messageEl.textContent = message;

        messagesArea.appendChild(messageEl);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
}

// Inicializar módulo quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new ChatModule();
});
