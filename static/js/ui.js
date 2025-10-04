/**
 * AI Chat Assistant - Módulo de Interfaz de Usuario
 * Manejo de la interfaz y interacciones del usuario
 */

class UI {
    constructor() {
        this.currentTheme = 'light';
        this.isSettingsOpen = false;
        this.notifications = [];
        this.animations = {
            duration: 300,
            easing: 'ease-in-out'
        };
    }
    
    /**
     * Mostrar pantalla de bienvenida
     */
    showWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatMessages = document.getElementById('chatMessages');
        
        if (welcomeScreen && chatMessages) {
            welcomeScreen.style.display = 'flex';
            chatMessages.style.display = 'none';
        }
    }
    
    /**
     * Ocultar pantalla de bienvenida
     */
    hideWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatMessages = document.getElementById('chatMessages');
        
        if (welcomeScreen && chatMessages) {
            welcomeScreen.style.display = 'none';
            chatMessages.style.display = 'flex';
        }
    }
    
    /**
     * Limpiar mensajes
     */
    clearMessages() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
    }
    
    /**
     * Agregar mensaje a la interfaz
     */
    addMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        
        this.hideWelcomeScreen();
        
        
        const messageElement = this.createMessageElement(message);
        
        
        chatMessages.appendChild(messageElement);
        
        
        this.scrollToBottom();
        
        
        setTimeout(() => {
            messageElement.classList.add('show');
        }, 10);
    }
    
    /**
     * Crear elemento HTML para el mensaje
     */
    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}`;
        messageDiv.dataset.messageId = message.id;
        
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = message.type === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';
        
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.innerHTML = this.formatMessage(message.content);
        
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-time';
        timestamp.textContent = this.formatTimestamp(message.timestamp);
        
        
        if (message.type === 'assistant') {
            const info = document.createElement('div');
            info.className = 'message-info';
            
            if (message.confidence !== undefined) {
                const confidence = document.createElement('span');
                confidence.className = 'confidence';
                confidence.textContent = `Confianza: ${Math.round(message.confidence * 100)}%`;
                info.appendChild(confidence);
            }
            
            if (message.context) {
                const context = document.createElement('span');
                context.className = 'context-info';
                context.textContent = this.getContextSummary(message.context);
                info.appendChild(context);
            }
            
            
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'btn-icon-small';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Copiar mensaje';
            copyBtn.addEventListener('click', () => this.copyMessage(message.content));
            
            const likeBtn = document.createElement('button');
            likeBtn.className = 'btn-icon-small';
            likeBtn.innerHTML = '<i class="fas fa-thumbs-up"></i>';
            likeBtn.title = 'Me gusta';
            likeBtn.addEventListener('click', () => this.likeMessage(message.id));
            
            actions.appendChild(copyBtn);
            actions.appendChild(likeBtn);
            
            content.appendChild(info);
            content.appendChild(actions);
        }
        
        
        content.appendChild(text);
        content.appendChild(timestamp);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        return messageDiv;
    }
    
    /**
     * Formatear mensaje con markdown básico
     */
    formatMessage(content) {
        
        let formatted = content
            
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            
            .replace(/`(.*?)`/g, '<code>$1</code>')
            
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
            
            .replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    /**
     * Formatear timestamp
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        
        if (diff < 24 * 60 * 60 * 1000 && date.toDateString() === now.toDateString()) {
            return date.toLocaleTimeString('es-ES', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
        
        
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        if (date.toDateString() === yesterday.toDateString()) {
            return 'Ayer ' + date.toLocaleTimeString('es-ES', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
        
        
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    /**
     * Obtener resumen del contexto
     */
    getContextSummary(context) {
        if (!context) return '';
        
        const parts = [];
        
        if (context.intent) {
            parts.push(`Intención: ${context.intent.intent}`);
        }
        
        if (context.emotions && context.emotions.emotions) {
            parts.push(`Emociones: ${context.emotions.emotions.join(', ')}`);
        }
        
        if (context.language) {
            parts.push(`Idioma: ${context.language.language}`);
        }
        
        return parts.join(' • ');
    }
    
    /**
     * Mostrar indicador de escritura
     */
    showTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.classList.add('show');
        }
    }
    
    /**
     * Ocultar indicador de escritura
     */
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.classList.remove('show');
        }
    }
    
    /**
     * Scroll al final de los mensajes
     */
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    /**
     * Mostrar modal de configuración
     */
    showSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.add('show');
            this.isSettingsOpen = true;
            document.body.style.overflow = 'hidden';
        }
    }
    
    /**
     * Ocultar modal de configuración
     */
    hideSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.remove('show');
            this.isSettingsOpen = false;
            document.body.style.overflow = '';
        }
    }
    
    /**
     * Aplicar tema
     */
    applyTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        
        
        const themeBtn = document.getElementById('themeBtn');
        if (themeBtn) {
            themeBtn.innerHTML = theme === 'light' 
                ? '<i class="fas fa-moon"></i>' 
                : '<i class="fas fa-sun"></i>';
        }
    }
    
    /**
     * Aplicar tamaño de fuente
     */
    applyFontSize(size) {
        const sizes = {
            small: '14px',
            medium: '16px',
            large: '18px'
        };
        
        document.documentElement.style.fontSize = sizes[size] || sizes.medium;
    }
    
    /**
     * Actualizar lista de conversaciones
     */
    updateConversationList(conversations) {
        const conversationList = document.getElementById('conversationList');
        if (!conversationList) return;
        
        conversationList.innerHTML = '';
        
        if (conversations.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <div class="empty-icon">
                    <i class="fas fa-comments"></i>
                </div>
                <p>No hay conversaciones</p>
                <small>Inicia una nueva conversación para comenzar</small>
            `;
            conversationList.appendChild(emptyState);
            return;
        }
        
        conversations.forEach(conversation => {
            const conversationElement = this.createConversationElement(conversation);
            conversationList.appendChild(conversationElement);
        });
    }
    
    /**
     * Crear elemento de conversación
     */
    createConversationElement(conversation) {
        const element = document.createElement('div');
        element.className = 'conversation-item';
        element.dataset.conversationId = conversation.id;
        
        element.innerHTML = `
            <div class="conversation-title">${this.escapeHtml(conversation.title)}</div>
            <div class="conversation-preview">${this.escapeHtml(conversation.preview)}</div>
            <div class="conversation-time">${this.formatTimestamp(conversation.timestamp)}</div>
        `;
        
        element.addEventListener('click', () => {
            this.loadConversation(conversation.id);
        });
        
        return element;
    }
    
    /**
     * Cargar conversación
     */
    async loadConversation(conversationId) {
        try {
            
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const activeItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
            if (activeItem) {
                activeItem.classList.add('active');
            }
            
            
            this.showLoading('Cargando conversación...');
            
            
            setTimeout(() => {
                this.hideLoading();
                this.hideWelcomeScreen();
            }, 1000);
            
        } catch (error) {
            console.error('Error cargando conversación:', error);
            this.showError('Error cargando conversación');
        }
    }
    
    /**
     * Actualizar estado de conexión
     */
    updateConnectionStatus(isConnected) {
        const statusIndicator = document.querySelector('.user-status');
        if (statusIndicator) {
            statusIndicator.textContent = isConnected ? 'En línea' : 'Desconectado';
            statusIndicator.className = `user-status ${isConnected ? 'online' : 'offline'}`;
        }
    }
    
    /**
     * Mostrar loading
     */
    showLoading(message = 'Cargando...') {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const loadingText = loadingOverlay?.querySelector('p');
        
        if (loadingOverlay) {
            if (loadingText) {
                loadingText.textContent = message;
            }
            loadingOverlay.classList.add('show');
        }
    }
    
    /**
     * Ocultar loading
     */
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('show');
        }
    }
    
    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            duration
        };
        
        this.notifications.push(notification);
        this.renderNotification(notification);
        
        
        setTimeout(() => {
            this.removeNotification(notification.id);
        }, duration);
    }
    
    /**
     * Renderizar notificación
     */
    renderNotification(notification) {
        const container = this.getNotificationContainer();
        
        const element = document.createElement('div');
        element.className = `notification notification-${notification.type}`;
        element.dataset.notificationId = notification.id;
        
        element.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-message">${this.escapeHtml(notification.message)}</div>
                <button class="notification-close" onclick="window.chatApp.ui.removeNotification(${notification.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(element);
        
        
        setTimeout(() => {
            element.classList.add('show');
        }, 10);
    }
    
    /**
     * Obtener contenedor de notificaciones
     */
    getNotificationContainer() {
        let container = document.getElementById('notificationContainer');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        return container;
    }
    
    /**
     * Obtener icono de notificación
     */
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        return icons[type] || 'info-circle';
    }
    
    /**
     * Remover notificación
     */
    removeNotification(id) {
        const element = document.querySelector(`[data-notification-id="${id}"]`);
        if (element) {
            element.classList.remove('show');
            setTimeout(() => {
                element.remove();
            }, this.animations.duration);
        }
        
        this.notifications = this.notifications.filter(n => n.id !== id);
    }
    
    /**
     * Mostrar error
     */
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    /**
     * Mostrar éxito
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    /**
     * Mostrar información
     */
    showInfo(message) {
        this.showNotification(message, 'info');
    }
    
    /**
     * Mostrar advertencia
     */
    showWarning(message) {
        this.showNotification(message, 'warning');
    }
    
    /**
     * Copiar mensaje al portapapeles
     */
    async copyMessage(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showSuccess('Mensaje copiado al portapapeles');
        } catch (error) {
            console.error('Error copiando mensaje:', error);
            this.showError('Error copiando mensaje');
        }
    }
    
    /**
     * Dar like a un mensaje
     */
    likeMessage(messageId) {
        
        this.showSuccess('¡Gracias por tu feedback!');
    }
    
    /**
     * Escapar HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Confirmar acción
     */
    confirm(message, callback) {
        if (confirm(message)) {
            callback();
        }
    }
    
    /**
     * Mostrar modal personalizado
     */
    showModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.id = 'customModal';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${this.escapeHtml(title)}</h3>
                    <button class="btn-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${buttons.map(btn => `
                        <button class="btn-${btn.type || 'secondary'}" onclick="${btn.onclick || 'this.closest(\'.modal\').remove()'}">
                            ${this.escapeHtml(btn.text)}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Ocultar modal personalizado
     */
    hideModal() {
        const modal = document.getElementById('customModal');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
        }
    }
}
