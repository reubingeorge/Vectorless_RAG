'use client'

import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  FileText,
  Upload,
  Search,
  Grid,
  List,
  Trash2,
  Play,
  CheckCircle,
  Clock,
  XCircle,
  Loader2,
  TreePine,
  RefreshCw,
  AlertTriangle,
  Eye,
} from 'lucide-react'
import { cn, formatBytes, formatDate } from '@/lib/utils'
import { documentsApi, treeApi, type Document as ApiDocument } from '@/lib/api'
import { useDocumentUpdates } from '@/hooks/use-document-updates'
import { TreeViewer } from './tree-viewer'
import toast from 'react-hot-toast'

interface Document {
  id: number
  name: string
  size: number
  uploadDate: Date
  status: 'uploaded' | 'processing' | 'indexed' | 'error'
  pageCount?: number
  treeGenerated?: boolean
  progress?: number
}

interface DocumentsPanelProps {
  selectedDocument: string | null
  onDocumentSelect: (docId: string) => void
  onStartChat: () => void
}

export function DocumentsPanel({
  selectedDocument,
  onDocumentSelect,
  onStartChat,
}: DocumentsPanelProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [generatingTreeFor, setGeneratingTreeFor] = useState<Set<number>>(new Set())
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null)
  const [treeViewerOpen, setTreeViewerOpen] = useState(false)
  const [treeViewerDocument, setTreeViewerDocument] = useState<{ id: number; name: string } | null>(null)

  // WebSocket for real-time updates
  useDocumentUpdates({
    onDocumentUpdate: (event) => {
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === event.doc_id
            ? {
                ...doc,
                status: event.status,
                pageCount: event.num_pages || doc.pageCount,
                progress: event.progress,
              }
            : doc
        )
      )

      if (event.status === 'error') {
        toast.error(event.message || 'Document processing failed')
      }
    },
    onTreeGeneration: (event) => {
      const { doc_id, status, progress, message, num_nodes, num_pages } = event

      // Update progress
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === doc_id
            ? {
                ...doc,
                progress,
                status: status === 'completed' ? 'indexed' : doc.status,
                treeGenerated: status === 'completed',
              }
            : doc
        )
      )

      // Show detailed progress messages
      if (status === 'started') {
        toast.loading(message || `Starting tree generation...`, {
          id: `tree-${doc_id}`,
        })
      } else if (status === 'processing') {
        const progressText = progress ? ` (${Math.round(progress)}%)` : ''
        toast.loading(message || `Generating tree${progressText}...`, {
          id: `tree-${doc_id}`,
        })
      } else if (status === 'completed') {
        setGeneratingTreeFor((prev) => {
          const newSet = new Set(prev)
          newSet.delete(doc_id)
          return newSet
        })
        const details = num_nodes ? ` (${num_nodes} nodes, ${num_pages} pages)` : ''
        toast.success(message || `Tree generated successfully${details}!`, {
          id: `tree-${doc_id}`,
        })
      } else if (status === 'error') {
        setGeneratingTreeFor((prev) => {
          const newSet = new Set(prev)
          newSet.delete(doc_id)
          return newSet
        })
        toast.error(message || 'Tree generation failed', {
          id: `tree-${doc_id}`,
        })
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
    },
  })

  // Load documents on mount
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      const apiDocs = await documentsApi.getAll()
      const docs: Document[] = apiDocs.map((d) => ({
        id: d.id,
        name: d.filename,
        size: d.size,
        uploadDate: new Date(d.created_at),
        status: d.status,
        pageCount: d.page_count,
        treeGenerated: !!d.tree_id,
      }))
      setDocuments(docs)
    } catch (error) {
      console.error('Error loading documents:', error)
      toast.error('Failed to load documents')
    } finally {
      setIsLoading(false)
    }
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      const uploadToast = toast.loading(`Uploading ${file.name}...`)

      try {
        // Upload file to backend
        await documentsApi.upload(file)

        toast.success(`${file.name} uploaded successfully!`, { id: uploadToast })
      } catch (error: any) {
        console.error('Error uploading file:', error)
        toast.error(error.message || `Failed to upload ${file.name}`, { id: uploadToast })
      }
    }

    // Reload documents list to show all uploaded documents
    await loadDocuments()
  }, [])

  const handleGenerateTree = async (docId: number) => {
    const treeToast = toast.loading('Generating tree...')
    setGeneratingTreeFor((prev) => new Set(prev).add(docId))

    try {
      const result = await treeApi.generate(docId)
      toast.success(result.message, { id: treeToast })
    } catch (error: any) {
      console.error('Error generating tree:', error)
      toast.error(error.message || 'Failed to generate tree', { id: treeToast })
      setGeneratingTreeFor((prev) => {
        const newSet = new Set(prev)
        newSet.delete(docId)
        return newSet
      })
    }
  }

  const handleDeleteClick = (doc: Document) => {
    setDocumentToDelete(doc)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return

    try {
      await documentsApi.delete(documentToDelete.id)
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentToDelete.id))
      toast.success('Document deleted successfully')
      setDeleteDialogOpen(false)
      setDocumentToDelete(null)
    } catch (error: any) {
      console.error('Error deleting document:', error)
      toast.error(error.message || 'Failed to delete document')
    }
  }

  const handleViewTree = (doc: Document) => {
    setTreeViewerDocument({ id: doc.id, name: doc.name })
    setTreeViewerOpen(true)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  })

  const filteredDocuments = documents.filter((doc) =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'indexed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Documents</h1>
            <p className="text-sm text-muted-foreground">
              {documents.length} documents uploaded
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={loadDocuments} disabled={isLoading}>
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="icon"
              onClick={() => setViewMode('grid')}
            >
              <Grid size={18} />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="icon"
              onClick={() => setViewMode('list')}
            >
              <List size={18} />
            </Button>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="border-b px-6 py-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Upload Zone */}
        <div
          {...getRootProps()}
          className={cn(
            'mb-6 rounded-lg border-2 border-dashed p-8 text-center transition-colors cursor-pointer',
            isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          )}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <p className="text-sm font-medium">
            {isDragActive
              ? 'Drop the PDF files here...'
              : 'Drag & drop PDF files here, or click to select'}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Support for PDF files up to 100MB
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && documents.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium">No documents yet</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Upload your first PDF to get started
            </p>
          </div>
        )}

        {/* Documents Grid/List */}
        {!isLoading && viewMode === 'grid' && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredDocuments.map((doc) => (
              <Card
                key={doc.id}
                className={cn(
                  'cursor-pointer transition-all hover:bg-accent hover:shadow-md',
                  selectedDocument === String(doc.id) && 'ring-2 ring-primary bg-accent'
                )}
                onClick={() => {
                  onDocumentSelect(String(doc.id))
                  // Auto-generate tree if document is uploaded but not indexed
                  if (doc.status === 'uploaded' && !generatingTreeFor.has(doc.id)) {
                    handleGenerateTree(doc.id)
                  }
                }}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                    {getStatusIcon(doc.status)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CardTitle className="line-clamp-2 text-sm">
                    {doc.name}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    {doc.size ? formatBytes(doc.size) : 'Unknown size'}
                    {doc.pageCount && ` • ${doc.pageCount} pages`}
                  </CardDescription>
                  <CardDescription className="text-xs">
                    {doc.uploadDate ? formatDate(doc.uploadDate) : 'Just now'}
                  </CardDescription>

                  {/* Progress Bar */}
                  {generatingTreeFor.has(doc.id) && doc.progress !== undefined && (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Generating tree...</span>
                        <span className="font-medium">{Math.round(doc.progress)}%</span>
                      </div>
                      <Progress value={doc.progress} className="h-1" />
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    {!doc.treeGenerated && !generatingTreeFor.has(doc.id) && (
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleGenerateTree(doc.id)
                        }}
                      >
                        <TreePine size={14} className="mr-1" />
                        Generate Tree
                      </Button>
                    )}
                    {doc.treeGenerated && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleViewTree(doc)
                          }}
                        >
                          <Eye size={14} className="mr-1" />
                          View Tree
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1"
                          onClick={(e) => {
                            e.stopPropagation()
                            onStartChat()
                          }}
                        >
                          <Play size={14} className="mr-1" />
                          Chat
                        </Button>
                      </>
                    )}
                    {generatingTreeFor.has(doc.id) && (
                      <Button size="sm" className="flex-1" disabled>
                        <Loader2 size={14} className="mr-1 animate-spin" />
                        Generating...
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteClick(doc)
                      }}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* List View */}
        {!isLoading && viewMode === 'list' && (
          <div className="space-y-2">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className={cn(
                  'flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent cursor-pointer',
                  selectedDocument === String(doc.id) && 'ring-2 ring-primary'
                )}
                onClick={() => onDocumentSelect(String(doc.id))}
              >
                <div className="flex items-center gap-3 flex-1">
                  <FileText className="h-6 w-6 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="font-medium">{doc.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatBytes(doc.size)}
                      {doc.pageCount && ` • ${doc.pageCount} pages`} • {formatDate(doc.uploadDate)}
                    </p>
                    {generatingTreeFor.has(doc.id) && doc.progress !== undefined && (
                      <div className="mt-2 max-w-xs">
                        <Progress value={doc.progress} className="h-1" />
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(doc.status)}
                  {!doc.treeGenerated && !generatingTreeFor.has(doc.id) && (
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleGenerateTree(doc.id)
                      }}
                    >
                      <TreePine size={14} className="mr-1" />
                      Generate Tree
                    </Button>
                  )}
                  {doc.treeGenerated && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleViewTree(doc)
                        }}
                      >
                        <Eye size={14} className="mr-1" />
                        View Tree
                      </Button>
                      <Button
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onStartChat()
                        }}
                      >
                        <Play size={14} className="mr-1" />
                        Chat
                      </Button>
                    </>
                  )}
                  {generatingTreeFor.has(doc.id) && (
                    <Button size="sm" disabled>
                      <Loader2 size={14} className="mr-1 animate-spin" />
                      Generating...
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteClick(doc)
                    }}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <AlertDialogTitle>Delete Document</AlertDialogTitle>
            </div>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{documentToDelete?.name}</strong>?
              {documentToDelete?.treeGenerated && (
                <span className="block mt-2 text-amber-600">
                  This document has an indexed tree that will also be deleted.
                </span>
              )}
              <span className="block mt-2">
                This action cannot be undone.
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-red-500 hover:bg-red-600 focus:ring-red-500"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Tree Viewer */}
      {treeViewerDocument && (
        <TreeViewer
          open={treeViewerOpen}
          onOpenChange={setTreeViewerOpen}
          documentId={treeViewerDocument.id}
          documentName={treeViewerDocument.name}
        />
      )}
    </div>
  )
}
