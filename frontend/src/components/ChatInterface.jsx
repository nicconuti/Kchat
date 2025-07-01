import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertCircle, CheckCircle, Loader } from 'lucide-react';

function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Hello! I\'m your K-Array AI assistant. How can I help you today?',
      timestamp: new Date(),
      sources: []
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
      sources: []
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
          user_id: `user_${Date.now()}`
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.response || 'I apologize, but I encountered an issue processing your request.',
        timestamp: new Date(),
        sources: data.sources || [],
        confidence: data.confidence
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback response for demo purposes
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'I\'m currently in demo mode. The backend service is not yet connected. However, I can help you with information about K-Array products and services!',
        timestamp: new Date(),
        sources: [],
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="container" style={{ maxWidth: '800px', padding: 'var(--space-4)', height: '100%' }}>
      <div className="card" style={{ 
        height: 'calc(100vh - 200px)', 
        display: 'flex', 
        flexDirection: 'column',
        padding: 0
      }}>
        {/* Chat Header */}
        <div style={{
          padding: 'var(--space-4)',
          borderBottom: '1px solid var(--karray-border)',
          backgroundColor: 'var(--karray-surface)'
        }}>
          <div className="flex items-center gap-3">
            <div style={{
              width: '32px',
              height: '32px',
              backgroundColor: 'var(--karray-primary)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={16} color="white" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)' }}>K-Array Assistant</h3>
              <p style={{ 
                margin: 0, 
                fontSize: 'var(--font-size-sm)', 
                color: 'var(--karray-text-secondary)' 
              }}>
                Online • Powered by RAG Technology
              </p>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)'
        }}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div style={{
                width: '32px',
                height: '32px',
                backgroundColor: message.type === 'user' ? 'var(--karray-accent)' : 'var(--karray-primary)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {message.type === 'user' ? (
                  <User size={16} color="white" />
                ) : (
                  <Bot size={16} color="white" />
                )}
              </div>

              {/* Message Content */}
              <div style={{
                maxWidth: '70%',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)'
              }}>
                <div
                  className="card"
                  style={{
                    padding: 'var(--space-3)',
                    backgroundColor: message.type === 'user' 
                      ? 'var(--karray-primary)' 
                      : message.isError 
                        ? 'rgb(239 68 68 / 0.1)'
                        : 'var(--karray-surface)',
                    color: message.type === 'user' ? 'white' : 'var(--karray-text-primary)',
                    border: message.isError ? '1px solid var(--karray-error)' : '1px solid var(--karray-border)'
                  }}
                >
                  <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </p>
                  
                  {/* Confidence Indicator */}
                  {message.confidence && (
                    <div className="flex items-center gap-2 mt-2">
                      {message.confidence > 0.7 ? (
                        <CheckCircle size={14} color="var(--karray-success)" />
                      ) : (
                        <AlertCircle size={14} color="var(--karray-warning)" />
                      )}
                      <span style={{ 
                        fontSize: 'var(--font-size-xs)',
                        color: 'var(--karray-text-secondary)'
                      }}>
                        Confidence: {Math.round(message.confidence * 100)}%
                      </span>
                    </div>
                  )}

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div style={{ marginTop: 'var(--space-2)' }}>
                      <div style={{
                        fontSize: 'var(--font-size-xs)',
                        color: 'var(--karray-text-secondary)',
                        marginBottom: 'var(--space-1)'
                      }}>
                        Sources:
                      </div>
                      {message.sources.map((source, idx) => (
                        <div key={idx} style={{
                          fontSize: 'var(--font-size-xs)',
                          padding: 'var(--space-1)',
                          backgroundColor: 'rgba(0,0,0,0.05)',
                          borderRadius: 'var(--radius-sm)',
                          marginBottom: 'var(--space-1)'
                        }}>
                          {source.title || source.url || `Source ${idx + 1}`}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Timestamp */}
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--karray-text-secondary)',
                  textAlign: message.type === 'user' ? 'right' : 'left'
                }}>
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3">
              <div style={{
                width: '32px',
                height: '32px',
                backgroundColor: 'var(--karray-primary)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Bot size={16} color="white" />
              </div>
              <div className="card" style={{
                padding: 'var(--space-3)',
                backgroundColor: 'var(--karray-surface)'
              }}>
                <div className="flex items-center gap-2">
                  <Loader size={16} className="loading" />
                  <span style={{ color: 'var(--karray-text-secondary)' }}>
                    Thinking...
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: 'var(--space-4)',
          borderTop: '1px solid var(--karray-border)',
          backgroundColor: 'var(--karray-surface)'
        }}>
          <div className="flex gap-3 items-end">
            <textarea
              ref={inputRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about K-Array products, services, or technical support..."
              className="form-input form-textarea"
              style={{
                flex: 1,
                minHeight: '44px',
                maxHeight: '120px',
                resize: 'none'
              }}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputText.trim() || isLoading}
              className="btn btn-primary"
              style={{
                padding: 'var(--space-3)',
                opacity: (!inputText.trim() || isLoading) ? 0.5 : 1
              }}
            >
              <Send size={16} />
            </button>
          </div>
          
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--karray-text-secondary)',
            marginTop: 'var(--space-2)',
            textAlign: 'center'
          }}>
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;