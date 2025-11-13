'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Eye,
  EyeOff,
  Check,
  X,
  Loader2,
  Key,
  TreePine,
  Search,
  Brain,
  Palette,
  DollarSign,
  AlertCircle,
  Info,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { maskAPIKey } from '@/lib/utils'
import { settingsApi } from '@/lib/api'

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  // API Key State
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [keyStatus, setKeyStatus] = useState<'valid' | 'invalid' | null>(null)

  // Tree Generation Settings
  const [treeSettings, setTreeSettings] = useState({
    toc_check_page_num: 20,
    max_page_num_each_node: 10,
    max_token_num_each_node: 20000,
    min_node_pages: 2,
    max_tree_depth: 5,
    max_retry: 3,
    if_add_node_id: true,
    if_add_node_summary: false,
    if_add_doc_description: false,
    if_add_node_text: false,
    if_use_toc: true,
    if_use_ocr: false,
  })

  // Query Settings (only settings actually used in backend)
  const [querySettings, setQuerySettings] = useState({
    citation_style: 'inline',
    cache_ttl_hours: 24,
  })

  // Model Settings (from settings-service ModelConfig)
  const [modelSettings, setModelSettings] = useState({
    model: 'gpt-4o',
    temperature: 0.7,
    max_tokens: 3000,
  })

  // UI Preferences
  const [uiPreferences, setUiPreferences] = useState({
    theme: 'system',
    fontSize: 'medium',
    codeTheme: 'github',
    animationSpeed: 'normal',
    sidebarPosition: 'left',
    showCostBadges: true,
    autoScroll: true,
    soundEnabled: false,
  })

  // Usage Settings
  const [usageSettings, setUsageSettings] = useState({
    monthly_limit: 50,
    per_query_limit: 1,
    per_query_limit_enabled: false,
    cache_first_mode: true,
  })

  // Load all settings when dialog opens
  useEffect(() => {
    if (open) {
      loadAllSettings()
    }
  }, [open])

  const loadAllSettings = async () => {
    await Promise.all([
      loadKeyStatus(),
      loadTreeSettings(),
      loadQuerySettings(),
      loadModelSettings(),
    ])
  }

  const loadKeyStatus = async () => {
    try {
      const data = await settingsApi.getKeyStatus()
      if (data.exists) {
        setApiKey(data.partial_key || '') // Show masked key
        setKeyStatus('valid')
      }
    } catch (error) {
      console.error('Failed to load key status:', error)
    }
  }

  const loadTreeSettings = async () => {
    try {
      const data = await settingsApi.getTreeSettings()
      setTreeSettings(data)
    } catch (error) {
      console.error('Failed to load tree settings:', error)
    }
  }

  const loadQuerySettings = async () => {
    try {
      const data = await settingsApi.getQuerySettings()
      setQuerySettings(data)
    } catch (error) {
      console.error('Failed to load query settings:', error)
    }
  }

  const loadModelSettings = async () => {
    try {
      const data = await settingsApi.getModelConfig()
      setModelSettings(data)
    } catch (error) {
      console.error('Failed to load model settings:', error)
    }
  }

  const verifyKey = async () => {
    setVerifying(true)
    try {
      // Verify the API key with backend
      const result = await settingsApi.verifyKey(apiKey)

      if (result.valid) {
        // Save the key if valid
        const saveResult = await settingsApi.saveKey(apiKey)
        setApiKey(saveResult.partial_key) // Show masked key
        setKeyStatus('valid')
        toast.success('API key verified and saved!')
      } else {
        setKeyStatus('invalid')
        toast.error(result.message || 'Invalid API key')
      }
    } catch (error: any) {
      setKeyStatus('invalid')
      toast.error(error.message || 'Failed to verify API key')
    } finally {
      setVerifying(false)
    }
  }

  const saveSettings = async () => {
    try {
      // Save all settings in parallel
      await Promise.all([
        settingsApi.updateTreeSettings(treeSettings),
        settingsApi.updateQuerySettings(querySettings),
        settingsApi.updateModelConfig(modelSettings),
      ])

      toast.success('Settings saved successfully!')
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save settings:', error)
      toast.error('Failed to save settings')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-4xl h-auto max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Configure your Indexer application settings
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="api-keys" className="w-full">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="api-keys" className="text-xs">
              <Key className="mr-1 h-3 w-3" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="tree-gen" className="text-xs">
              <TreePine className="mr-1 h-3 w-3" />
              Tree Gen
            </TabsTrigger>
            <TabsTrigger value="query" className="text-xs">
              <Search className="mr-1 h-3 w-3" />
              Query
            </TabsTrigger>
            <TabsTrigger value="model" className="text-xs">
              <Brain className="mr-1 h-3 w-3" />
              Model
            </TabsTrigger>
            <TabsTrigger value="ui" className="text-xs">
              <Palette className="mr-1 h-3 w-3" />
              UI
            </TabsTrigger>
            <TabsTrigger value="usage" className="text-xs">
              <DollarSign className="mr-1 h-3 w-3" />
              Usage
            </TabsTrigger>
          </TabsList>

          {/* API Keys Tab */}
          <TabsContent value="api-keys" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>OpenAI API Key</CardTitle>
                <CardDescription>
                  Your API key is encrypted and stored securely
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-..."
                      className="pr-10"
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0"
                      onClick={() => setShowKey(!showKey)}
                    >
                      {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </Button>
                  </div>
                  <Button
                    onClick={verifyKey}
                    disabled={!apiKey || verifying}
                  >
                    {verifying ? (
                      <Loader2 className="animate-spin" size={16} />
                    ) : (
                      'Verify'
                    )}
                  </Button>
                </div>

                {keyStatus && (
                  <div className={`flex items-center gap-2 text-sm ${
                    keyStatus === 'valid' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {keyStatus === 'valid' ? <Check size={16} /> : <X size={16} />}
                    {keyStatus === 'valid'
                      ? `Key verified: ${maskAPIKey(apiKey)}`
                      : 'Invalid API key'}
                  </div>
                )}

                <div className="rounded-lg bg-muted p-3 text-sm">
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="space-y-1">
                      <p>Get your OpenAI API key from the <a href="https://platform.openai.com/api-keys" target="_blank" className="underline">OpenAI Platform</a></p>
                      <p className="text-xs text-muted-foreground">Your key starts with "sk-" and is used to access OpenAI models</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tree Generation Tab */}
          <TabsContent value="tree-gen" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>PageIndex Tree Generation</CardTitle>
                <CardDescription>
                  Configure how document trees are generated
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* TOC Detection */}
                <div>
                  <label className="text-sm font-medium">TOC Check Pages</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Number of pages to check for Table of Contents
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[treeSettings.toc_check_page_num]}
                      onValueChange={([value]) =>
                        setTreeSettings({...treeSettings, toc_check_page_num: value})
                      }
                      min={5}
                      max={50}
                      step={5}
                      className="flex-1"
                    />
                    <span className="w-12 text-sm font-medium">
                      {treeSettings.toc_check_page_num}
                    </span>
                  </div>
                </div>

                {/* Node Size */}
                <div>
                  <label className="text-sm font-medium">Max Pages per Node</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Maximum pages each tree node can contain
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[treeSettings.max_page_num_each_node]}
                      onValueChange={([value]) =>
                        setTreeSettings({...treeSettings, max_page_num_each_node: value})
                      }
                      min={1}
                      max={50}
                      step={1}
                      className="flex-1"
                    />
                    <span className="w-12 text-sm font-medium">
                      {treeSettings.max_page_num_each_node}
                    </span>
                  </div>
                </div>

                {/* Max Tokens */}
                <div>
                  <label className="text-sm font-medium">Max Tokens per Node</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Maximum tokens each tree node can contain
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[treeSettings.max_token_num_each_node]}
                      onValueChange={([value]) =>
                        setTreeSettings({...treeSettings, max_token_num_each_node: value})
                      }
                      min={1000}
                      max={50000}
                      step={1000}
                      className="flex-1"
                    />
                    <span className="w-16 text-sm font-medium">
                      {treeSettings.max_token_num_each_node.toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Tree Depth */}
                <div>
                  <label className="text-sm font-medium">Max Tree Depth</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Maximum depth of the document tree structure
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[treeSettings.max_tree_depth]}
                      onValueChange={([value]) =>
                        setTreeSettings({...treeSettings, max_tree_depth: value})
                      }
                      min={2}
                      max={10}
                      step={1}
                      className="flex-1"
                    />
                    <span className="w-12 text-sm font-medium">
                      {treeSettings.max_tree_depth}
                    </span>
                  </div>
                </div>

                {/* Max Retry */}
                <div>
                  <label className="text-sm font-medium">Max Retry Attempts</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Maximum number of retry attempts for API calls
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[treeSettings.max_retry]}
                      onValueChange={([value]) =>
                        setTreeSettings({...treeSettings, max_retry: value})
                      }
                      min={1}
                      max={10}
                      step={1}
                      className="flex-1"
                    />
                    <span className="w-12 text-sm font-medium">
                      {treeSettings.max_retry}
                    </span>
                  </div>
                </div>

                {/* Toggle Options */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Add Node IDs</label>
                      <p className="text-xs text-muted-foreground">
                        Assign unique identifiers to tree nodes
                      </p>
                    </div>
                    <Switch
                      checked={treeSettings.if_add_node_id}
                      onCheckedChange={(checked) =>
                        setTreeSettings({...treeSettings, if_add_node_id: checked})
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Generate Node Summaries</label>
                      <p className="text-xs text-muted-foreground">
                        Create AI summaries for nodes (costs extra)
                      </p>
                    </div>
                    <Switch
                      checked={treeSettings.if_add_node_summary}
                      onCheckedChange={(checked) =>
                        setTreeSettings({...treeSettings, if_add_node_summary: checked})
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Use Table of Contents</label>
                      <p className="text-xs text-muted-foreground">
                        Use TOC if found in document
                      </p>
                    </div>
                    <Switch
                      checked={treeSettings.if_use_toc}
                      onCheckedChange={(checked) =>
                        setTreeSettings({...treeSettings, if_use_toc: checked})
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Enable OCR</label>
                      <p className="text-xs text-muted-foreground">
                        Use OCR for scanned PDFs
                      </p>
                    </div>
                    <Switch
                      checked={treeSettings.if_use_ocr}
                      onCheckedChange={(checked) =>
                        setTreeSettings({...treeSettings, if_use_ocr: checked})
                      }
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Query Settings Tab */}
          <TabsContent value="query" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Query Settings</CardTitle>
                <CardDescription>
                  Configure how queries are processed and responses are formatted
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Citation Style</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    How to format citations in answers
                  </p>
                  <Select
                    value={querySettings.citation_style}
                    onValueChange={(value) =>
                      setQuerySettings({...querySettings, citation_style: value})
                    }
                  >
                    <SelectTrigger className="w-full mt-1">
                      <SelectValue placeholder="Select citation style" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inline">Inline (pages X-Y)</SelectItem>
                      <SelectItem value="footnote">Footnote [1], [2]</SelectItem>
                      <SelectItem value="none">None</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium">Cache TTL (hours)</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    How long to cache query results (1 hour to 1 week)
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[querySettings.cache_ttl_hours]}
                      onValueChange={([value]) =>
                        setQuerySettings({...querySettings, cache_ttl_hours: value})
                      }
                      min={1}
                      max={168}
                      step={1}
                      className="flex-1"
                    />
                    <span className="w-16 text-sm font-medium">
                      {querySettings.cache_ttl_hours}h
                    </span>
                  </div>
                </div>

                <div className="rounded-lg bg-muted p-3 text-sm">
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="space-y-1">
                      <p className="font-medium">Note: Number of context nodes is automatically determined</p>
                      <p className="text-xs text-muted-foreground">
                        PageIndex's two-stage retrieval uses the LLM to intelligently select relevant nodes during Stage 1.
                        The number of nodes is not manually configurable.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Model Configuration Tab */}
          <TabsContent value="model" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Model Configuration</CardTitle>
                <CardDescription>
                  Configure OpenAI model parameters for query processing
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Model</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    OpenAI model used for both tree search (Stage 1) and answer generation (Stage 2)
                  </p>
                  <Select
                    value={modelSettings.model}
                    onValueChange={(value) =>
                      setModelSettings({...modelSettings, model: value})
                    }
                  >
                    <SelectTrigger className="w-full mt-1">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4o">GPT-4o (Recommended)</SelectItem>
                      <SelectItem value="gpt5">GPT-5</SelectItem>
                      <SelectItem value="gpt5-mini">GPT-5 Mini</SelectItem>
                      <SelectItem value="gpt5-nano">GPT-5 Nano</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium">Temperature</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Controls randomness (0 = focused, 2 = creative). Affects Stage 2 answer generation.
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[modelSettings.temperature]}
                      onValueChange={([value]) =>
                        setModelSettings({...modelSettings, temperature: value})
                      }
                      min={0}
                      max={2}
                      step={0.1}
                      className="flex-1"
                    />
                    <span className="w-12 text-sm font-medium">
                      {modelSettings.temperature.toFixed(1)}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Max Tokens</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Maximum response length (100-16000 tokens). Higher = longer answers.
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[modelSettings.max_tokens]}
                      onValueChange={([value]) =>
                        setModelSettings({...modelSettings, max_tokens: value})
                      }
                      min={100}
                      max={16000}
                      step={100}
                      className="flex-1"
                    />
                    <span className="w-16 text-sm font-medium">
                      {modelSettings.max_tokens}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* UI Preferences Tab */}
          <TabsContent value="ui" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>UI Preferences</CardTitle>
                <CardDescription>
                  Customize the application interface
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Theme</label>
                  <select
                    className="w-full mt-1 rounded-md border bg-background px-3 py-2 text-sm"
                    value={uiPreferences.theme}
                    onChange={(e) =>
                      setUiPreferences({...uiPreferences, theme: e.target.value})
                    }
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">Font Size</label>
                  <select
                    className="w-full mt-1 rounded-md border bg-background px-3 py-2 text-sm"
                    value={uiPreferences.fontSize}
                    onChange={(e) =>
                      setUiPreferences({...uiPreferences, fontSize: e.target.value})
                    }
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">Code Theme</label>
                  <select
                    className="w-full mt-1 rounded-md border bg-background px-3 py-2 text-sm"
                    value={uiPreferences.codeTheme}
                    onChange={(e) =>
                      setUiPreferences({...uiPreferences, codeTheme: e.target.value})
                    }
                  >
                    <option value="github">GitHub</option>
                    <option value="monokai">Monokai</option>
                    <option value="dracula">Dracula</option>
                  </select>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Show Cost Badges</label>
                      <p className="text-xs text-muted-foreground">
                        Display cost information on messages
                      </p>
                    </div>
                    <Switch
                      checked={uiPreferences.showCostBadges}
                      onCheckedChange={(checked) =>
                        setUiPreferences({...uiPreferences, showCostBadges: checked})
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Auto-scroll</label>
                      <p className="text-xs text-muted-foreground">
                        Automatically scroll to new messages
                      </p>
                    </div>
                    <Switch
                      checked={uiPreferences.autoScroll}
                      onCheckedChange={(checked) =>
                        setUiPreferences({...uiPreferences, autoScroll: checked})
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Sound Effects</label>
                      <p className="text-xs text-muted-foreground">
                        Play sounds for notifications
                      </p>
                    </div>
                    <Switch
                      checked={uiPreferences.soundEnabled}
                      onCheckedChange={(checked) =>
                        setUiPreferences({...uiPreferences, soundEnabled: checked})
                      }
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Usage & Costs Tab */}
          <TabsContent value="usage" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Usage & Costs</CardTitle>
                <CardDescription>
                  Monitor and control your API usage
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Usage Stats */}
                <div className="rounded-lg bg-muted p-4 space-y-2">
                  <h3 className="font-medium text-sm">Current Month Usage</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Total Queries</p>
                      <p className="text-xl font-semibold">150</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Total Cost</p>
                      <p className="text-xl font-semibold">$12.50</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Cache Hit Rate</p>
                      <p className="text-xl font-semibold">65%</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Saved by Cache</p>
                      <p className="text-xl font-semibold">$8.25</p>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Monthly Limit ($)</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Alert when usage exceeds this amount
                  </p>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[usageSettings.monthly_limit]}
                      onValueChange={([value]) =>
                        setUsageSettings({...usageSettings, monthly_limit: value})
                      }
                      min={10}
                      max={500}
                      step={10}
                      className="flex-1"
                    />
                    <span className="w-16 text-sm font-medium">
                      ${usageSettings.monthly_limit}
                    </span>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <label className="text-sm font-medium">Per-Query Limit</label>
                      <p className="text-xs text-muted-foreground">
                        Maximum cost per query
                      </p>
                    </div>
                    <Switch
                      checked={usageSettings.per_query_limit_enabled}
                      onCheckedChange={(checked) =>
                        setUsageSettings({...usageSettings, per_query_limit_enabled: checked})
                      }
                    />
                  </div>
                  {usageSettings.per_query_limit_enabled && (
                    <div className="flex items-center gap-4">
                      <Slider
                        value={[usageSettings.per_query_limit]}
                        onValueChange={([value]) =>
                          setUsageSettings({...usageSettings, per_query_limit: value})
                        }
                        min={0.1}
                        max={5}
                        step={0.1}
                        className="flex-1"
                      />
                      <span className="w-16 text-sm font-medium">
                        ${usageSettings.per_query_limit.toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Cache First Mode</label>
                    <p className="text-xs text-muted-foreground">
                      Always check cache before making API calls
                    </p>
                  </div>
                  <Switch
                    checked={usageSettings.cache_first_mode}
                    onCheckedChange={(checked) =>
                      setUsageSettings({...usageSettings, cache_first_mode: checked})
                    }
                  />
                </div>

                {/* Alert */}
                <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium text-yellow-600">Usage Alert</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        You've used 25% of your monthly limit. Current: $12.50 / $50.00
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={saveSettings}>
            Save Settings
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}