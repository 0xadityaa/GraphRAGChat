"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Link2 } from "lucide-react"

interface Source {
  id: number
  url: string
  title: string
}

interface MarkdownRendererProps {
  content: string
  sources?: Source[]
  onSourceClick?: (url: string) => void
}

export function MarkdownRenderer({ content, sources, onSourceClick }: MarkdownRendererProps) {
  // Process content to replace source references with clickable links
  const processedContent = content.replace(/\[(\d+)\]/g, (match, num) => {
    const sourceNum = Number.parseInt(num)
    const source = sources?.find((s) => s.id === sourceNum)
    if (source && onSourceClick) {
      // Keep the [number] format in the text, but make it non-clickable here
      // The clickable sources will be rendered separately below.
      return `[${num}]`
    }
    return match
  })

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Custom styling for markdown elements
          h1: ({ children }) => <h1 className="text-lg font-bold mb-2 text-foreground">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-semibold mb-2 text-foreground">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold mb-1 text-foreground">{children}</h3>,
          p: ({ children }) => <p className="mb-2 text-foreground leading-relaxed">{children}</p>,
          ul: ({ children }) => <ul className="mb-2 ml-4 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="mb-2 ml-4 space-y-1 list-decimal">{children}</ol>,
          li: ({ children }) => <li className="text-foreground">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
          em: ({ children }) => <em className="italic text-foreground">{children}</em>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-muted-foreground/30 pl-4 italic text-muted-foreground mb-2">
              {children}
            </blockquote>
          ),
          code: ({ children }) => (
            <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono text-foreground">{children}</code>
          ),
          pre: ({ children }) => <pre className="bg-muted p-3 rounded-md overflow-x-auto mb-2">{children}</pre>,
        }}
      >
        {processedContent}
      </ReactMarkdown>

      {/* Render source links with new styling */}
      {sources && sources.length > 0 && (
        <div className="mt-4 pt-3 border-t border-border/50">
          <h4 className="text-xs font-semibold text-muted-foreground mb-2">Sources:</h4>
          <div className="flex flex-wrap gap-2">
            {sources.map((source) => (
              <button
                key={source.id}
                onClick={() => onSourceClick?.(source.url)}
                className="inline-flex items-center text-xs bg-background border border-border hover:bg-muted/80 hover:border-muted-foreground/30 px-2.5 py-1 rounded-full transition-colors group text-muted-foreground hover:text-foreground shadow-sm hover:shadow"
                title={source.url} // Show full URL on hover
              >
                <Link2 className="h-3 w-3 mr-1.5 text-muted-foreground group-hover:text-primary transition-colors" />
                <span className="truncate max-w-[150px] group-hover:max-w-none transition-all duration-300">
                  {source.title} [{source.id}]
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
