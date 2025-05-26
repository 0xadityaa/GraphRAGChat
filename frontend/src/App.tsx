import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageCircle, Send, X, ExternalLink } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  citations?: string[];
  timestamp: Date;
}

interface ChatResponse {
  answer: string;
  citations: string[];
  conversation_id: string;
  message_id: string;
  timestamp: string;
  processing_time: number;
}

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize conversation ID
  useEffect(() => {
    let storedConversationId = localStorage.getItem('graphrag_conversation_id');
    if (!storedConversationId) {
      storedConversationId = `conv_${uuidv4()}`;
      localStorage.setItem('graphrag_conversation_id', storedConversationId);
    }
    setConversationId(storedConversationId);
    
    // Load chat history from localStorage
    const storedMessages = localStorage.getItem('graphrag_chat_history');
    if (storedMessages) {
      try {
        const parsedMessages = JSON.parse(storedMessages);
        // Convert timestamp strings back to Date objects
        const messagesWithDates = parsedMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(messagesWithDates);
      } catch (error) {
        console.error('Error parsing stored messages:', error);
      }
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Save messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('graphrag_chat_history', JSON.stringify(messages));
    }
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: uuidv4(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage.content,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      const botMessage: Message = {
        id: data.message_id,
        type: 'bot',
        content: data.answer,
        citations: data.citations,
        timestamp: new Date(data.timestamp),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: uuidv4(),
        type: 'bot',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('graphrag_chat_history');
    // Generate new conversation ID
    const newConversationId = `conv_${uuidv4()}`;
    setConversationId(newConversationId);
    localStorage.setItem('graphrag_conversation_id', newConversationId);
  };

  return (
    <div className="app">
      {/* Full-screen background */}
      <div className="background" style={{
        backgroundImage: 'url(/bg.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        width: '100vw',
        height: '100vh',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 0,
      }} />
      
      {/* Content overlay */}
      <div className="content-overlay">
        {/* Chat toggle button */}
        {!isOpen && (
          <button
            onClick={() => setIsOpen(true)}
            className="chat-toggle-btn"
            aria-label="Open chat"
          >
            <MessageCircle size={24} />
          </button>
        )}

        {/* Chat popup */}
        {isOpen && (
          <div className="chat-popup">
            <div className="chat-header">
              <h3>Smartie</h3>
              <div className="chat-controls">
                <button onClick={clearChat} className="clear-btn" title="Clear chat">
                  Clear
                </button>
                <button onClick={() => setIsOpen(false)} className="close-btn" aria-label="Close chat">
                  <X size={20} />
                </button>
              </div>
            </div>

            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="welcome-message">
                  <p>👋 Hello! I'm Smartie, your Nestlé knowledge assistant. Ask me anything about Nestlé company, products, recipes, stories, or any other information!</p>
                </div>
              )}
              
              {messages.map((message) => (
                <div key={message.id} className={`message ${message.type}`}>
                  <div className="message-content">
                    {message.type === 'user' ? (
                      <p>{message.content}</p>
                    ) : (
                      <div className="bot-message">
                        <ReactMarkdown 
                          className="markdown-content"
                          components={{
                            h1: ({children}) => <h1 className="md-h1">{children}</h1>,
                            h2: ({children}) => <h2 className="md-h2">{children}</h2>,
                            h3: ({children}) => <h3 className="md-h3">{children}</h3>,
                            p: ({children}) => <p className="md-p">{children}</p>,
                            ul: ({children}) => <ul className="md-ul">{children}</ul>,
                            ol: ({children}) => <ol className="md-ol">{children}</ol>,
                            li: ({children}) => <li className="md-li">{children}</li>,
                            code: ({children}) => <code className="md-code">{children}</code>,
                            pre: ({children}) => <pre className="md-pre">{children}</pre>,
                            blockquote: ({children}) => <blockquote className="md-blockquote">{children}</blockquote>,
                            strong: ({children}) => <strong className="md-strong">{children}</strong>,
                            em: ({children}) => <em className="md-em">{children}</em>,
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                        {message.citations && message.citations.length > 0 && (
                          <div className="citations">
                            <span className="citations-label">Sources:</span>
                            <div className="citations-badges">
                              {message.citations.map((citation, index) => (
                                <a
                                  key={index}
                                  href={citation}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="citation-badge"
                                  title={citation}
                                >
                                  {index + 1}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="message-time">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="message bot">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about Nestle..."
                className="input-field"
                rows={1}
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="send-btn"
                aria-label="Send message"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
