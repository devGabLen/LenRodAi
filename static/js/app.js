class ChatApp {
    constructor() {
        this.state = {
            currentSessionId: null,
            isConnected: false,
            isTyping: false,
            messages: [],
            conversations: [],
            settings: {
                theme: 'light',
                personality: 'professional',
                responseLength: 'medium',
                fontSize: 'medium'
            },
            user: {
                name: 'Usuario',
                status: 'online'
            }
        };
        
        this.websocket = null;
        this.ui = new UI();
        this.chat = new Chat();
        this.websocketManager = new WebSocketManager();
        
        this.init();
    }
    
    async init() {
        console.log('Inicializando AI Chat Assistant...');
        
        this.ui.showLoading('Inicializando asistente...');
        
        try {
            await this.loadSettings();
            
            this.ui.applyTheme(this.state.settings.theme);
            
            await this.websocketManager.connect();
            await this.loadConversations();
            
            this.setupEventListeners();
            
            this.ui.hideLoading();
            
            console.log('Aplicación inicializada correctamente');
            
        } catch (error) {
            console.error('Error inicializando aplicación:', error);
            this.ui.showError('Error inicializando la aplicación. Por favor, recarga la página.');
        }
    }
    
    setupEventListeners() {
        // Event listeners principales
        const newChatBtn = document.getElementById('newChatBtn');
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');
        
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.startNewChat());
        }
        
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => this.handleInputKeydown(e));
            messageInput.addEventListener('input', () => this.handleInputChange());
        }
        
        // Event listeners opcionales (pueden no existir en el HTML)
        const settingsBtn = document.getElementById('settingsBtn');
        const themeBtn = document.getElementById('themeBtn');
        const saveSettingsBtn = document.getElementById('saveSettingsBtn');
        const resetSettingsBtn = document.getElementById('resetSettingsBtn');
        const closeSettingsBtn = document.getElementById('closeSettingsBtn');
        
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.ui.showSettings());
        }
        
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        }
        
        if (resetSettingsBtn) {
            resetSettingsBtn.addEventListener('click', () => this.resetSettings());
        }
        
        if (closeSettingsBtn) {
            closeSettingsBtn.addEventListener('click', () => this.ui.hideSettings());
        }
        
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const prompt = e.currentTarget.dataset.prompt;
                this.sendQuickAction(prompt);
            });
        });
        
        
        const attachBtn = document.getElementById('attachBtn');
        const voiceBtn = document.getElementById('voiceBtn');
        
        if (attachBtn) {
            attachBtn.addEventListener('click', () => this.handleAttachFile());
        }
        
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.handleVoiceInput());
        }
        
        
        const settingsModal = document.getElementById('settingsModal');
        if (settingsModal) {
            settingsModal.addEventListener('click', (e) => {
                if (e.target.id === 'settingsModal') {
                    this.ui.hideSettings();
                }
            });
        }
        
        this.websocketManager.on('connected', () => {
            this.state.isConnected = true;
            this.ui.updateConnectionStatus(true);
        });
        
        this.websocketManager.on('disconnected', () => {
            this.state.isConnected = false;
            this.ui.updateConnectionStatus(false);
        });
        
        this.websocketManager.on('message', (data) => {
            this.handleWebSocketMessage(data);
        });
        
        this.websocketManager.on('typing', (data) => {
            this.handleTypingIndicator(data);
        });
        
        
        window.addEventListener('beforeunload', (e) => {
            if (this.state.messages.length > 0) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }
    
    async startNewChat() {
        try {
            
            this.state.currentSessionId = this.generateSessionId();
            this.state.messages = [];
            
            
            this.ui.clearMessages();
            this.ui.showWelcomeScreen();
            
            
            await this.loadConversations();
            
            console.log('✅ Nueva conversación iniciada:', this.state.currentSessionId);
            
        } catch (error) {
            console.error('❌ Error iniciando nueva conversación:', error);
            this.ui.showError('Error iniciando nueva conversación');
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        try {
            
            messageInput.value = '';
            this.updateCharCounter();
            
            
            if (!this.state.currentSessionId) {
                this.state.currentSessionId = this.generateSessionId();
            }
            
            
            const userMessage = {
                id: this.generateMessageId(),
                type: 'user',
                content: message,
                timestamp: new Date().toISOString()
            };
            
            this.state.messages.push(userMessage);
            this.ui.addMessage(userMessage);
            
            
            this.ui.hideWelcomeScreen();
            
            
            await this.websocketManager.sendMessage({
                type: 'message',
                message: message,
                session_id: this.state.currentSessionId,
                history: this.getRecentHistory()
            });
            
            
            this.ui.showTypingIndicator();
            
        } catch (error) {
            console.error('❌ Error enviando mensaje:', error);
            this.ui.showError('Error enviando mensaje');
        }
    }
    
    async sendQuickAction(prompt) {
        
        const messageInput = document.getElementById('messageInput');
        messageInput.value = prompt;
        
        
        await this.sendMessage();
    }
    
    handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }
    
    handleInputChange() {
        this.updateCharCounter();
        this.autoResizeTextarea();
        
        
        if (this.state.isConnected) {
            this.websocketManager.sendTyping(true);
        }
    }
    
    updateCharCounter() {
        const messageInput = document.getElementById('messageInput');
        const charCounter = document.getElementById('charCount');
        const count = messageInput.value.length;
        
        if (charCounter) {
            charCounter.textContent = count;
        }
        
        
        if (charCounter) {
            if (count > 1800) {
                charCounter.style.color = '#ef4444';
            } else if (count > 1500) {
                charCounter.style.color = '#f59e0b';
            } else {
                charCounter.style.color = 'var(--text-muted)';
            }
        }
    }
    
    autoResizeTextarea() {
        const messageInput = document.getElementById('messageInput');
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }
    
    handleWebSocketMessage(data) {
        try {
            switch (data.type) {
                case 'response':
                    this.handleAIResponse(data);
                    break;
                case 'error':
                    this.handleError(data);
                    break;
                case 'typing':
                    this.handleTypingIndicator(data);
                    break;
                case 'context_updated':
                    this.handleContextUpdate(data);
                    break;
                default:
                    console.warn('Tipo de mensaje WebSocket no reconocido:', data.type);
            }
        } catch (error) {
            console.error('❌ Error procesando mensaje WebSocket:', error);
        }
    }
    
    handleAIResponse(data) {
        
        this.ui.hideTypingIndicator();
        
        
        const aiMessage = {
            id: this.generateMessageId(),
            type: 'assistant',
            content: data.message,
            timestamp: data.timestamp,
            confidence: data.confidence,
            context: data.context,
            modelInfo: data.model_info
        };
        
        
        this.state.messages.push(aiMessage);
        this.ui.addMessage(aiMessage);
        
        
        this.updateConversationList();
        
        
        this.ui.scrollToBottom();
    }
    
    handleError(data) {
        this.ui.hideTypingIndicator();
        this.ui.showError(data.message);
    }
    
    handleTypingIndicator(data) {
        if (data.is_typing) {
            this.ui.showTypingIndicator();
        } else {
            this.ui.hideTypingIndicator();
        }
    }
    
    handleContextUpdate(data) {
        console.log('✅ Contexto actualizado:', data);
    }
    
    async loadConversations() {
        try {
            
            
            const conversations = this.getStoredConversations();
            this.state.conversations = conversations;
            this.ui.updateConversationList(conversations);
            
        } catch (error) {
            console.error('❌ Error cargando conversaciones:', error);
        }
    }
    
    updateConversationList() {
        if (this.state.messages.length > 0) {
            const lastMessage = this.state.messages[this.state.messages.length - 1];
            const conversation = {
                id: this.state.currentSessionId,
                title: this.generateConversationTitle(),
                preview: lastMessage.content.substring(0, 100),
                timestamp: lastMessage.timestamp,
                messageCount: this.state.messages.length
            };
            
            
            const existingIndex = this.state.conversations.findIndex(c => c.id === this.state.currentSessionId);
            if (existingIndex >= 0) {
                this.state.conversations[existingIndex] = conversation;
            } else {
                this.state.conversations.unshift(conversation);
            }
            
            
            this.saveConversations();
            
            
            this.ui.updateConversationList(this.state.conversations);
        }
    }
    
    generateConversationTitle() {
        if (this.state.messages.length === 0) return 'Nueva conversación';
        
        const firstMessage = this.state.messages[0];
        return firstMessage.content.substring(0, 50) + (firstMessage.content.length > 50 ? '...' : '');
    }
    
    getRecentHistory() {
        return this.state.messages.slice(-10).map(msg => ({
            user_message: msg.type === 'user' ? msg.content : '',
            ai_response: msg.type === 'assistant' ? msg.content : ''
        }));
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    generateMessageId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async loadSettings() {
        try {
            const saved = localStorage.getItem('chatApp_settings');
            if (saved) {
                this.state.settings = { ...this.state.settings, ...JSON.parse(saved) };
            }
            
            
            const themeEl = document.getElementById('theme');
            const personalityEl = document.getElementById('aiPersonality');
            const responseLengthEl = document.getElementById('responseLength');
            const fontSizeEl = document.getElementById('fontSize');
            
            if (themeEl) themeEl.value = this.state.settings.theme;
            if (personalityEl) personalityEl.value = this.state.settings.personality;
            if (responseLengthEl) responseLengthEl.value = this.state.settings.responseLength;
            if (fontSizeEl) fontSizeEl.value = this.state.settings.fontSize;
            
        } catch (error) {
            console.error('❌ Error cargando configuración:', error);
        }
    }
    
    async saveSettings() {
        try {
            
            const themeEl = document.getElementById('theme');
            const personalityEl = document.getElementById('aiPersonality');
            const responseLengthEl = document.getElementById('responseLength');
            const fontSizeEl = document.getElementById('fontSize');
            
            if (themeEl) this.state.settings.theme = themeEl.value;
            if (personalityEl) this.state.settings.personality = personalityEl.value;
            if (responseLengthEl) this.state.settings.responseLength = responseLengthEl.value;
            if (fontSizeEl) this.state.settings.fontSize = fontSizeEl.value;
            
            
            localStorage.setItem('chatApp_settings', JSON.stringify(this.state.settings));
            
            
            this.ui.applyTheme(this.state.settings.theme);
            this.ui.applyFontSize(this.state.settings.fontSize);
            
            
            this.ui.hideSettings();
            
            
            this.ui.showSuccess('Configuración guardada correctamente');
            
        } catch (error) {
            console.error('❌ Error guardando configuración:', error);
            this.ui.showError('Error guardando configuración');
        }
    }
    
    resetSettings() {
        if (confirm('¿Estás seguro de que quieres restablecer la configuración?')) {
            this.state.settings = {
                theme: 'light',
                personality: 'professional',
                responseLength: 'medium',
                fontSize: 'medium'
            };
            
            
            const themeEl = document.getElementById('theme');
            const personalityEl = document.getElementById('aiPersonality');
            const responseLengthEl = document.getElementById('responseLength');
            const fontSizeEl = document.getElementById('fontSize');
            
            if (themeEl) themeEl.value = 'light';
            if (personalityEl) personalityEl.value = 'professional';
            if (responseLengthEl) responseLengthEl.value = 'medium';
            if (fontSizeEl) fontSizeEl.value = 'medium';
            
            
            this.ui.applyTheme('light');
            this.ui.applyFontSize('medium');
            
            this.ui.showSuccess('Configuración restablecida');
        }
    }
    
    toggleTheme() {
        const currentTheme = this.state.settings.theme;
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        this.state.settings.theme = newTheme;
        this.ui.applyTheme(newTheme);
        
        
        const themeBtn = document.getElementById('themeBtn');
        themeBtn.innerHTML = newTheme === 'light' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
        
        
        localStorage.setItem('chatApp_settings', JSON.stringify(this.state.settings));
    }
    
    handleAttachFile() {
        
        this.ui.showInfo('Funcionalidad de adjuntar archivos próximamente');
    }
    
    handleVoiceInput() {
        
        this.ui.showInfo('Funcionalidad de entrada de voz próximamente');
    }
    
    getStoredConversations() {
        try {
            const stored = localStorage.getItem('chatApp_conversations');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('❌ Error cargando conversaciones guardadas:', error);
            return [];
        }
    }
    
    saveConversations() {
        try {
            localStorage.setItem('chatApp_conversations', JSON.stringify(this.state.conversations));
        } catch (error) {
            console.error('❌ Error guardando conversaciones:', error);
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
