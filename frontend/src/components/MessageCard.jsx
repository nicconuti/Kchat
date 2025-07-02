import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  Chip,
  Paper,
  IconButton,
  Fade,
  Stack,
  Slide
} from '@mui/material';
import {
  Android as BotIcon,
  Person as PersonIcon,
  ContentCopy as CopyIcon,
  ThumbUp as ThumbUpIcon,
  Stars as SparklesIcon,
  Description as FileTextIcon,
  Launch as ExternalLinkIcon
} from '@mui/icons-material';

export default function MessageCard({ message, onCopy, onFeedback }) {
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
    position: 'relative'
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
                backdropFilter: 'blur(10px)'
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
                  wordBreak: 'break-word'
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
                    border: '1px solid rgba(0, 0, 0, 0.05)'
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
                          justifyContent: 'flex-start'
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
