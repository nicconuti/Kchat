import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Avatar,
  Chip,
  Paper,
  Collapse,
  IconButton,
  Container,
  Stack,
  Divider,
  Fade,
  Slide,
  LinearProgress,
} from '@mui/material';
import MUIResponsiveLayout from './MUIResponsiveLayout';
import {
  Send as SendIcon,
  Android as BotIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  ThumbUp as ThumbUpIcon,
  Stars as SparklesIcon,
  Description as FileTextIcon,
  Launch as ExternalLinkIcon,
  Psychology as PsychologyIcon,
  Schedule as ClockIcon,
} from '@mui/icons-material';

function MUIMessageCard({ message, onCopy, onFeedback }) {
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const isUser = message.type === 'user';
  const hasError = message.isError;

  const getMessageCardSx = () => ({
    mb: 3,
    borderRadius: 5,
    overflow: 'hidden',
    background: isUser
      ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
      : hasError
        ? 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)'
        : 'white',
    border: isUser
      ? '1px solid rgba(59, 130, 246, 0.2)'
      : hasError
        ? '1px solid rgba(239, 68, 68, 0.2)'
        : '1px solid rgba(226, 232, 240, 0.6)',
    boxShadow: isUser
      ? '0 4px 20px rgba(59, 130, 246, 0.15)'
      : hasError
        ? '0 4px 20px rgba(239, 68, 68, 0.15)'
        : 3,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
    position: 'relative',
  });

  return (
    <Slide direction="up" in={true} timeout={400}>
      <Card
        sx={getMessageCardSx()}
        onMouseEnter={() => {
          setIsHovered(true);
          setShowActions(true);
        }}
        onMouseLeave={() => {
          setIsHovered(false);
          setShowActions(false);
        }}
      >
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Box display="flex" gap={2} alignItems="flex-start">
            <Avatar
              sx={{
                width: 44,
                height: 44,
                background: isUser
                  ? 'rgba(255, 255, 255, 0.2)'
                  : 'linear-gradient(135deg, #0a0a0a 0%, #1e1e1e 100%)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                backdropFilter: 'blur(10px)',
              }}
            >
              {isUser ? <PersonIcon /> : <BotIcon />}
            </Avatar>
            <Box flex={1} position="relative">
              {message.isStreaming && (
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <SparklesIcon sx={{ fontSize: 16, animation: 'pulse 1.5s infinite' }} />
                  <Typography variant="caption" fontWeight={500}>
                    K-Array AI sta pensando...
                  </Typography>
                </Box>
              )}
              <Typography
                variant="body1"
                sx={{
                  color: isUser ? 'white' : hasError ? 'error.main' : 'text.primary',
                  lineHeight: 1.6,
                  fontWeight: isUser ? 500 : 400,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {message.content}
                {message.isStreaming && (
                  <Box component="span" sx={{ ml: 0.5, animation: 'pulse 1s infinite' }}>●</Box>
                )}
              </Typography>
              {message.sources && message.sources.length > 0 && (
                <Paper
                  elevation={0}
                  sx={{
                    mt: 2,
                    p: 2,
                    background: 'rgba(255, 255, 255, 0.9)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 3,
                    border: '1px solid rgba(0, 0, 0, 0.05)',
                  }}
                >
                  <Box display="flex" alignItems="center" gap={1} mb={1.5}>
                    <FileTextIcon sx={{ fontSize: 16 }} />
                    <Typography variant="subtitle2" fontWeight={600}>
                      Fonti documentali
                    </Typography>
                  </Box>
                  <Stack spacing={1}>
                    {message.sources.map((source, index) => (
                      <Chip
                        key={index}
                        icon={<ExternalLinkIcon sx={{ fontSize: 14 }} />}
                        label={typeof source === 'string' ? source : source.snippet}
                        size="small"
                        sx={{
                          backgroundColor: 'rgba(59, 130, 246, 0.05)',
                          color: 'primary.main',
                          '& .MuiChip-icon': { color: 'primary.main' },
                          justifyContent: 'flex-start',
                        }}
                      />
                    ))}
                  </Stack>
                </Paper>
              )}
              <Fade in={showActions && !isUser}>
                <Box position="absolute" top={-10} right={0} display="flex" gap={1}>
                  <IconButton
                    size="small"
                    onClick={() => onCopy && onCopy(message.content)}
                    sx={{ bgcolor: 'rgba(255, 255, 255, 0.9)', boxShadow: 2 }}
                  >
                    <CopyIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => onFeedback && onFeedback(message, 'positive')}
                    sx={{ bgcolor: 'rgba(255, 255, 255, 0.9)', color: 'success.main', boxShadow: 2 }}
                  >
                    <ThumbUpIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                </Box>
              </Fade>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Slide>
  );
}

function MUIReasoningPanel({ steps, isExpanded, onToggle }) {
  return (
    <Paper
      elevation={0}
      sx={{
        mt: 2,
        borderRadius: 4,
        overflow: 'hidden',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.05))',
        backdropFilter: 'blur(10px)',
      }}
    >
      <Button
        fullWidth
        onClick={onToggle}
        sx={{ p: 2, justifyContent: 'space-between', color: 'primary.main', fontWeight: 600 }}
        endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        startIcon={<PsychologyIcon />}
      >
        Processo di ragionamento ({steps.length} passi)
      </Button>
      <Collapse in={isExpanded}>
        <Box p={2.5}>
          <Stack spacing={2}>
            {steps.map((step, index) => (
              <Slide key={index} direction="up" in={true} timeout={400 + index * 100}>
                <Paper elevation={1} sx={{ p: 2, borderRadius: 3 }}>
                  <Box display="flex" gap={2}>
                    <Avatar sx={{ width: 32, height: 32, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', fontSize: '0.875rem' }}>
                      {index + 1}
                    </Avatar>
                    <Box flex={1}>
                      <Typography variant="subtitle2" fontWeight={600} mb={0.5}>{step.step}</Typography>
                      <Typography variant="body2" color="text.secondary" mb={1}>{step.message}</Typography>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <ClockIcon sx={{ fontSize: 12, color: 'text.disabled' }} />
                        <Typography variant="caption" color="text.disabled">
                          {new Date(step.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Paper>
              </Slide>
            ))}
          </Stack>
        </Box>
      </Collapse>
    </Paper>
  );
}

export default function MUIModernChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState([]);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    setMessages([{
      id: 'welcome',
      type: 'assistant',
      content: 'Ciao! Sono l\'assistente K-Array AI... Come posso assisterti oggi?',
      timestamp: new Date().toISOString(),
      isStreaming: false
    }]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Grazie per la tua domanda: "${userMessage.content}"...`,
        timestamp: new Date().toISOString(),
        isStreaming: false,
        sources: ['K-Framework 3 Documentation', 'Technical Support Manual', 'Product Specifications']
      };
      setTimeout(() => {
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoading(false);
      }, 1500);
    } catch (error) {
      console.error('Chat error:', error);
      setIsLoading(false);
    }
  };

  const handleCopy = (text) => navigator.clipboard.writeText(text);
  const handleFeedback = (message, type) => console.log('Feedback:', { message: message.id, type });
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    'Cos\'è K-Framework 3?',
    'Supporto tecnico',
    'Catalogo prodotti',
    'Specifiche tecniche'
  ];

  return (
    <MUIResponsiveLayout>
      <Box sx={{ height: '100%', background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Container maxWidth="md" sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Paper elevation={3} sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRadius: 4 }}>
            <Box flex={1} sx={{ overflowY: 'auto', p: 3 }}>
              {messages.map((message) => (
                <MUIMessageCard key={message.id} message={message} onCopy={handleCopy} onFeedback={handleFeedback} />
              ))}
              {isLoading && (
                <Box sx={{ mb: 3 }}>
                  <LinearProgress sx={{ borderRadius: 2, height: 6 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    K-Array AI sta elaborando la risposta...
                  </Typography>
                </Box>
              )}
              {reasoningSteps.length > 0 && (
                <MUIReasoningPanel steps={reasoningSteps} isExpanded={reasoningExpanded} onToggle={() => setReasoningExpanded(!reasoningExpanded)} />
              )}
              <div ref={messagesEndRef} />
            </Box>
            <Divider />
            <Box sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Box display="flex" gap={2} alignItems="flex-end">
                  <TextField
                    ref={inputRef}
                    fullWidth
                    multiline
                    maxRows={4}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Chiedi informazioni sui prodotti K-Array, supporto tecnico, o qualsiasi altra cosa..."
                    disabled={isLoading}
                    variant="outlined"
                    sx={{ '& .MuiOutlinedInput-root': { borderRadius: 5 } }}
                  />
                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    sx={{ minWidth: 64, height: 56, borderRadius: 4 }}
                  >
                    <SendIcon />
                  </Button>
                </Box>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {quickActions.map((suggestion, index) => (
                    <Chip
                      key={index}
                      label={suggestion}
                      onClick={() => setInput(suggestion)}
                      sx={{ borderRadius: 5, '&:hover': { transform: 'translateY(-2px)', boxShadow: 2 }, transition: 'all 0.2s ease' }}
                    />
                  ))}
                </Stack>
              </Stack>
            </Box>
          </Paper>
        </Container>
      </Box>
    </MUIResponsiveLayout>
  );
}