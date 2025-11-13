'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/sidebar'
import { ChatInterface } from '@/components/chat/chat-interface'
import { DocumentsPanel } from '@/components/documents/documents-panel'
import { SettingsDialog } from '@/components/settings/settings-dialog'

export default function Home() {
  const [currentView, setCurrentView] = useState<'chat' | 'documents'>('chat')
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onViewChange={setCurrentView}
        selectedDocument={selectedDocument}
        onDocumentSelect={setSelectedDocument}
        onSettingsClick={() => setIsSettingsOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        {currentView === 'chat' ? (
          <ChatInterface
            selectedDocument={selectedDocument}
            onNavigateToDocuments={() => setCurrentView('documents')}
          />
        ) : (
          <DocumentsPanel
            selectedDocument={selectedDocument}
            onDocumentSelect={setSelectedDocument}
            onStartChat={() => setCurrentView('chat')}
          />
        )}
      </main>

      {/* Settings Dialog */}
      <SettingsDialog
        open={isSettingsOpen}
        onOpenChange={setIsSettingsOpen}
      />
    </div>
  )
}