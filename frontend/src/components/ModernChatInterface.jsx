import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  AlertCircle, 
  CheckCircle, 
  Loader2, 
  ChevronDown, 
  ChevronUp,
  Clock,
  Search,
  MessageSquare,
  Zap,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Maximize2,
  Minimize2,
  Settings,
  Sparkles,
  FileText,
  ExternalLink
} from 'lucide-react';

// Modern gradient backgrounds
const gradients = {
  primary: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
  secondary: 'linear-gradient(135deg, #ff3366 0%, #ff6b9d 100%)',
  success: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
  karray: 'linear-gradient(135deg, #0a0a0a 0%, #1e1e1e 100%)',
  accent: 'linear-gradient(135deg, #ff3366 0%, #ff6b9d 100%)'
};

// Enhanced Animation Keyframes
const animations = `
  @keyframes slideInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slideInLeft {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  @keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
  }

  @keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
    40%, 43% { transform: translate3d(0,-8px,0); }
    70% { transform: translate3d(0,-4px,0); }
    90% { transform: translate3d(0,-2px,0); }
  }

  @keyframes typing {
    0% { width: 0; }
    100% { width: 100%; }
  }

  .message-enter {
    animation: slideInUp 0.4s ease-out;
  }

  .user-message-enter {
    animation: slideInLeft 0.4s ease-out;
  }

  .typing-indicator {
    animation: pulse 1.5s ease-in-out infinite;
  }

  .shimmer-effect {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200px 100%;
    animation: shimmer 2s infinite;
  }

  .bounce-effect {
    animation: bounce 2s infinite;
  }
`;

// Modern Button Component
function ModernButton({ children, variant = 'primary', size = 'md', disabled = false, loading = false, onClick, ...props }) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: '12px',
    border: 'none',
    fontWeight: '600',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative',
    overflow: 'hidden'
  };

  const variants = {
    primary: {
      background: gradients.primary,
      color: 'white',
      boxShadow: '0 4px 14px 0 rgba(59, 130, 246, 0.3)',
      border: '1px solid transparent'
    },
    secondary: {
      background: 'white',
      color: '#0a0a0a',
      border: '1px solid #e2e8f0',
      boxShadow: '0 2px 8px 0 rgba(0, 0, 0, 0.05)'
    },
    ghost: {
      background: 'transparent',
      color: '#525252',
      border: '1px solid transparent'
    },
    accent: {
      background: gradients.accent,
      color: 'white',
      boxShadow: '0 4px 14px 0 rgba(255, 51, 102, 0.3)',
      border: '1px solid transparent'
    }
  };

  const sizes = {
    sm: { padding: '8px 16px', fontSize: '14px' },
    md: { padding: '12px 24px', fontSize: '16px' },
    lg: { padding: '16px 32px', fontSize: '18px' }
  };

  const hoverEffect = !disabled && !loading ? {
    transform: 'translateY(-2px)',
    boxShadow: '0 8px 24px 0 rgba(0, 0, 0, 0.15)'
  } : {};

  return (
    <button
      style={{
        ...baseStyles,
        ...variants[variant],
        ...sizes[size],
        opacity: disabled ? 0.5 : 1
      }}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          Object.assign(e.target.style, hoverEffect);
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = variants[variant].boxShadow || '0 2px 8px 0 rgba(0, 0, 0, 0.05)';
        }
      }}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />}
      {children}
    </button>
  );
}

// Enhanced Message Card Component
function MessageCard({ message, onCopy, onFeedback }) {
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const isUser = message.type === 'user';
  const hasError = message.isError;

  const cardStyle = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '16px',
    marginBottom: '24px',
    padding: '20px',
    borderRadius: '20px',
    background: isUser 
      ? gradients.primary
      : hasError 
        ? 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)'
        : 'white',
    boxShadow: isUser 
      ? '0 4px 20px rgba(59, 130, 246, 0.15)'
      : hasError
        ? '0 4px 20px rgba(239, 68, 68, 0.15)' 
        : '0 4px 20px rgba(0, 0, 0, 0.08)',
    border: isUser 
      ? '1px solid rgba(59, 130, 246, 0.2)'
      : hasError
        ? '1px solid rgba(239, 68, 68, 0.2)'
        : '1px solid rgba(226, 232, 240, 0.6)',
    position: 'relative',
    overflow: 'hidden',
    transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    animation: 'slideInUp 0.4s ease-out'
  };

  const avatarStyle = {
    width: '44px',
    height: '44px',
    borderRadius: '14px',
    background: isUser ? 'rgba(255, 255, 255, 0.2)' : gradients.karray,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    backdropFilter: 'blur(10px)'
  };

  return (
    <div 
      style={cardStyle}
      onMouseEnter={() => {
        setIsHovered(true);
        setShowActions(true);
      }}
      onMouseLeave={() => {
        setIsHovered(false);
        setShowActions(false);
      }}
    >
      {/* Glass morphism effect */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: isUser ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.02)',
        backdropFilter: 'blur(10px)',
        borderRadius: '20px',
        pointerEvents: 'none'
      }} />

      <div style={avatarStyle}>
        {isUser ? 
          <User size={20} color="white" /> : 
          <Bot size={20} color="white" />
        }
      </div>
      
      <div style={{ flex: 1, position: 'relative', zIndex: 1 }}>
        <div style={{
          color: isUser ? 'white' : '#1a1a1a',
          lineHeight: 1.6,
          fontSize: '16px',
          fontWeight: isUser ? '500' : '400'
        }}>
          {message.isStreaming && (
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px',
              fontSize: '14px',
              color: isUser ? 'rgba(255, 255, 255, 0.8)' : '#666',
              fontWeight: '500'
            }}>
              <Sparkles size={14} style={{ animation: 'pulse 1.5s ease-in-out infinite' }} />
              K-Array AI sta pensando...
            </div>
          )}
          
          {message.content}
          
          {message.isStreaming && (
            <span style={{
              marginLeft: '2px',
              animation: 'pulse 1s infinite',
              color: isUser ? 'rgba(255, 255, 255, 0.8)' : '#666'
            }}>●</span>
          )}
        </div>
        
        {/* Enhanced Sources Display */}
        {message.sources && message.sources.length > 0 && (
          <div style={{
            marginTop: '16px',
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '12px',
            border: '1px solid rgba(0, 0, 0, 0.05)',
            backdropFilter: 'blur(10px)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
              fontSize: '14px',
              fontWeight: '600',
              color: '#1a1a1a'
            }}>
              <FileText size={16} />
              Fonti documentali
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {message.sources.map((source, index) => (
                <div key={index} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  background: 'rgba(102, 126, 234, 0.05)',
                  borderRadius: '8px',
                  fontSize: '13px',
                  color: '#4f46e5',
                  transition: 'all 0.2s ease'
                }}>
                  <ExternalLink size={14} />
                  {typeof source === 'string' ? source : source.snippet}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Message Actions */}
        {showActions && !isUser && (
          <div style={{
            position: 'absolute',
            top: '-10px',
            right: '0',
            display: 'flex',
            gap: '8px',
            animation: 'fadeIn 0.3s ease-out'
          }}>
            <button
              onClick={() => onCopy && onCopy(message.content)}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.9)',
                color: '#666',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'white';
                e.target.style.color = '#1a1a1a';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.9)';
                e.target.style.color = '#666';
              }}
            >
              <Copy size={14} />
            </button>
            <button
              onClick={() => onFeedback && onFeedback(message, 'positive')}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.9)',
                color: '#10b981',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.2s ease'
              }}
            >
              <ThumbsUp size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Enhanced Reasoning Panel
function ModernReasoningPanel({ steps, isExpanded, onToggle }) {
  return (
    <div style={{
      marginTop: '16px',
      borderRadius: '16px',
      overflow: 'hidden',
      border: '1px solid rgba(102, 126, 234, 0.2)',
      background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
      backdropFilter: 'blur(10px)'
    }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          padding: '16px 20px',
          background: 'transparent',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          fontSize: '15px',
          fontWeight: '600',
          color: '#4f46e5',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(102, 126, 234, 0.1)';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'transparent';
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Zap size={18} />
          Processo di ragionamento ({steps.length} passi)
        </span>
        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>
      
      {isExpanded && (
        <div style={{
          padding: '20px',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {steps.map((step, index) => (
              <div key={index} style={{
                display: 'flex',
                gap: '16px',
                padding: '16px',
                background: 'white',
                borderRadius: '12px',
                border: '1px solid rgba(0, 0, 0, 0.05)',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                animation: `slideInUp 0.4s ease-out ${index * 0.1}s both`
              }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: gradients.primary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: '600',
                  flexShrink: 0
                }}>
                  {index + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '15px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    marginBottom: '4px'
                  }}>
                    {step.step}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    color: '#666',
                    lineHeight: 1.5
                  }}>
                    {step.message}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#999',
                    marginTop: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <Clock size={12} />
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Main Modern Chat Interface
export default function ModernChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState([]);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Sample welcome message
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      type: 'assistant',
      content: 'Ciao! Sono l\'assistente K-Array AI. Posso aiutarti con informazioni sui prodotti K-Array, supporto tecnico per K-Framework 3, e molto altro. Come posso assisterti oggi?',
      timestamp: new Date().toISOString(),
      isStreaming: false
    }]);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setReasoningSteps([]);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage.content,
          include_reasoning: true 
        })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
        sources: []
      };

      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'reasoning') {
                setReasoningSteps(prev => [...prev, data.data]);
              } else if (data.type === 'response_chunk') {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { ...msg, content: msg.content + data.data.content }
                    : msg
                ));
              } else if (data.type === 'response_complete') {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { 
                        ...msg, 
                        isStreaming: false, 
                        sources: data.data.sources || [],
                        confidence: data.data.confidence 
                      }
                    : msg
                ));
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessage.id 
          ? { 
              ...msg, 
              content: 'Mi dispiace, si è verificato un errore. Riprova tra poco.', 
              isError: true, 
              isStreaming: false 
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };

  const handleFeedback = (message, type) => {
    console.log('Feedback:', { message: message.id, type });
    // Could implement feedback API call here
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <style>{animations}</style>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        height: isFullscreen ? '100vh' : 'calc(100vh - 60px)',
        maxWidth: '1200px',
        margin: '0 auto',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Enhanced Header */}
        <div style={{
          padding: '20px 24px',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '14px',
              background: gradients.karray,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
            }}>
              <MessageSquare size={24} color="white" />
            </div>
            <div>
              <h1 style={{
                fontSize: '24px',
                fontWeight: '700',
                margin: 0,
                background: gradients.karray,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                K-Array AI Assistant
              </h1>
              <p style={{
                fontSize: '14px',
                color: '#666',
                margin: 0
              }}>
                Assistenza intelligente per prodotti e servizi K-Array
              </p>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <ModernButton
              variant="ghost"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </ModernButton>
            <ModernButton variant="ghost" size="sm">
              <Settings size={16} />
            </ModernButton>
          </div>
        </div>

        {/* Enhanced Messages Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          background: 'transparent'
        }}>
          {messages.map((message) => (
            <MessageCard
              key={message.id}
              message={message}
              onCopy={handleCopy}
              onFeedback={handleFeedback}
            />
          ))}
          
          {reasoningSteps.length > 0 && (
            <ModernReasoningPanel
              steps={reasoningSteps}
              isExpanded={reasoningExpanded}
              onToggle={() => setReasoningExpanded(!reasoningExpanded)}
            />
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Enhanced Input Area */}
        <div style={{
          padding: '24px',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(0, 0, 0, 0.05)'
        }}>
          <div style={{
            display: 'flex',
            gap: '16px',
            alignItems: 'stretch',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            <div style={{
              flex: 1,
              position: 'relative',
              borderRadius: '20px',
              background: 'white',
              border: '2px solid rgba(59, 130, 246, 0.1)',
              transition: 'all 0.3s ease',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              display: 'flex',
              alignItems: 'stretch'
            }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Chiedi informazioni sui prodotti K-Array, supporto tecnico, o qualsiasi altra cosa..."
                disabled={isLoading}
                style={{
                  width: '100%',
                  minHeight: '56px',
                  maxHeight: '120px',
                  padding: '16px 20px',
                  border: 'none',
                  borderRadius: '20px',
                  fontSize: '16px',
                  lineHeight: '1.5',
                  resize: 'none',
                  outline: 'none',
                  background: 'transparent',
                  color: '#1a1a1a'
                }}
                onFocus={(e) => {
                  e.target.parentElement.style.borderColor = '#3b82f6';
                  e.target.parentElement.style.boxShadow = '0 4px 20px rgba(59, 130, 246, 0.15)';
                }}
                onBlur={(e) => {
                  e.target.parentElement.style.borderColor = 'rgba(59, 130, 246, 0.1)';
                  e.target.parentElement.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.08)';
                }}
              />
            </div>
            
            <ModernButton
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              loading={isLoading}
              size="lg"
              style={{
                borderRadius: '16px',
                minWidth: '64px',
                height: '64px',
                alignSelf: 'stretch',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Send size={20} />
            </ModernButton>
          </div>
          
          {/* Quick Actions */}
          <div style={{
            display: 'flex',
            gap: '12px',
            marginTop: '16px',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            {[
              'Cos\'è K-Framework 3?',
              'Supporto tecnico',
              'Catalogo prodotti',
              'Specifiche tecniche'
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setInput(suggestion)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '20px',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  background: 'rgba(59, 130, 246, 0.05)',
                  color: '#3b82f6',
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontWeight: '500'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(102, 126, 234, 0.1)';
                  e.target.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(102, 126, 234, 0.05)';
                  e.target.style.transform = 'translateY(0)';
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}