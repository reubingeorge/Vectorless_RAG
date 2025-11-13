'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import {
  MessageSquare,
  FileText,
  Settings,
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  Clock,
  Star,
} from 'lucide-react'

interface Conversation {
  id: string
  title: string
  timestamp: Date
  preview: string
  documentId?: string
}

interface SidebarProps {
  currentView: 'chat' | 'documents'
  onViewChange: (view: 'chat' | 'documents') => void
  selectedDocument: string | null
  onDocumentSelect: (docId: string | null) => void
  onSettingsClick: () => void
}

export function Sidebar({
  currentView,
  onViewChange,
  selectedDocument,
  onDocumentSelect,
  onSettingsClick,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  // TODO: Load conversations from backend when chat service is implemented
  const [conversations, setConversations] = useState<Conversation[]>([])

  const groupConversationsByDate = (convos: Conversation[]) => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const lastWeek = new Date(today)
    lastWeek.setDate(lastWeek.getDate() - 7)

    const groups: { [key: string]: Conversation[] } = {
      Today: [],
      Yesterday: [],
      'Last 7 Days': [],
      Older: [],
    }

    convos.forEach((convo) => {
      const convoDate = new Date(convo.timestamp)
      if (convoDate.toDateString() === today.toDateString()) {
        groups['Today'].push(convo)
      } else if (convoDate.toDateString() === yesterday.toDateString()) {
        groups['Yesterday'].push(convo)
      } else if (convoDate > lastWeek) {
        groups['Last 7 Days'].push(convo)
      } else {
        groups['Older'].push(convo)
      }
    })

    return groups
  }

  const filteredConversations = conversations.filter((convo) =>
    convo.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const groupedConversations = groupConversationsByDate(filteredConversations)

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-background transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b px-4">
        {!isCollapsed && (
          <h2 className="text-lg font-semibold">Indexer</h2>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </Button>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button
          className={cn('w-full justify-start', isCollapsed && 'justify-center')}
          onClick={() => onViewChange('chat')}
        >
          <Plus size={18} className={cn(!isCollapsed && 'mr-2')} />
          {!isCollapsed && 'New Chat'}
        </Button>
      </div>

      {/* View Switcher */}
      <div className="flex gap-2 px-4 pb-4">
        <Button
          variant={currentView === 'chat' ? 'default' : 'outline'}
          size="sm"
          className={cn('flex-1', isCollapsed && 'px-0')}
          onClick={() => onViewChange('chat')}
        >
          <MessageSquare size={16} className={cn(!isCollapsed && 'mr-2')} />
          {!isCollapsed && 'Chat'}
        </Button>
        <Button
          variant={currentView === 'documents' ? 'default' : 'outline'}
          size="sm"
          className={cn('flex-1', isCollapsed && 'px-0')}
          onClick={() => onViewChange('documents')}
        >
          <FileText size={16} className={cn(!isCollapsed && 'mr-2')} />
          {!isCollapsed && 'Docs'}
        </Button>
      </div>

      {/* Search */}
      {!isCollapsed && (
        <div className="px-4 pb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4">
        {!isCollapsed ? (
          Object.entries(groupedConversations).map(([group, convos]) => {
            if (convos.length === 0) return null
            return (
              <div key={group} className="mb-4">
                <h3 className="mb-2 text-xs font-semibold text-muted-foreground">
                  {group}
                </h3>
                <div className="space-y-1">
                  {convos.map((convo) => (
                    <button
                      key={convo.id}
                      className="w-full rounded-md px-2 py-2 text-left text-sm hover:bg-accent"
                    >
                      <div className="flex items-center gap-2">
                        {convo.documentId ? (
                          <FileText size={14} className="text-muted-foreground" />
                        ) : (
                          <MessageSquare size={14} className="text-muted-foreground" />
                        )}
                        <span className="flex-1 truncate font-medium">
                          {convo.title}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {convo.preview}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            )
          })
        ) : (
          <div className="space-y-2">
            {filteredConversations.slice(0, 5).map((convo) => (
              <Button
                key={convo.id}
                variant="ghost"
                size="icon"
                className="w-full"
              >
                {convo.documentId ? (
                  <FileText size={18} />
                ) : (
                  <MessageSquare size={18} />
                )}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="border-t p-4">
        <Button
          variant="ghost"
          className={cn('w-full justify-start', isCollapsed && 'justify-center')}
          onClick={onSettingsClick}
        >
          <Settings size={18} className={cn(!isCollapsed && 'mr-2')} />
          {!isCollapsed && 'Settings'}
        </Button>
      </div>
    </aside>
  )
}