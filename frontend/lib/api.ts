/**
 * API Client for Indexer Backend
 * Communicates with API Gateway at port 8000
 */

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for long operations
  headers: {
    'Content-Type': 'application/json',
  },
})

// ============================================================================
// Documents API
// ============================================================================

export interface Document {
  id: number
  filename: string
  file_path: string
  created_at: string  // API returns created_at not upload_date
  size: number  // API returns size not file_size
  page_count?: number  // API returns page_count not num_pages
  status: 'uploaded' | 'processing' | 'indexed' | 'error'
}

export const documentsApi = {
  /**
   * Upload a PDF document
   */
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<Document>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 1 minute for upload
    })

    return response.data
  },

  /**
   * Get all documents
   */
  getAll: async (): Promise<Document[]> => {
    const response = await api.get<{ documents: Document[] }>('/api/documents')
    return response.data.documents
  },

  /**
   * Get a single document by ID
   */
  getById: async (id: number): Promise<Document> => {
    const response = await api.get<Document>(`/api/documents/${id}`)
    return response.data
  },

  /**
   * Delete a document
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/documents/${id}`)
  },
}

// ============================================================================
// Tree API
// ============================================================================

export interface TreeNode {
  title: string
  start_index: number
  end_index: number
  node_id?: string
  nodes?: TreeNode[]
  text?: string
  summary?: string
}

export interface Tree {
  id: number
  doc_id: number
  tree_data: TreeNode[]
  num_pages: number
  num_nodes: number
  created_at: string
}

export const treeApi = {
  /**
   * Generate tree for a document
   */
  generate: async (docId: number): Promise<{ tree_id: number; status: string; message: string }> => {
    const response = await api.post(`/api/trees/generate/${docId}`, {}, {
      timeout: 300000, // 5 minutes for tree generation
    })
    return response.data
  },

  /**
   * Get tree for a document
   */
  getByDocId: async (docId: number): Promise<Tree> => {
    const response = await api.get<Tree>(`/api/trees/document/${docId}`)
    return response.data
  },

  /**
   * Get tree by ID
   */
  getById: async (treeId: number): Promise<Tree> => {
    const response = await api.get<Tree>(`/api/trees/${treeId}`)
    return response.data
  },

  /**
   * Get tree structure for viewing (simplified format)
   */
  getTree: async (docId: number): Promise<{ tree: TreeNode[] }> => {
    const treeData = await treeApi.getByDocId(docId)
    return { tree: treeData.tree_data }
  },
}

// ============================================================================
// Settings API
// ============================================================================

export interface TreeSettings {
  model: string
  toc_check_page_num: number
  max_page_num_each_node: number
  max_token_num_each_node: number
  if_add_node_id: boolean
  if_add_node_summary: boolean
  if_add_doc_description: boolean
  if_add_node_text: boolean
}

export interface QuerySettings {
  citation_style: 'inline' | 'footnote' | 'none'
  cache_ttl_hours: number
}

export interface ModelConfig {
  model: 'gpt-4o' | 'gpt5' | 'gpt5-mini' | 'gpt5-nano'
  temperature: number
  max_tokens: number
}

export const settingsApi = {
  /**
   * Verify OpenAI API key
   */
  verifyKey: async (key: string): Promise<{ valid: boolean; message: string }> => {
    const response = await api.post('/api/settings/verify-key', { key })
    return response.data
  },

  /**
   * Save OpenAI API key
   */
  saveKey: async (key: string): Promise<{ success: boolean; partial_key: string }> => {
    const response = await api.post('/api/settings/save-key', { key })
    return response.data
  },

  /**
   * Get key status (without revealing the key)
   */
  getKeyStatus: async (): Promise<{ has_key: boolean; partial_key?: string }> => {
    const response = await api.get('/api/settings/key-status')
    return response.data
  },

  /**
   * Get tree generation settings
   */
  getTreeSettings: async (): Promise<TreeSettings> => {
    const response = await api.get<TreeSettings>('/api/settings/tree')
    return response.data
  },

  /**
   * Update tree generation settings
   */
  updateTreeSettings: async (settings: Partial<TreeSettings>): Promise<TreeSettings> => {
    const response = await api.post<TreeSettings>('/api/settings/tree', settings)
    return response.data
  },

  /**
   * Get query settings
   */
  getQuerySettings: async (): Promise<QuerySettings> => {
    const response = await api.get<QuerySettings>('/api/settings/query')
    return response.data
  },

  /**
   * Update query settings
   */
  updateQuerySettings: async (settings: Partial<QuerySettings>): Promise<QuerySettings> => {
    const response = await api.post<QuerySettings>('/api/settings/query', settings)
    return response.data
  },

  /**
   * Get model configuration
   */
  getModelConfig: async (): Promise<ModelConfig> => {
    const response = await api.get<ModelConfig>('/api/settings/model')
    return response.data
  },

  /**
   * Update model configuration
   */
  updateModelConfig: async (config: Partial<ModelConfig>): Promise<ModelConfig> => {
    const response = await api.post<ModelConfig>('/api/settings/model', config)
    return response.data
  },
}

// ============================================================================
// Query API (PageIndex Two-Stage Retrieval)
// ============================================================================

export interface Citation {
  node_id: string
  section: string
  start_page: number
  end_page: number
}

export interface QueryRequest {
  question: string
  document_id: number
  use_cache?: boolean
  include_citations?: boolean
}

export interface QueryResponse {
  question: string
  answer: string
  citations: Citation[]
  tokens_used: number
  cost: number
  cached: boolean
  relevant_nodes: string[]
}

export const queryApi = {
  /**
   * Query a document using PageIndex two-stage retrieval
   */
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await api.post<QueryResponse>('/api/query', request, {
      timeout: 180000, // 3 minutes for query processing
    })
    return response.data
  },
}

// ============================================================================
// Conversations API
// ============================================================================

export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  tokens: number
  cost: number
  metadata?: string
  created_at: string
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export const conversationsApi = {
  /**
   * Get all conversations
   */
  getAll: async (): Promise<Conversation[]> => {
    const response = await api.get<{ conversations: Conversation[] }>('/api/conversations')
    return response.data.conversations
  },

  /**
   * Get a single conversation with messages
   */
  getById: async (id: number): Promise<Conversation & { messages: Message[] }> => {
    const response = await api.get<Conversation & { messages: Message[] }>(`/api/conversations/${id}`)
    return response.data
  },

  /**
   * Create a new conversation
   */
  create: async (title: string): Promise<Conversation> => {
    const response = await api.post<Conversation>('/api/conversations', { title })
    return response.data
  },

  /**
   * Delete a conversation
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/conversations/${id}`)
  },
}

// ============================================================================
// Stats API
// ============================================================================

export interface Stats {
  total_documents: number
  total_trees: number
  total_conversations: number
  cache_stats: {
    size: number
    hit_rate: number
  }
}

export const statsApi = {
  getAll: async (): Promise<Stats> => {
    const response = await api.get<Stats>('/api/stats')
    return response.data
  },
}

// ============================================================================
// Error Handling
// ============================================================================

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.detail || error.response.data?.message || error.message
      console.error('API Error:', message)
      throw new Error(message)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message)
      throw new Error('Network error: Unable to reach the server')
    } else {
      // Something else happened
      console.error('Error:', error.message)
      throw error
    }
  }
)

export default api
