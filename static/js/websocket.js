/**
 * AI Chat Assistant - Módulo WebSocket
 * Manejo de conexiones en tiempo real
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnecting = false;
        this.eventListeners = {};
        this.messageQueue = [];
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
    }
    
    /**
     * Conectar al WebSocket
     */
    async connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }
        
        this.isConnecting = true;
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
            
            console.log('🔌 Conectando a WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = (event) => {
                console.log(' WebSocket conectado');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.processMessageQueue();
                this.emit('connected', event);
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error(' Error parseando mensaje WebSocket:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log(' WebSocket desconectado:', event.code, event.reason);
                this.isConnecting = false;
                this.stopHeartbeat();
                this.emit('disconnected', event);
                
                
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error(' Error en WebSocket:', error);
                this.isConnecting = false;
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error(' Error conectando WebSocket:', error);
            this.isConnecting = false;
            this.emit('error', error);
        }
    }
    
    /**
     * Desconectar WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Desconexión intencional');
            this.ws = null;
        }
        this.stopHeartbeat();
        this.reconnectAttempts = this.maxReconnectAttempts; 
    }
    
    /**
     * Enviar mensaje
     */
    sendMessage(data) {
        const message = {
            ...data,
            timestamp: new Date().toISOString(),
            id: this.generateMessageId()
        };
        
        if (this.isConnected()) {
            try {
                this.ws.send(JSON.stringify(message));
                console.log('📤 Mensaje enviado:', message.type);
            } catch (error) {
                console.error('❌ Error enviando mensaje:', error);
                this.queueMessage(message);
            }
        } else {
            console.log('⏳ WebSocket no conectado, encolando mensaje');
            this.queueMessage(message);
        }
    }
    
    /**
     * Enviar indicador de escritura
     */
    sendTyping(isTyping) {
        this.sendMessage({
            type: 'typing',
            is_typing: isTyping,
            user_id: this.getUserId()
        });
    }
    
    /**
     * Enviar actualización de contexto
     */
    sendContextUpdate(context) {
        this.sendMessage({
            type: 'context_update',
            ...context
        });
    }
    
    /**
     * Manejar mensajes recibidos
     */
    handleMessage(data) {
        console.log('📥 Mensaje recibido:', data.type);
        
        switch (data.type) {
            case 'response':
                this.emit('message', data);
                break;
                
            case 'error':
                this.emit('error', data);
                break;
                
            case 'typing':
                this.emit('typing', data);
                break;
                
            case 'context_updated':
                this.emit('context_updated', data);
                break;
                
            case 'admin_broadcast':
                this.emit('admin_broadcast', data);
                break;
                
            case 'pong':
                this.handlePong();
                break;
                
            default:
                console.warn('⚠️ Tipo de mensaje no reconocido:', data.type);
                this.emit('unknown_message', data);
        }
    }
    
    /**
     * Verificar si está conectado
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
    
    /**
     * Obtener estado de conexión
     */
    getConnectionState() {
        if (!this.ws) return 'disconnected';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }
    
    /**
     * Programar reconexión
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ Máximo de intentos de reconexión alcanzado');
            this.emit('max_reconnect_attempts_reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); 
        
        console.log(`🔄 Reintentando conexión en ${delay}ms (intento ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    /**
     * Iniciar heartbeat
     */
    startHeartbeat() {
        this.stopHeartbeat(); 
        
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected()) {
                this.sendPing();
            }
        }, 30000); 
    }
    
    /**
     * Detener heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    /**
     * Enviar ping
     */
    sendPing() {
        this.sendMessage({
            type: 'ping'
        });
        
        
        this.heartbeatTimeout = setTimeout(() => {
            console.log('❌ Timeout de heartbeat, cerrando conexión');
            this.ws.close(1000, 'Heartbeat timeout');
        }, 10000); 
    }
    
    /**
     * Manejar pong
     */
    handlePong() {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    /**
     * Encolar mensaje
     */
    queueMessage(message) {
        this.messageQueue.push(message);
        
        
        if (this.messageQueue.length > 100) {
            this.messageQueue.shift();
        }
    }
    
    /**
     * Procesar cola de mensajes
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected()) {
            const message = this.messageQueue.shift();
            try {
                this.ws.send(JSON.stringify(message));
                console.log('📤 Mensaje de cola enviado:', message.type);
            } catch (error) {
                console.error('❌ Error enviando mensaje de cola:', error);
                this.messageQueue.unshift(message); 
                break;
            }
        }
    }
    
    /**
     * Obtener ID de usuario
     */
    getUserId() {
        
        return localStorage.getItem('userId') || 'anonymous';
    }
    
    /**
     * Generar ID de mensaje
     */
    generateMessageId() {
        return 'ws_msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Sistema de eventos
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }
    
    off(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }
    
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ Error en listener de evento ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Obtener estadísticas de conexión
     */
    getStats() {
        return {
            connectionState: this.getConnectionState(),
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            isConnected: this.isConnected(),
            lastActivity: this.lastActivity
        };
    }
    
    /**
     * Configurar opciones de reconexión
     */
    setReconnectOptions(options) {
        if (options.maxAttempts !== undefined) {
            this.maxReconnectAttempts = options.maxAttempts;
        }
        if (options.delay !== undefined) {
            this.reconnectDelay = options.delay;
        }
    }
    
    /**
     * Limpiar recursos
     */
    cleanup() {
        this.disconnect();
        this.eventListeners = {};
        this.messageQueue = [];
    }
}


class AdminWebSocketManager extends WebSocketManager {
    constructor() {
        super();
        this.isAdmin = false;
    }
    
    async connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }
        
        this.isConnecting = true;
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/admin`;
            
            console.log('🔌 Conectando a WebSocket de administración:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('✅ WebSocket de administración conectado');
                this.isConnecting = false;
                this.isAdmin = true;
                this.startHeartbeat();
                this.emit('connected', event);
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleAdminMessage(data);
                } catch (error) {
                    console.error('❌ Error parseando mensaje de administración:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket de administración desconectado:', event.code, event.reason);
                this.isConnecting = false;
                this.isAdmin = false;
                this.stopHeartbeat();
                this.emit('disconnected', event);
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ Error en WebSocket de administración:', error);
                this.isConnecting = false;
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('❌ Error conectando WebSocket de administración:', error);
            this.isConnecting = false;
            this.emit('error', error);
        }
    }
    
    handleAdminMessage(data) {
        console.log('📥 Mensaje de administración recibido:', data.type);
        
        switch (data.type) {
            case 'admin_stats':
                this.emit('admin_stats', data.stats);
                break;
                
            case 'connection_stats':
                this.emit('connection_stats', data.connections);
                break;
                
            case 'broadcast_sent':
                this.emit('broadcast_sent', data);
                break;
                
            default:
                this.handleMessage(data);
        }
    }
    
    sendAdminCommand(command, data = {}) {
        this.sendMessage({
            type: 'admin_command',
            command: command,
            ...data
        });
    }
    
    getStats() {
        this.sendAdminCommand('get_stats');
    }
    
    getConnections() {
        this.sendAdminCommand('get_connections');
    }
    
    broadcast(message) {
        this.sendAdminCommand('broadcast', { message });
    }
}
