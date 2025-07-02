import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  AlertCircle, 
  CheckCircle, 
  Loader, 
  ChevronDown, 
  ChevronUp,
  Zap
} from 'lucide-react';

// Component for reasoning steps
function ReasoningPanel({ steps, isExpanded, onToggle }) {
  return (
    <div style={{
      marginTop: 'var(--space-2)',
      border: '1px solid var(--karray-border)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden'
    }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          padding: 'var(--space-2)',
          backgroundColor: 'var(--karray-surface)',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          fontSize: 'var(--font-size-sm)',
          color: 'var(--karray-text-secondary)'
        }}
      >
        <span className="flex items-center gap-2">
          <Zap size={14} />
          Processo di ragionamento ({steps.length} passi)
        </span>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      
      {isExpanded && (
        <div style={{
          padding: 'var(--space-3)',
          backgroundColor: 'var(--karray-background)',
          borderTop: '1px solid var(--karray-border)'
        }}>
          {steps.map((step, index) => (
            <div key={index} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--space-2)',
              marginBottom: 'var(--space-2)',
              fontSize: 'var(--font-size-sm)'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                backgroundColor: step.type === 'error' ? 'var(--karray-error)' : 'var(--karray-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '2px'
              }}>
                {step.type === 'error' ? (
                  <AlertCircle size={10} color="white" />
                ) : step.type === 'progress' ? (
                  <Loader size={10} color="white" />
                ) : (
                  <CheckCircle size={10} color="white" />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontWeight: 500,
                  color: step.type === 'error' ? 'var(--karray-error)' : 'var(--karray-text)'
                }}>
                  {step.message}
                </div>
                {step.details && (
                  <div style={{ 
                    marginTop: 'var(--space-1)',
                    color: 'var(--karray-text-secondary)',
                    fontSize: 'var(--font-size-xs)'
                  }}>
                    {step.details}
                  </div>
                )}
                <div style={{
                  marginTop: 'var(--space-1)',
                  color: 'var(--karray-text-secondary)',
                  fontSize: 'var(--font-size-xs)'
                }}>
                  {new Date(step.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Component for streaming message
function StreamingMessage({ message, onReasoningToggle }) {
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  
  const handleReasoningToggle = () => {
    setReasoningExpanded(!reasoningExpanded);
    if (onReasoningToggle) {
      onReasoningToggle(!reasoningExpanded);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: 'var(--space-3)',
      marginBottom: 'var(--space-4)'
    }}>
      <div style={{
        width: '32px',
        height: '32px',
        backgroundColor: message.type === 'user' ? 'var(--karray-secondary)' : 'var(--karray-primary)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0
      }}>
        {message.type === 'user' ? 
          <User size={16} color="white" /> : 
          <Bot size={16} color="white" />
        }
      </div>
      
      <div style={{ flex: 1 }}>
        <div style={{
          backgroundColor: message.type === 'user' ? 'var(--karray-surface)' : 'white',
          border: message.isError ? '1px solid var(--karray-error)' : '1px solid var(--karray-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-3)',
          position: 'relative'
        }}>
          {message.isStreaming && (
            <div style={{
              position: 'absolute',
              top: 'var(--space-2)',
              right: 'var(--space-2)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--karray-text-secondary)'
            }}>
              <Loader size={12} style={{ animation: 'spin 1s linear infinite' }} />
              Scrivendo...
            </div>
          )}
          
          <div style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: 1.5,
            color: message.isError ? 'var(--karray-error)' : 'var(--karray-text)'
          }}>
            {message.content}
            {message.isStreaming && (
              <span style={{
                opacity: 0.7,
                animation: 'blink 1s infinite'
              }}>|</span>
            )}
          </div>
          
          {message.sources && message.sources.length > 0 && (
            <div style={{
              marginTop: 'var(--space-2)',
              padding: 'var(--space-2)',
              backgroundColor: 'var(--karray-surface)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-sm)'
            }}>
              <strong>Fonti:</strong>
              <ul style={{ margin: 'var(--space-1) 0 0 var(--space-4)', padding: 0 }}>
                {message.sources.map((source, index) => (
                  <li key={index}>
                    {typeof source === 'string' 
                      ? source 
                      : source?.source || source?.title || `Fonte ${index + 1}`
                    }
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div style={{
            marginTop: 'var(--space-2)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--karray-text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span>{message.timestamp.toLocaleTimeString()}</span>
            {message.confidence && (
              <span>Confidenza: {Math.round(message.confidence * 100)}%</span>
            )}
          </div>
        </div>
        
        {message.reasoning && message.reasoning.length > 0 && (
          <ReasoningPanel 
            steps={message.reasoning}
            isExpanded={reasoningExpanded}
            onToggle={handleReasoningToggle}
          />
        )}
      </div>
    </div>
  );
}

function StreamingChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Ciao! Sono il tuo assistente AI K-Array. Come posso aiutarti oggi?',
      timestamp: new Date(),
      sources: [],
      reasoning: []
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [showReasoning, setShowReasoning] = useState(true);
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
      sources: [],
      reasoning: []
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // Create bot message for streaming
    const botMessageId = Date.now() + 1;
    const botMessage = {
      id: botMessageId,
      type: 'bot',
      content: '',
      timestamp: new Date(),
      sources: [],
      reasoning: [],
      isStreaming: true
    };

    setMessages(prev => [...prev, botMessage]);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
          user_id: `user_${Date.now()}`,
          include_reasoning: showReasoning
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              
              setMessages(prev => prev.map(msg => {
                if (msg.id === botMessageId) {
                  const updatedMsg = { ...msg };
                  
                  switch (data.type) {
                    case 'reasoning':
                    case 'progress':
                      updatedMsg.reasoning = [...(updatedMsg.reasoning || []), {
                        type: data.type,
                        message: data.data.message,
                        details: data.data.step || data.data.sequence?.join(' → '),
                        timestamp: data.timestamp
                      }];
                      break;
                      
                    case 'response':
                      updatedMsg.content = data.data.text;
                      updatedMsg.isStreaming = !data.data.is_complete;
                      break;
                      
                    case 'metadata':
                      updatedMsg.confidence = data.data.confidence;
                      updatedMsg.sources = data.data.sources;
                      break;
                      
                    case 'complete':
                      updatedMsg.isStreaming = false;
                      break;
                      
                    case 'error':
                      updatedMsg.content = `Errore: ${data.data.message}`;
                      updatedMsg.isError = true;
                      updatedMsg.isStreaming = false;
                      break;
                  }
                  
                  return updatedMsg;
                }
                return msg;
              }));
              
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }

    } catch (error) {
      console.error('Chat error:', error);
      
      setMessages(prev => prev.map(msg => {
        if (msg.id === botMessageId) {
          return {
            ...msg,
            content: `Errore nella comunicazione: ${error.message}`,
            isError: true,
            isStreaming: false
          };
        }
        return msg;
      }));
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
          <div className="flex items-center justify-between">
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
                  Online • Streaming & RAG Technology
                </p>
              </div>
            </div>
            
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              style={{
                padding: 'var(--space-2)',
                border: `1px solid ${showReasoning ? 'var(--karray-primary)' : 'var(--karray-border)'}`,
                borderRadius: 'var(--radius-md)',
                backgroundColor: showReasoning ? 'var(--karray-primary)' : 'transparent',
                color: showReasoning ? 'white' : 'var(--karray-text)',
                cursor: 'pointer',
                fontSize: 'var(--font-size-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)'
              }}
            >
              <Zap size={14} />
              Ragionamento
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {messages.map((message) => (
            <StreamingMessage 
              key={message.id} 
              message={message}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: 'var(--space-4)',
          borderTop: '1px solid var(--karray-border)',
          backgroundColor: 'var(--karray-surface)'
        }}>
          <div style={{
            display: 'flex',
            gap: 'var(--space-2)',
            alignItems: 'flex-end'
          }}>
            <textarea
              ref={inputRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Scrivi il tuo messaggio..."
              disabled={isLoading}
              style={{
                flex: 1,
                minHeight: '40px',
                maxHeight: '120px',
                padding: 'var(--space-3)',
                border: '1px solid var(--karray-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
                fontFamily: 'inherit',
                resize: 'none',
                backgroundColor: 'white'
              }}
              rows={1}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputText.trim()}
              style={{
                padding: 'var(--space-3)',
                backgroundColor: 'var(--karray-primary)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading || !inputText.trim() ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: '44px',
                height: '44px'
              }}
            >
              {isLoading ? (
                <Loader size={20} style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}

export default StreamingChatInterface;