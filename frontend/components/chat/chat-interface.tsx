'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { MessageBubble } from './message-bubble'
import { Send, StopCircle, FileText, AlertCircle, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'
import { documentsApi, conversationsApi, type Document } from '@/lib/api'
import { useWebSocket, type QueryAnswerEvent, type QueryErrorEvent } from '@/lib/websocket'
import toast from 'react-hot-toast'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isStreaming?: boolean
  documentContext?: string
  cost?: number
  tokens?: number
  cached?: boolean
  citations?: Array<{
    node_id: string
    section: string
    start_page: number
    end_page: number
  }>
}

interface ChatInterfaceProps {
  selectedDocument: string | null
  onNavigateToDocuments: () => void
}

export function ChatInterface({ selectedDocument, onNavigateToDocuments }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your RAG assistant powered by PageIndex. I can help you understand and query your documents using two-stage reasoning-based retrieval. Select a document above to get started!',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocId, setSelectedDocId] = useState<string>('')
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [currentQuestionId, setCurrentQuestionId] = useState<string | null>(null)
  const [streamedThinking, setStreamedThinking] = useState<string>('')
  const [streamedNodes, setStreamedNodes] = useState<string[]>([])
  const [streamedAnswer, setStreamedAnswer] = useState<string>('')
  const [isStreamingAnswer, setIsStreamingAnswer] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // WebSocket connection
  const { isConnected, sendQuery, on, off } = useWebSocket()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load documents on mount
  useEffect(() => {
    loadDocuments()
    createConversation()
  }, [])

  // Setup WebSocket event listeners for real-time streaming
  useEffect(() => {
    const handleThinkingStream = (data: any) => {
      setStreamedThinking((prev) => prev + data.chunk)
    }

    const handleNodes = (data: any) => {
      setStreamedNodes(data.node_list)
    }

    const handleAnswerStream = (data: any) => {
      setIsStreamingAnswer(true)
      setStreamedAnswer((prev) => prev + data.chunk)
    }

    const handleAnswerComplete = (data: any) => {
      setIsStreamingAnswer(false)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: streamedAnswer,
        timestamp: new Date(),
        cost: data.cost,
        tokens: data.tokens_used,
        cached: data.cached,
        citations: data.citations,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
      setCurrentQuestionId(null)

      // Clear streaming state
      setStreamedThinking('')
      setStreamedNodes([])
      setStreamedAnswer('')

      // Show toast with cost info
      if (data.cached) {
        toast.success('Answer retrieved from cache (no cost)')
      } else {
        toast.success(`Query completed: ${data.tokens_used} tokens ($${data.cost.toFixed(4)})`)
      }
    }

    const handleQueryError = (data: QueryErrorEvent) => {
      console.error('Query error:', data)

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${data.message}`,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
      setIsLoading(false)
      setCurrentQuestionId(null)
      setThinkingProcess(null)
      toast.error(`Query failed: ${data.message}`)
    }

    const handleQueryStarted = () => {
      // Reset streaming state
      setStreamedThinking('')
      setStreamedNodes([])
      setStreamedAnswer('')
    }

    const handleQueryCompleted = () => {
      setIsLoading(false)
    }

    on('query:thinking_stream', handleThinkingStream)
    on('query:nodes', handleNodes)
    on('query:answer_stream', handleAnswerStream)
    on('query:answer_complete', handleAnswerComplete)
    on('query:error', handleQueryError)
    on('query:started', handleQueryStarted)
    on('query:completed', handleQueryCompleted)

    return () => {
      off('query:thinking_stream', handleThinkingStream)
      off('query:nodes', handleNodes)
      off('query:answer_stream', handleAnswerStream)
      off('query:answer_complete', handleAnswerComplete)
      off('query:error', handleQueryError)
      off('query:started', handleQueryStarted)
      off('query:completed', handleQueryCompleted)
    }
  }, [on, off, streamedAnswer])

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true)
      const docs = await documentsApi.getAll()
      // Filter only documents that are indexed (have status 'indexed')
      const indexedDocs = docs.filter(d => d.status === 'indexed')
      setDocuments(indexedDocs)

      // Auto-select first document if available
      if (indexedDocs.length > 0 && !selectedDocId) {
        setSelectedDocId(indexedDocs[0].id.toString())
      }
    } catch (error) {
      console.error('Error loading documents:', error)
      toast.error('Failed to load documents')
    } finally {
      setLoadingDocs(false)
    }
  }

  const createConversation = async () => {
    try {
      const conversation = await conversationsApi.create('New Conversation')
      setConversationId(conversation.id)
    } catch (error) {
      console.error('Error creating conversation:', error)
      toast.error('Failed to create conversation')
    }
  }

  const handleDocumentChange = (value: string) => {
    setSelectedDocId(value)
    const doc = documents.find(d => d.id.toString() === value)
    if (doc) {
      toast.success(`Switched to ${doc.filename}`)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    if (!selectedDocId) {
      toast.error('Please select a document first')
      return
    }

    if (!conversationId) {
      toast.error('No active conversation. Please refresh the page.')
      return
    }

    if (!isConnected) {
      toast.error('Not connected to chat service. Please check your connection.')
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setCurrentQuestionId(userMessage.id)
    setInput('')
    setIsLoading(true)

    // Send query via WebSocket
    sendQuery({
      question: input,
      document_id: parseInt(selectedDocId),
      conversation_id: conversationId,
      use_cache: true,
      include_citations: true,
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-4 flex-1">
          <h1 className="text-xl font-semibold">Chat</h1>

          {/* Document Selector */}
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            {loadingDocs ? (
              <span className="text-sm text-muted-foreground">Loading...</span>
            ) : documents.length === 0 ? (
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-amber-500" />
                <span className="text-sm text-muted-foreground">No indexed documents</span>
                <Button variant="link" size="sm" onClick={onNavigateToDocuments} className="h-auto p-0 text-xs">
                  Index a document
                </Button>
              </div>
            ) : (
              <Select value={selectedDocId} onValueChange={handleDocumentChange}>
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="Select a document..." />
                </SelectTrigger>
                <SelectContent>
                  {documents.map((doc) => (
                    <SelectItem key={doc.id} value={doc.id.toString()}>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        <span className="truncate">{doc.filename}</span>
                        {doc.page_count && (
                          <span className="text-xs text-muted-foreground">
                            ({doc.page_count} pages)
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={cn(
              "h-2 w-2 rounded-full",
              isConnected ? "bg-green-500" : "bg-red-500"
            )} />
            <span className="text-xs text-muted-foreground">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <span className="text-sm text-muted-foreground">Model: GPT-4o</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
        <div className="mx-auto max-w-4xl space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex justify-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <Bot size={16} />
              </div>
              <div className="max-w-[80%] rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm px-4 py-3">
                {streamedThinking || streamedNodes.length > 0 || streamedAnswer ? (
                  <div className="space-y-3">
                    {streamedThinking && (
                      <div className="text-sm text-gray-700 dark:text-gray-300 font-mono">
                        <span className="text-blue-600 dark:text-blue-400 font-semibold">&quot;thinking&quot;:</span>{' '}
                        <span className="italic">&quot;{streamedThinking}<span className="animate-pulse">|</span>&quot;</span>
                      </div>
                    )}

                    {streamedNodes.length > 0 && (
                      <div className="text-sm text-gray-700 dark:text-gray-300 font-mono">
                        <span className="text-blue-600 dark:text-blue-400 font-semibold">&quot;node_list&quot;:</span>{' '}
                        <span>[{streamedNodes.map(n => `"${n}"`).join(', ')}]</span>
                      </div>
                    )}

                    {streamedAnswer && (
                      <div className="text-sm text-gray-700 dark:text-gray-300 prose dark:prose-invert max-w-none">
                        {streamedAnswer}<span className="animate-pulse">|</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
                    <div className="h-2 w-2 rounded-full bg-blue-600 animate-pulse animation-delay-200" />
                    <div className="h-2 w-2 rounded-full bg-blue-600 animate-pulse animation-delay-400" />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Processing query...</span>
                  </div>
                )}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t px-6 py-4">
        <div className="mx-auto max-w-4xl">
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={selectedDocId ? "Ask about your document..." : "Select a document first..."}
              disabled={isLoading || !selectedDocId || !isConnected}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading || !selectedDocId || !isConnected}
              size="icon"
            >
              <Send size={18} />
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Press Enter to send, Shift+Enter for new line • PageIndex two-stage retrieval
          </p>
        </div>
      </div>
    </div>
  )
}
