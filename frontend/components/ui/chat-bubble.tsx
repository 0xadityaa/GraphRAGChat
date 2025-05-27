"use client"

import type * as React from "react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { MessageLoading } from "@/components/ui/message-loading"
import { MarkdownRenderer } from "@/components/ui/markdown-renderer"

interface ChatBubbleProps {
  variant?: "sent" | "received"
  layout?: "default" | "ai"
  className?: string
  children: React.ReactNode
}

export function ChatBubble({ variant = "received", layout = "default", className, children }: ChatBubbleProps) {
  return (
    <div className={cn("flex items-start gap-2 mb-4", variant === "sent" && "flex-row-reverse", className)}>
      {children}
    </div>
  )
}

interface Source {
  id: number
  url: string
  title: string
}

interface ChatBubbleMessageProps {
  variant?: "sent" | "received"
  isLoading?: boolean
  className?: string
  children?: React.ReactNode
  sources?: Source[]
}

export function ChatBubbleMessage({
  variant = "received",
  isLoading,
  className,
  children,
  sources,
}: ChatBubbleMessageProps) {
  const handleSourceClick = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer")
  }

  return (
    <div
      className={cn(
        "rounded-lg p-3 max-w-[80%]",
        variant === "sent" ? "bg-primary text-primary-foreground" : "bg-muted",
        className,
      )}
    >
      {isLoading ? (
        <div className="flex items-center space-x-2">
          <MessageLoading />
        </div>
      ) : (
        <div>
          {variant === "sent" ? (
            <div className="text-sm">{children}</div>
          ) : (
            <MarkdownRenderer content={children as string} sources={sources} onSourceClick={handleSourceClick} />
          )}
        </div>
      )}
    </div>
  )
}

interface ChatBubbleAvatarProps {
  src?: string
  fallback?: React.ReactNode
  className?: string
}

export function ChatBubbleAvatar({ src, fallback = "AI", className }: ChatBubbleAvatarProps) {
  return (
    <Avatar className={cn("h-8 w-8", className)}>
      {src && <AvatarImage src={src || "/placeholder.svg"} />}
      <AvatarFallback>{fallback}</AvatarFallback>
    </Avatar>
  )
}

interface ChatBubbleActionProps {
  icon?: React.ReactNode
  onClick?: () => void
  className?: string
}

export function ChatBubbleAction({ icon, onClick, className }: ChatBubbleActionProps) {
  return (
    <Button variant="ghost" size="icon" className={cn("h-6 w-6", className)} onClick={onClick}>
      {icon}
    </Button>
  )
}

export function ChatBubbleActionWrapper({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return <div className={cn("flex items-center gap-1 mt-2", className)}>{children}</div>
}
