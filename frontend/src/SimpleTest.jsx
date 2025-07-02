import React, { useState } from 'react';

function SimpleTest() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const testAPI = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    setResponse('Inviando...');
    
    try {
      const payload = {
        message: message.trim(),
        session_id: 'test_session',
        user_id: 'test_user'
      };
      
      console.log('Sending payload:', payload);
      
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      console.log('Response status:', res.status);
      console.log('Response headers:', Object.fromEntries(res.headers.entries()));
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('Error response body:', errorText);
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }
      
      const data = await res.json();
      console.log('Success response:', data);
      setResponse(`SUCCESS: ${data.response}`);
      
    } catch (error) {
      console.error('Full error:', error);
      setResponse(`ERROR: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>Test API Semplice</h2>
      <div style={{ marginBottom: '10px' }}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Scrivi un messaggio..."
          style={{ width: '300px', padding: '8px' }}
          onKeyPress={(e) => e.key === 'Enter' && testAPI()}
        />
        <button onClick={testAPI} disabled={loading} style={{ marginLeft: '10px', padding: '8px' }}>
          {loading ? 'Inviando...' : 'Invia'}
        </button>
      </div>
      <div style={{ 
        border: '1px solid #ccc', 
        padding: '10px', 
        minHeight: '100px',
        backgroundColor: response.startsWith('ERROR') ? '#ffebee' : '#e8f5e8'
      }}>
        <strong>Risposta:</strong><br />
        {response || 'Nessuna risposta ancora...'}
      </div>
    </div>
  );
}

export default SimpleTest;