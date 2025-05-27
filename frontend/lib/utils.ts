import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Utility function to clean and format LLM response
export function cleanLLMResponse(response: string): string {
  // Remove citation markers like [1], [2], etc. from the main text
  // but keep them for processing later
  let cleaned = response
  
  // Remove "Sources:" section and everything after it since we handle citations separately
  const sourcesIndex = cleaned.toLowerCase().indexOf('sources:')
  if (sourcesIndex !== -1) {
    cleaned = cleaned.substring(0, sourcesIndex).trim()
  }
  
  // Remove "Cited Sources:" section
  const citedSourcesIndex = cleaned.toLowerCase().indexOf('cited sources:')
  if (citedSourcesIndex !== -1) {
    cleaned = cleaned.substring(0, citedSourcesIndex).trim()
  }
  
  // Clean up extra whitespace
  cleaned = cleaned.replace(/\n\s*\n\s*\n/g, '\n\n').trim()
  
  return cleaned
}
