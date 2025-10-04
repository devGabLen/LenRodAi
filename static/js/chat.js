/**
 * AI Chat Assistant - Módulo de Chat
 * Manejo de mensajes y conversaciones
 */

class Chat {
    constructor() {
        this.messageHistory = [];
        this.currentSession = null;
        this.isTyping = false;
    }
    
    /**
     * Enviar mensaje al asistente
     */
    async sendMessage(message, sessionId = null) {
        try {
            
            if (!message || message.trim().length === 0) {
                throw new Error('El mensaje no puede estar vacío');
            }
            
            if (message.length > 2000) {
                throw new Error('El mensaje es demasiado largo (máximo 2000 caracteres)');
            }
            
            
            const userMessage = {
                id: this.generateId(),
                type: 'user',
                content: message.trim(),
                timestamp: new Date().toISOString(),
                sessionId: sessionId || this.currentSession
            };
            
            
            this.messageHistory.push(userMessage);
            
            
            this.displayMessage(userMessage);
            
            
            const response = await this.sendToServer(userMessage);
            
            return response;
            
        } catch (error) {
            console.error('Error enviando mensaje:', error);
            this.showError('Error enviando mensaje: ' + error.message);
            throw error;
        }
    }
    
    /**
     * Enviar mensaje al servidor
     */
    async sendToServer(message) {
        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message.content,
                    session_id: message.sessionId,
                    context: this.getContext()
                })
            });
            
            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }
            
            const data = await response.json();
            
            
            const aiMessage = {
                id: this.generateId(),
                type: 'assistant',
                content: data.response,
                timestamp: data.timestamp,
                confidence: data.confidence,
                context: data.context,
                modelInfo: data.model_info,
                sessionId: data.session_id
            };
            
            
            this.messageHistory.push(aiMessage);
            
            
            this.displayMessage(aiMessage);
            
            return aiMessage;
            
        } catch (error) {
            console.error('Error comunicándose con el servidor:', error);
            throw error;
        }
    }
    
    /**
     * Mostrar mensaje en la interfaz
     */
    displayMessage(message) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        
        const messageElement = this.createMessageElement(message);
        
        
        messagesContainer.appendChild(messageElement);
        
        
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
            
            content.appendChild(info);
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
     * Obtener contexto actual
     */
    getContext() {
        return {
            messageCount: this.messageHistory.length,
            lastMessage: this.messageHistory[this.messageHistory.length - 1]?.content,
            sessionDuration: this.getSessionDuration(),
            userPreferences: this.getUserPreferences()
        };
    }
    
    /**
     * Obtener duración de la sesión
     */
    getSessionDuration() {
        if (this.messageHistory.length === 0) return 0;
        
        const firstMessage = this.messageHistory[0];
        const lastMessage = this.messageHistory[this.messageHistory.length - 1];
        
        const start = new Date(firstMessage.timestamp);
        const end = new Date(lastMessage.timestamp);
        
        return Math.round((end - start) / 1000); 
    }
    
    /**
     * Obtener preferencias del usuario
     */
    getUserPreferences() {
        
        return {
            language: 'es',
            responseStyle: 'professional',
            detailLevel: 'medium'
        };
    }
    
    /**
     * Limpiar historial de mensajes
     */
    clearHistory() {
        this.messageHistory = [];
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
    }
    
    /**
     * Cargar historial de mensajes
     */
    async loadHistory(sessionId) {
        try {
            const response = await fetch(`/api/chat/history/${sessionId}`);
            
            if (!response.ok) {
                throw new Error(`Error cargando historial: ${response.status}`);
            }
            
            const data = await response.json();
            
            
            this.clearHistory();
            
            
            data.history.forEach(msg => {
                const userMessage = {
                    id: this.generateId(),
                    type: 'user',
                    content: msg.user_message,
                    timestamp: msg.timestamp
                };
                
                const aiMessage = {
                    id: this.generateId(),
                    type: 'assistant',
                    content: msg.ai_response,
                    timestamp: msg.timestamp,
                    confidence: msg.confidence,
                    context: msg.context
                };
                
                this.messageHistory.push(userMessage, aiMessage);
                this.displayMessage(userMessage);
                this.displayMessage(aiMessage);
            });
            
            this.currentSession = sessionId;
            
        } catch (error) {
            console.error('Error cargando historial:', error);
            this.showError('Error cargando historial de conversación');
        }
    }
    
    /**
     * Exportar conversación
     */
    exportConversation(format = 'json') {
        if (this.messageHistory.length === 0) {
            this.showError('No hay mensajes para exportar');
            return;
        }
        
        const exportData = {
            sessionId: this.currentSession,
            exportedAt: new Date().toISOString(),
            messageCount: this.messageHistory.length,
            messages: this.messageHistory
        };
        
        let content, mimeType, filename;
        
        switch (format) {
            case 'json':
                content = JSON.stringify(exportData, null, 2);
                mimeType = 'application/json';
                filename = `conversacion_${this.currentSession}.json`;
                break;
                
            case 'txt':
                content = this.formatConversationAsText(exportData);
                mimeType = 'text/plain';
                filename = `conversacion_${this.currentSession}.txt`;
                break;
                
            default:
                throw new Error('Formato no soportado');
        }
        
        
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    /**
     * Formatear conversación como texto
     */
    formatConversationAsText(data) {
        let text = `Conversación exportada el ${new Date(data.exportedAt).toLocaleString('es-ES')}\n`;
        text += `Sesión: ${data.sessionId}\n`;
        text += `Total de mensajes: ${data.messageCount}\n\n`;
        text += '='.repeat(50) + '\n\n';
        
        data.messages.forEach(msg => {
            const timestamp = new Date(msg.timestamp).toLocaleString('es-ES');
            const sender = msg.type === 'user' ? 'Usuario' : 'Asistente';
            
            text += `[${timestamp}] ${sender}:\n`;
            text += `${msg.content}\n\n`;
        });
        
        return text;
    }
    
    /**
     * Buscar en el historial
     */
    searchHistory(query) {
        if (!query || query.trim().length === 0) {
            return this.messageHistory;
        }
        
        const searchTerm = query.toLowerCase();
        
        return this.messageHistory.filter(msg => 
            msg.content.toLowerCase().includes(searchTerm)
        );
    }
    
    /**
     * Obtener estadísticas de la conversación
     */
    getConversationStats() {
        const userMessages = this.messageHistory.filter(msg => msg.type === 'user');
        const aiMessages = this.messageHistory.filter(msg => msg.type === 'assistant');
        
        const totalWords = this.messageHistory.reduce((count, msg) => {
            return count + msg.content.split(' ').length;
        }, 0);
        
        const avgConfidence = aiMessages.reduce((sum, msg) => {
            return sum + (msg.confidence || 0);
        }, 0) / (aiMessages.length || 1);
        
        return {
            totalMessages: this.messageHistory.length,
            userMessages: userMessages.length,
            aiMessages: aiMessages.length,
            totalWords: totalWords,
            avgWordsPerMessage: Math.round(totalWords / this.messageHistory.length),
            avgConfidence: Math.round(avgConfidence * 100) / 100,
            sessionDuration: this.getSessionDuration()
        };
    }
    
    /**
     * Scroll al final de los mensajes
     */
    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    /**
     * Mostrar error
     */
    showError(message) {
        
        console.error(message);
        
    }
    
    /**
     * Generar ID único
     */
    generateId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}
