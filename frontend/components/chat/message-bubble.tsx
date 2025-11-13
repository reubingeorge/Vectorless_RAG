'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Button } from '@/components/ui/button'
import { Copy, Check, User, Bot, DollarSign } from 'lucide-react'
import { cn, formatTime } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isStreaming?: boolean
  documentContext?: string
  cost?: number
}

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const handleCopyCode = async (code: string) => {
    await navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'message-fade-in flex gap-3',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Bot size={16} />
        </div>
      )}

      <div
        className={cn(
          'group relative max-w-[80%] rounded-lg px-4 py-3 shadow-sm',
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
        )}
      >
        {/* Cost Badge */}
        {message.cost && !isUser && (
          <div className="absolute -right-2 -top-2 flex items-center gap-1 rounded-full bg-background border px-2 py-0.5 text-xs text-muted-foreground shadow-sm">
            <DollarSign size={10} />
            {message.cost.toFixed(3)}
          </div>
        )}

        {/* Message Content */}
        <div className={cn(
          'prose prose-sm max-w-none dark:prose-invert',
          isUser && 'text-white'
        )}>
          {isUser ? (
            <p className="m-0 whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '')
                  const code = String(children).replace(/\n$/, '')

                  return !inline && match ? (
                    <div className="relative my-4">
                      <div className="absolute right-2 top-2 z-10 opacity-0 transition-opacity group-hover:opacity-100">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 bg-gray-700 hover:bg-gray-600"
                          onClick={() => handleCopyCode(code)}
                        >
                          {copiedCode === code ? (
                            <Check size={14} className="text-green-400" />
                          ) : (
                            <Copy size={14} className="text-gray-300" />
                          )}
                        </Button>
                      </div>
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        className="!m-0 !rounded-lg"
                        {...props}
                      >
                        {code}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                      {children}
                    </code>
                  )
                },
                p({ children }) {
                  return <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
                },
                ul({ children }) {
                  return <ul className="mb-3 list-disc pl-6 space-y-1">{children}</ul>
                },
                ol({ children }) {
                  return <ol className="mb-3 list-decimal pl-6 space-y-1">{children}</ol>
                },
                li({ children }) {
                  return <li className="leading-relaxed">{children}</li>
                },
                h1({ children }) {
                  return <h1 className="text-2xl font-bold mt-4 mb-2">{children}</h1>
                },
                h2({ children }) {
                  return <h2 className="text-xl font-bold mt-3 mb-2">{children}</h2>
                },
                h3({ children }) {
                  return <h3 className="text-lg font-semibold mt-2 mb-1">{children}</h3>
                },
                blockquote({ children }) {
                  return <blockquote className="border-l-4 border-blue-500 pl-4 italic my-3">{children}</blockquote>
                },
                table({ children }) {
                  return <div className="overflow-x-auto my-4"><table className="min-w-full border-collapse">{children}</table></div>
                },
                th({ children }) {
                  return <th className="border border-gray-300 dark:border-gray-600 px-4 py-2 bg-gray-50 dark:bg-gray-700 font-semibold">{children}</th>
                },
                td({ children }) {
                  return <td className="border border-gray-300 dark:border-gray-600 px-4 py-2">{children}</td>
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Timestamp */}
        <div className={cn(
          'mt-2 text-xs opacity-60',
          isUser ? 'text-white' : 'text-gray-500 dark:text-gray-400'
        )}>
          {formatTime(message.timestamp)}
        </div>

        {/* Streaming Indicator */}
        {message.isStreaming && (
          <div className="mt-2">
            <span className="inline-block h-2 w-2 animate-pulse-subtle rounded-full bg-current" />
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
          <User size={16} />
        </div>
      )}
    </div>
  )
}