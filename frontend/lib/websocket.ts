import { io, Socket } from 'socket.io-client'

// ============================================================================
// Types matching backend Chat Service
// ============================================================================

export interface QueryRequest {
  question: string
  document_id: number
  conversation_id: number
  use_cache?: boolean
  include_citations?: boolean
}

export interface QueryStartedEvent {
  question: string
  conversation_id: number
}

export interface Citation {
  node_id: string
  section: string
  start_page: number
  end_page: number
}

export interface QueryAnswerEvent {
  answer: string
  question: string
  citations: Citation[]
  tokens_used: number
  cost: number
  cached: boolean
  relevant_nodes: string[]
}

export interface QueryCompletedEvent {
  conversation_id: number
  tokens_used: number
  cost: number
}

export interface QueryErrorEvent {
  message: string
  conversation_id: number
}

export interface TreeProgressEvent {
  document_id: number
  status: string
  progress?: number
  message?: string
}

export interface TreeEvent {
  document_id: number
  tree_id?: number
  message?: string
  error?: string
}

export interface DocumentUpdateEvent {
  document_id: number
  status: string
  message?: string
}

export interface ConnectionStatusEvent {
  status: 'connected' | 'disconnected' | 'error'
  message?: string
  sid?: string
}

// ============================================================================
// WebSocket Manager
// ============================================================================

class WebSocketManager {
  private socket: Socket | null = null
  private listeners: Map<string, Set<Function>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false

  constructor() {
    // Don't auto-connect, let components call connect() explicitly
  }

  public connect() {
    if (this.socket?.connected || this.isConnecting) {
      return
    }

    this.isConnecting = true
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8004'

    this.socket = io(wsUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    })

    this.setupEventHandlers()
  }

  private setupEventHandlers() {
    if (!this.socket) return

    // Connection events
    this.socket.on('connect', () => {
      this.isConnecting = false
      this.reconnectAttempts = 0
      this.emit('connection-status', {
        status: 'connected',
        message: 'Connected to server'
      })
    })

    this.socket.on('connected', (data: { message: string; sid: string }) => {
      this.emit('server-connected', data)
    })

    this.socket.on('disconnect', (reason) => {
      this.isConnecting = false
      this.emit('connection-status', {
        status: 'disconnected',
        message: reason
      })
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket: Connection error -', error.message)
      this.isConnecting = false
      this.reconnectAttempts++

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this.emit('connection-status', {
          status: 'error',
          message: 'Failed to connect to server after multiple attempts'
        })
      }
    })

    // Query events (PageIndex two-stage retrieval)
    this.socket.on('query:started', (data: QueryStartedEvent) => {
      this.emit('query:started', data)
    })

    this.socket.on('query:answer', (data: QueryAnswerEvent) => {
      this.emit('query:answer', data)
    })

    this.socket.on('query:completed', (data: QueryCompletedEvent) => {
      this.emit('query:completed', data)
    })

    this.socket.on('query:error', (data: QueryErrorEvent) => {
      console.error('Query: Error -', data.message)
      this.emit('query:error', data)
    })

    this.socket.on('query:thinking_stream', (data: any) => {
      this.emit('query:thinking_stream', data)
    })

    this.socket.on('query:nodes', (data: any) => {
      this.emit('query:nodes', data)
    })

    this.socket.on('query:answer_stream', (data: any) => {
      this.emit('query:answer_stream', data)
    })

    this.socket.on('query:answer_complete', (data: any) => {
      this.emit('query:answer_complete', data)
    })

    this.socket.on('query:progress', (data: any) => {
      this.emit('query:progress', data)
    })

    // Tree generation events
    this.socket.on('tree:started', (data: TreeEvent) => {
      this.emit('tree:started', data)
    })

    this.socket.on('tree:progress', (data: TreeProgressEvent) => {
      this.emit('tree:progress', data)
    })

    this.socket.on('tree:completed', (data: TreeEvent) => {
      this.emit('tree:completed', data)
    })

    this.socket.on('tree:error', (data: TreeEvent) => {
      console.error('Tree: Generation error -', data.error)
      this.emit('tree:error', data)
    })

    // Document update events
    this.socket.on('document:update', (data: DocumentUpdateEvent) => {
      this.emit('document:update', data)
    })

    // Generic error event
    this.socket.on('error', (error: { message: string }) => {
      console.error('Socket: Error -', error.message)
      this.emit('socket-error', error)
    })
  }

  /**
   * Send a query to the chat service
   */
  public sendQuery(queryRequest: QueryRequest) {
    if (!this.socket?.connected) {
      console.error('WebSocket: Cannot send query - not connected')
      this.emit('query:error', {
        message: 'Not connected to server. Please try again.',
        conversation_id: queryRequest.conversation_id
      })
      return
    }

    this.socket.emit('query', queryRequest)
  }

  /**
   * Send a generic message (legacy support)
   */
  public sendMessage(message: string, documentId?: number, conversationId?: number) {
    if (!this.socket?.connected) {
      console.error('WebSocket: Cannot send message - not connected')
      return
    }

    this.socket.emit('message', {
      message,
      document_id: documentId,
      conversation_id: conversationId,
      timestamp: new Date().toISOString(),
    })
  }

  /**
   * Register event listener
   */
  public on(event: string, handler: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)?.add(handler)
  }

  /**
   * Unregister event listener
   */
  public off(event: string, handler: Function) {
    this.listeners.get(event)?.delete(handler)
  }

  /**
   * Emit event to local listeners
   */
  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach(handler => {
      try {
        handler(data)
      } catch (error) {
        console.error(`Error in event handler for ${event}:`, error)
      }
    })
  }

  /**
   * Disconnect from WebSocket
   */
  public disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.isConnecting = false
    }
  }

  /**
   * Check if WebSocket is connected
   */
  public isConnected(): boolean {
    return this.socket?.connected ?? false
  }

  /**
   * Get connection state
   */
  public getConnectionState(): 'connected' | 'disconnected' | 'connecting' {
    if (this.socket?.connected) return 'connected'
    if (this.isConnecting) return 'connecting'
    return 'disconnected'
  }
}

// ============================================================================
// Singleton Export
// ============================================================================

export const wsManager = new WebSocketManager()

// ============================================================================
// React Hook
// ============================================================================

import { useEffect, useState } from 'react'

export interface UseWebSocketReturn {
  isConnected: boolean
  connectionStatus: ConnectionStatusEvent
  sendQuery: (request: QueryRequest) => void
  sendMessage: (message: string, documentId?: number, conversationId?: number) => void
  on: (event: string, handler: Function) => void
  off: (event: string, handler: Function) => void
  connect: () => void
  disconnect: () => void
}

export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(wsManager.isConnected())
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatusEvent>({
    status: wsManager.isConnected() ? 'connected' : 'disconnected'
  })

  useEffect(() => {
    const handleConnectionStatus = (status: ConnectionStatusEvent) => {
      setConnectionStatus(status)
      setIsConnected(status.status === 'connected')
    }

    wsManager.on('connection-status', handleConnectionStatus)

    // Auto-connect when hook is used
    if (!wsManager.isConnected()) {
      wsManager.connect()
    }

    return () => {
      wsManager.off('connection-status', handleConnectionStatus)
      // Don't disconnect on unmount - keep connection alive
    }
  }, [])

  return {
    isConnected,
    connectionStatus,
    sendQuery: wsManager.sendQuery.bind(wsManager),
    sendMessage: wsManager.sendMessage.bind(wsManager),
    on: wsManager.on.bind(wsManager),
    off: wsManager.off.bind(wsManager),
    connect: wsManager.connect.bind(wsManager),
    disconnect: wsManager.disconnect.bind(wsManager),
  }
}
