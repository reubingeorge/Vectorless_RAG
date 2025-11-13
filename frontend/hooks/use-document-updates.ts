/**
 * React Hook for Real-Time Document Updates via WebSocket
 * Listens to document processing and tree generation events
 */

import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000'

export interface DocumentUpdateEvent {
  doc_id: number
  status: 'uploaded' | 'processing' | 'indexed' | 'error'
  message?: string
  num_pages?: number
  progress?: number
}

export interface TreeGenerationEvent {
  doc_id: number
  tree_id?: number
  status: 'started' | 'processing' | 'completed' | 'error'
  message?: string
  progress?: number
  num_nodes?: number
  num_pages?: number
}

interface UseDocumentUpdatesOptions {
  onDocumentUpdate?: (event: DocumentUpdateEvent) => void
  onTreeGeneration?: (event: TreeGenerationEvent) => void
  onError?: (error: Error) => void
}

export function useDocumentUpdates({
  onDocumentUpdate,
  onTreeGeneration,
  onError,
}: UseDocumentUpdatesOptions = {}) {
  const socketRef = useRef<Socket | null>(null)
  const isConnecting = useRef(false)

  useEffect(() => {
    // Prevent double connection in React Strict Mode
    if (isConnecting.current || socketRef.current?.connected) {
      return
    }

    isConnecting.current = true

    // Connect to WebSocket
    const socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000,
    })

    socketRef.current = socket

    // Connection events
    socket.on('connect', () => {
      isConnecting.current = false
    })

    socket.on('disconnect', (reason) => {
      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        // Don't reconnect if manually disconnected
        isConnecting.current = false
      }
    })

    socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error)
      isConnecting.current = false
      onError?.(error)
    })

    // Document update events
    socket.on('document:update', (event: DocumentUpdateEvent) => {
      onDocumentUpdate?.(event)
    })

    socket.on('document:processing', (event: DocumentUpdateEvent) => {
      onDocumentUpdate?.({ ...event, status: 'processing' })
    })

    socket.on('document:indexed', (event: DocumentUpdateEvent) => {
      onDocumentUpdate?.({ ...event, status: 'indexed' })
    })

    socket.on('document:error', (event: DocumentUpdateEvent) => {
      console.error('Document error:', event)
      onDocumentUpdate?.({ ...event, status: 'error' })
    })

    // Tree generation events
    socket.on('tree:started', (event: TreeGenerationEvent) => {
      onTreeGeneration?.({ ...event, status: 'started' })
    })

    socket.on('tree:progress', (event: TreeGenerationEvent) => {
      onTreeGeneration?.({ ...event, status: 'processing' })
    })

    socket.on('tree:completed', (event: TreeGenerationEvent) => {
      onTreeGeneration?.({ ...event, status: 'completed' })
    })

    socket.on('tree:error', (event: TreeGenerationEvent) => {
      console.error('Tree generation error:', event)
      onTreeGeneration?.({ ...event, status: 'error' })
    })

    // Cleanup on unmount only
    return () => {
      isConnecting.current = false
      if (socket.connected) {
        socket.disconnect()
      }
    }
  }, []) // Empty deps - only run once on mount

  return {
    socket: socketRef.current,
    isConnected: socketRef.current?.connected || false,
  }
}
