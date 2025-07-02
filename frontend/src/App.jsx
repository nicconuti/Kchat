import React, { useState, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import getMuiTheme from './theme/muiTheme';
import ColorModeContext from './theme/ColorModeContext';
import Layout from './components/Layout';
import ChatInterface from './components/ChatInterface';
import StreamingChatInterface from './components/StreamingChatInterface';
import ModernChatInterface from './components/ModernChatInterface';
import MUIModernChatInterface from './components/MUIModernChatInterface';
import DocumentUpload from './components/DocumentUpload';
import SystemStatus from './components/SystemStatus';
import SimpleTest from './SimpleTest';
import './App.css';
import './styles/ModernUI.css';
import './styles/MUIAnimations.css';

function App() {
  const [mode, setMode] = useState(() => localStorage.getItem('colorMode') || 'light');
  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode(prev => {
          const next = prev === 'light' ? 'dark' : 'light';
          localStorage.setItem('colorMode', next);
          return next;
        });
      }
    }),
    []
  );
  const theme = useMemo(() => getMuiTheme(mode), [mode]);
  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
      <Router>
        <Routes>
          {/* New MUI Interface as Default */}
          <Route path="/" element={<MUIModernChatInterface />} />
          <Route path="/chat" element={<MUIModernChatInterface />} />
          <Route path="/chat/mui" element={<MUIModernChatInterface />} />
          
          {/* Legacy Interfaces */}
          <Route path="/chat/modern" element={
            <Layout>
              <ModernChatInterface />
            </Layout>
          } />
          <Route path="/chat/streaming" element={
            <Layout>
              <StreamingChatInterface />
            </Layout>
          } />
          <Route path="/chat/legacy" element={
            <Layout>
              <ChatInterface />
            </Layout>
          } />
          <Route path="/upload" element={
            <Layout>
              <DocumentUpload />
            </Layout>
          } />
          <Route path="/status" element={
            <Layout>
              <SystemStatus />
            </Layout>
          } />
          <Route path="/test" element={
            <Layout>
              <SimpleTest />
            </Layout>
          } />
        </Routes>
      </Router>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export default App;
