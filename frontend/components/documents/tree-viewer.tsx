'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  ChevronRight,
  ChevronDown,
  FileText,
  Loader2,
  AlertCircle,
  BookOpen,
  Hash,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { treeApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface TreeNode {
  title: string
  start_index?: number
  end_index?: number
  node_id?: string
  summary?: string
  nodes?: TreeNode[]
}

interface TreeViewerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  documentId: number
  documentName: string
}

export function TreeViewer({ open, onOpenChange, documentId, documentName }: TreeViewerProps) {
  const [tree, setTree] = useState<TreeNode[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (open && documentId) {
      loadTree()
    }
  }, [open, documentId])

  const loadTree = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await treeApi.getTree(documentId)
      setTree(response.tree)
      // Auto-expand first level
      if (response.tree && response.tree.length > 0) {
        const firstLevelIds = response.tree
          .filter((node: TreeNode) => node.node_id)
          .map((node: TreeNode) => node.node_id!)
        setExpandedNodes(new Set(firstLevelIds))
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tree')
      toast.error('Failed to load tree')
    } finally {
      setLoading(false)
    }
  }

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  const expandAll = () => {
    const allIds = new Set<string>()
    const collectIds = (nodes: TreeNode[]) => {
      nodes.forEach((node) => {
        if (node.node_id) allIds.add(node.node_id)
        if (node.nodes) collectIds(node.nodes)
      })
    }
    if (tree) collectIds(tree)
    setExpandedNodes(allIds)
  }

  const collapseAll = () => {
    setExpandedNodes(new Set())
  }

  const renderNode = (node: TreeNode, depth: number = 0) => {
    const hasChildren = node.nodes && node.nodes.length > 0
    const isExpanded = node.node_id ? expandedNodes.has(node.node_id) : false
    const nodeKey = node.node_id || `${node.title}-${depth}`

    return (
      <div key={nodeKey} className="select-none">
        <div
          className={cn(
            'group flex items-start gap-2 py-2 px-3 rounded-md hover:bg-accent/50 transition-colors cursor-pointer',
            depth === 0 && 'font-medium'
          )}
          style={{ paddingLeft: `${depth * 1.5 + 0.75}rem` }}
          onClick={() => {
            if (hasChildren && node.node_id) {
              toggleNode(node.node_id)
            }
          }}
        >
          {/* Expand/Collapse Icon */}
          <div className="flex-shrink-0 w-4 h-4 mt-0.5">
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              )
            ) : (
              <div className="w-4 h-4" />
            )}
          </div>

          {/* Node Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn('text-sm', depth === 0 && 'text-base font-semibold')}>
                {node.title}
              </span>

              {/* Page Range Badge */}
              {node.start_index && node.end_index && (
                <Badge variant="secondary" className="text-xs font-normal">
                  <BookOpen className="w-3 h-3 mr-1" />
                  {node.start_index === node.end_index
                    ? `p.${node.start_index}`
                    : `p.${node.start_index}-${node.end_index}`}
                </Badge>
              )}

              {/* Node ID Badge */}
              {node.node_id && (
                <Badge variant="outline" className="text-xs font-mono font-normal opacity-60 group-hover:opacity-100 transition-opacity">
                  <Hash className="w-3 h-3 mr-1" />
                  {node.node_id}
                </Badge>
              )}
            </div>

            {/* Summary */}
            {node.summary && isExpanded && (
              <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                {node.summary}
              </p>
            )}
          </div>
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="mt-0.5">
            {node.nodes!.map((childNode, idx) => renderNode(childNode, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-xl flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <span className="truncate">Document Tree</span>
              </DialogTitle>
              <DialogDescription className="mt-1.5 truncate">
                {documentName}
              </DialogDescription>
            </div>

            {/* Tree Controls */}
            {!loading && !error && tree && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={expandAll}
                  className="text-xs"
                >
                  Expand All
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={collapseAll}
                  className="text-xs"
                >
                  Collapse All
                </Button>
              </div>
            )}
          </div>
        </DialogHeader>

        {/* Tree Content */}
        <div className="flex-1 overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">Loading document tree...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-3" />
                <p className="text-sm font-medium mb-1">Failed to Load Tree</p>
                <p className="text-sm text-muted-foreground mb-4">{error}</p>
                <Button onClick={loadTree} size="sm">
                  Try Again
                </Button>
              </div>
            </div>
          )}

          {!loading && !error && tree && (
            <ScrollArea className="h-full px-6 py-4">
              {tree.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">No tree structure found</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-0.5">
                  {tree.map((node, idx) => renderNode(node, 0))}
                </div>
              )}
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
