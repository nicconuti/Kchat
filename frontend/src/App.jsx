import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import SystemStatus from './components/SystemStatus';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<ChatInterface />} />
          <Route path="/chat" element={<ChatInterface />} />
          <Route path="/upload" element={<DocumentUpload />} />
          <Route path="/status" element={<SystemStatus />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
