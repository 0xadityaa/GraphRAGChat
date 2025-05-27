"use client"

import { useState, useEffect, useRef, type FormEvent } from "react"
import { Bot, Paperclip, Mic, Send, User, Link2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ChatBubble, ChatBubbleAvatar, ChatBubbleMessage } from "@/components/ui/chat-bubble"
import { ChatInput } from "@/components/ui/chat-input"
import {
  ExpandableChat,
  ExpandableChatHeader,
  ExpandableChatBody,
  ExpandableChatFooter,
} from "@/components/ui/expandable-chat"
import { ChatMessageList } from "@/components/ui/chat-message-list"
import { chatApi, generateConversationId, formatCitationsForUI } from "@/lib/api"
import { cleanLLMResponse } from "@/lib/utils"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  sources?: Array<{ id: number; url: string; title: string }>
  timestamp: Date
  error?: boolean
}

export function ExpandableChatDemo() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      content: "Hey! I'm Smartie, your personal **MadeWithNestlé** assistant. Ask me anything, and I'll quickly search the entire site to find the answers you need!",
      sender: "ai",
      timestamp: new Date(),
    },
  ])

  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string>(generateConversationId())
  const [error, setError] = useState<string | null>(null)

  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Check backend health on mount
  useEffect(() => {
    console.log("Generated conversation ID:", conversationId)
    
    const checkHealth = async () => {
      try {
        const health = await chatApi.healthCheck()
        if (!health) {
          console.warn("Backend health check failed - API may be unavailable")
        } else {
          console.log("Backend is healthy:", health)
        }
      } catch (error) {
        console.error("Backend health check error:", error)
      }
    }
    checkHealth()
  }, [])

  // Debug logging for input state
  useEffect(() => {
    console.log("Input state debug:", {
      isLoading,
      conversationId,
      inputDisabled: isLoading || !conversationId,
      inputValue: input
    })
  }, [isLoading, conversationId, input])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    console.log("handleSubmit called with:", { input: input.trim(), isLoading, conversationId })
    
    if (!input.trim() || isLoading || !conversationId) {
      console.log("Submit blocked:", { 
        noInput: !input.trim(), 
        isLoading, 
        noConversationId: !conversationId 
      })
      return
    }

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content: input.trim(),
      sender: "user",
      timestamp: new Date(),
    }

    console.log("Starting API call with conversationId:", conversationId)
    
    // Add user message immediately
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setError(null)

    try {
      // Call the real API
      const response = await chatApi.sendMessage({
        question: userMessage.content,
        conversation_id: conversationId,
      })

      console.log("API response received, conversationId still:", conversationId)

      // Clean the response content
      const cleanedContent = cleanLLMResponse(response.answer)

      // Format citations for UI
      const formattedSources = formatCitationsForUI(response.citations)

      // Create AI response message
      const aiMessage: Message = {
        id: response.message_id,
        content: cleanedContent,
        sender: "ai",
        sources: formattedSources,
        timestamp: new Date(response.timestamp),
      }

      setMessages((prev) => [...prev, aiMessage])
      console.log("API Response processed:", {
        processingTime: response.processing_time,
        citationsCount: response.citations.length,
        conversationIdAfter: conversationId
      })

    } catch (error) {
      console.error("Chat API Error:", error)
      
      // Add error message
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        content: `Sorry, I encountered an error while processing your request. ${
          error instanceof Error ? error.message : "Please try again."
        }`,
        sender: "ai",
        timestamp: new Date(),
        error: true,
      }

      setMessages((prev) => [...prev, errorMessage])
      setError(error instanceof Error ? error.message : "Unknown error occurred")
    } finally {
      setIsLoading(false)
      console.log("handleSubmit finished, final state:", { 
        isLoading: false, 
        conversationId,
        inputWillBeDisabled: false || !conversationId
      })
    }
  }

  const handleClearConversation = async () => {
    try {
      if (conversationId) {
        await chatApi.deleteConversation(conversationId)
      }
      // Reset to initial state
      setMessages([
        {
      id: "welcome",
      content: "Hey! I'm Smartie, your personal **MadeWithNestlé** assistant. Ask me anything, and I'll quickly search the entire site to find the answers you need!",
      sender: "ai",
      timestamp: new Date(),
    }
      ])
      const newConversationId = generateConversationId()
      setConversationId(newConversationId)
      setError(null)
      console.log("Conversation cleared, new ID:", newConversationId)
    } catch (error) {
      console.error("Error clearing conversation:", error)
    }
  }

  // Refocus input after loading ends
  useEffect(() => {
    if (!isLoading && conversationId && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isLoading, conversationId])

  return (
    <ExpandableChat size="lg" position="bottom-right" icon={<Bot className="h-6 w-6" />}>
      <ExpandableChatHeader className="flex-col text-start justify-start">
        <div className="flex items-center justify-between w-full">
          <div>
            <h1 className="text-xl font-semibold">Smartie</h1>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearConversation}
            className="text-xs"
            disabled={isLoading}
          >
            Clear
          </Button>
        </div>
        {error && (
          <div className="mt-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive">
            Connection issue: {error}
          </div>
        )}
      </ExpandableChatHeader>

      <ExpandableChatBody>
        <ChatMessageList>
          {messages.map((message) => (
            <ChatBubble key={message.id} variant={message.sender === "user" ? "sent" : "received"}>
              <ChatBubbleAvatar
                className="h-8 w-8 shrink-0"
                fallback={message.sender === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              />
              <ChatBubbleMessage 
                variant={message.sender === "user" ? "sent" : "received"} 
                sources={message.sources}
                className={message.error ? "border border-destructive/20 bg-destructive/5" : undefined}
              >
                {message.content}
              </ChatBubbleMessage>
            </ChatBubble>
          ))}

          {isLoading && (
            <ChatBubble variant="received">
              <ChatBubbleAvatar
                className="h-8 w-8 shrink-0"
                fallback={<Bot className="h-4 w-4" />}
              />
              <ChatBubbleMessage isLoading />
            </ChatBubble>
          )}
        </ChatMessageList>
      </ExpandableChatBody>

      <ExpandableChatFooter>
        <form
          onSubmit={handleSubmit}
          className="relative rounded-lg border bg-background focus-within:ring-1 focus-within:ring-ring p-1"
        >
          <ChatInput
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about products, recipes, sustainability..."
            className="min-h-12 resize-none rounded-lg bg-background border-0 p-3 shadow-none focus-visible:ring-0"
            disabled={isLoading}
            ref={inputRef}
          />
          <div className="flex items-center p-3 pt-0 justify-between">
            <Button 
              type="submit" 
              size="sm" 
              className="ml-auto" 
              disabled={isLoading || !input.trim()}
            >
              <Send className="size-4" />
            </Button>
          </div>
        </form>
      </ExpandableChatFooter>
    </ExpandableChat>
  )
}
