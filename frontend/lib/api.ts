// API client for GraphRAG Chatbot backend
// To configure the API URL, create a .env.local file with:
// NEXT_PUBLIC_API_URL=http://localhost:8000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatRequest {
  question: string
  conversation_id: string
}

export interface ChatResponse {
  answer: string
  citations: string[]
  conversation_id: string
  message_id: string
  timestamp: string
  processing_time: number
}

export interface ApiError {
  error: string
  conversation_id: string
  timestamp: string
  processing_time?: number
}

export class ChatApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail?.error || 
          errorData.detail || 
          `HTTP ${response.status}: ${response.statusText}`
        )
      }

      const data: ChatResponse = await response.json()
      return data
    } catch (error) {
      console.error('API Error:', error)
      throw error instanceof Error ? error : new Error('Unknown API error')
    }
  }

  async getConversationHistory(conversationId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/conversations/${conversationId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          return { conversation_id: conversationId, messages: [], message_count: 0 }
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching conversation history:', error)
      throw error instanceof Error ? error : new Error('Unknown API error')
    }
  }

  async deleteConversation(conversationId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/conversations/${conversationId}`, {
        method: 'DELETE',
      })

      if (!response.ok && response.status !== 404) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return response.status !== 404 ? await response.json() : null
    } catch (error) {
      console.error('Error deleting conversation:', error)
      throw error instanceof Error ? error : new Error('Unknown API error')
    }
  }

  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      return response.ok ? await response.json() : null
    } catch (error) {
      console.error('Health check failed:', error)
      return null
    }
  }
}

// Singleton instance
export const chatApi = new ChatApiClient()

// Utility function to generate conversation IDs
export function generateConversationId(): string {
  return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Utility function to format citations for UI
export function formatCitationsForUI(citations: string[]): Array<{ id: number; url: string; title: string }> {
  return citations.map((url, index) => ({
    id: index + 1,
    url: url,
    title: extractTitleFromUrl(url) || `Source ${index + 1}`
  }))
}

// Extract a readable title from URL
function extractTitleFromUrl(url: string): string | null {
  try {
    const urlObj = new URL(url)
    const pathname = urlObj.pathname
    
    // Remove leading slash and split by slashes
    const segments = pathname.replace(/^\//, '').split('/')
    
    // Get the last meaningful segment
    const lastSegment = segments[segments.length - 1] || segments[segments.length - 2]
    
    if (!lastSegment) return null
    
    // Convert to readable format
    return lastSegment
      .replace(/[-_]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .trim()
  } catch {
    return null
  }
} 