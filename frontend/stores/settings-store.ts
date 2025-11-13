import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

interface TreeGenerationSettings {
  toc_check_page_num: number
  max_page_num_each_node: number
  max_token_num_each_node: number
  min_node_pages: number
  max_tree_depth: number
  if_add_node_id: boolean
  if_add_node_summary: boolean
  if_add_doc_description: boolean
  if_add_node_text: boolean
  if_use_toc: boolean
  if_use_ocr: boolean
}

interface QuerySettings {
  response_style: 'concise' | 'balanced' | 'detailed'
  max_context_nodes: number
  citation_style: 'inline' | 'footnote' | 'none'
  cache_ttl_hours: number
  streaming_enabled: boolean
}

interface ModelConfig {
  model: 'gpt-4' | 'gpt-4-turbo' | 'gpt-4o' | 'gpt-3.5-turbo'
  temperature: number
  max_tokens: number
  top_p: number
  frequency_penalty: number
  presence_penalty: number
}

interface UIPreferences {
  theme: 'light' | 'dark' | 'system'
  fontSize: 'small' | 'medium' | 'large'
  codeTheme: 'github' | 'monokai' | 'dracula'
  animationSpeed: 'off' | 'reduced' | 'normal'
  sidebarPosition: 'left' | 'right'
  showCostBadges: boolean
  autoScroll: boolean
  soundEnabled: boolean
}

interface UsageSettings {
  monthly_limit: number
  per_query_limit: number
  per_query_limit_enabled: boolean
  cache_first_mode: boolean
}

interface SettingsStore {
  // API Key
  apiKeyStatus: 'valid' | 'invalid' | 'unchecked'
  apiKeyDisplay: string

  // Tree Generation Settings
  treeSettings: TreeGenerationSettings

  // Query Settings
  querySettings: QuerySettings

  // Model Config
  modelConfig: ModelConfig

  // UI Preferences
  uiPreferences: UIPreferences

  // Usage Settings
  usageSettings: UsageSettings

  // Actions
  updateTreeSettings: (settings: Partial<TreeGenerationSettings>) => void
  updateQuerySettings: (settings: Partial<QuerySettings>) => void
  updateModelConfig: (config: Partial<ModelConfig>) => void
  updateUIPreferences: (prefs: Partial<UIPreferences>) => void
  updateUsageSettings: (settings: Partial<UsageSettings>) => void
  setApiKeyStatus: (status: 'valid' | 'invalid' | 'unchecked', display?: string) => void
  loadSettingsFromServer: () => Promise<void>
  saveSettingsToServer: () => Promise<void>
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      // Default values
      apiKeyStatus: 'unchecked',
      apiKeyDisplay: '',

      treeSettings: {
        toc_check_page_num: 20,
        max_page_num_each_node: 10,
        max_token_num_each_node: 20000,
        min_node_pages: 2,
        max_tree_depth: 5,
        if_add_node_id: true,
        if_add_node_summary: false,
        if_add_doc_description: false,
        if_add_node_text: false,
        if_use_toc: true,
        if_use_ocr: false,
      },

      querySettings: {
        response_style: 'balanced',
        max_context_nodes: 5,
        citation_style: 'inline',
        cache_ttl_hours: 24,
        streaming_enabled: true,
      },

      modelConfig: {
        model: 'gpt-4',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 1,
        frequency_penalty: 0,
        presence_penalty: 0,
      },

      uiPreferences: {
        theme: 'system',
        fontSize: 'medium',
        codeTheme: 'github',
        animationSpeed: 'normal',
        sidebarPosition: 'left',
        showCostBadges: true,
        autoScroll: true,
        soundEnabled: false,
      },

      usageSettings: {
        monthly_limit: 50,
        per_query_limit: 1,
        per_query_limit_enabled: false,
        cache_first_mode: true,
      },

      // Actions
      updateTreeSettings: (settings) =>
        set((state) => ({
          treeSettings: { ...state.treeSettings, ...settings },
        })),

      updateQuerySettings: (settings) =>
        set((state) => ({
          querySettings: { ...state.querySettings, ...settings },
        })),

      updateModelConfig: (config) =>
        set((state) => ({
          modelConfig: { ...state.modelConfig, ...config },
        })),

      updateUIPreferences: (prefs) =>
        set((state) => ({
          uiPreferences: { ...state.uiPreferences, ...prefs },
        })),

      updateUsageSettings: (settings) =>
        set((state) => ({
          usageSettings: { ...state.usageSettings, ...settings },
        })),

      setApiKeyStatus: (status, display) =>
        set({
          apiKeyStatus: status,
          apiKeyDisplay: display || '',
        }),

      loadSettingsFromServer: async () => {
        try {
          const [treeRes, queryRes, modelRes, usageRes] = await Promise.all([
            axios.get(`${API_URL}/api/settings/tree`),
            axios.get(`${API_URL}/api/settings/query`),
            axios.get(`${API_URL}/api/settings/model`),
            axios.get(`${API_URL}/api/settings/usage`),
          ])

          set({
            treeSettings: treeRes.data,
            querySettings: queryRes.data,
            modelConfig: modelRes.data,
            usageSettings: usageRes.data,
          })
        } catch (error) {
          console.error('Failed to load settings from server:', error)
        }
      },

      saveSettingsToServer: async () => {
        const state = get()
        try {
          await Promise.all([
            axios.post(`${API_URL}/api/settings/tree`, state.treeSettings),
            axios.post(`${API_URL}/api/settings/query`, state.querySettings),
            axios.post(`${API_URL}/api/settings/model`, state.modelConfig),
            axios.post(`${API_URL}/api/settings/usage`, state.usageSettings),
          ])
        } catch (error) {
          console.error('Failed to save settings to server:', error)
          throw error
        }
      },
    }),
    {
      name: 'settings-storage',
      partialize: (state) => ({
        // Only persist UI preferences and usage settings locally
        uiPreferences: state.uiPreferences,
        usageSettings: state.usageSettings,
        apiKeyDisplay: state.apiKeyDisplay,
        apiKeyStatus: state.apiKeyStatus,
      }),
    }
  )
)