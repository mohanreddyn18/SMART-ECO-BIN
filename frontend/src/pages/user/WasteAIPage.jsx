import React, { useState, useRef, useEffect } from 'react';
import {
  FiSend,
  FiCpu,
  FiUser,
  FiHelpCircle,
  FiCheckCircle,
  FiRefreshCw
} from 'react-icons/fi';
import { api } from '../../services/api';

export default function WasteAIPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: 'Hello! I am WasteAI, your intelligent recycling and disposal assistant. How can I help you segregate or dispose of waste today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [serviceStatus, setServiceStatus] = useState('Checking backend...');
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const suggestedPrompts = [
    'Can pizza boxes with grease be recycled?',
    'What should I do with spent lithium batteries?',
    'How should I clean and dispose of plastic milk containers?',
    'Where do fluorescent light tubes belong?'
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    let active = true;
    api.getHealth()
      .then((health) => {
        if (active) {
          setServiceStatus(health.gemini_configured ? 'Gemini configured' : 'Gemini not configured');
        }
      })
      .catch(() => {
        if (active) setServiceStatus('Backend unavailable');
      });

    return () => {
      active = false;
    };
  }, []);

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const data = await api.queryWasteAI(query);
      if (!data?.reply) {
        throw new Error('WasteAI returned no response.');
      }
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'ai',
          text: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (requestError) {
      setError(requestError.message || 'WasteAI could not generate a response.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">WasteAI Assistant</h1>
        <p className="page-subtitle">
          AI-generated waste segregation and disposal guidance. Responses are not
          authoritative local rules or a replacement for the classifier result.
        </p>
      </div>

      <div className="card" style={{ height: '70vh', display: 'flex', flexDirection: 'column', padding: 0 }}>
        {/* Chat Header */}
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#2563eb', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FiCpu />
            </div>
            <div>
              <div style={{ fontWeight: 600, color: '#111827' }}>WasteAI Knowledge Engine</div>
              <div style={{ fontSize: '0.75rem', color: serviceStatus === 'Gemini configured' ? '#10b981' : '#b45309' }}>
                ● {serviceStatus}
              </div>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-outline"
            style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
            onClick={() => setMessages([messages[0]])}
          >
            <FiRefreshCw style={{ marginRight: '4px' }} /> Clear Chat
          </button>
        </div>

        {/* Messages Scroll Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                gap: '10px',
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%'
              }}
            >
              {msg.sender === 'ai' && (
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <FiCpu />
                </div>
              )}

              <div>
                <div
                  style={{
                    backgroundColor: msg.sender === 'user' ? '#2563eb' : '#f3f4f6',
                    color: msg.sender === 'user' ? '#ffffff' : '#1f2937',
                    padding: '0.75rem 1rem',
                    borderRadius: msg.sender === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    fontSize: '0.9rem',
                    lineHeight: 1.5,
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {msg.text}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '3px', textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                  {msg.timestamp}
                </div>
              </div>

              {msg.sender === 'user' && (
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#2563eb', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <FiUser />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', gap: '10px', alignSelf: 'flex-start' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FiCpu />
              </div>
              <div style={{ backgroundColor: '#f3f4f6', padding: '0.75rem 1rem', borderRadius: '12px 12px 12px 2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
                <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>WasteAI is reasoning...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Queries */}
        <div style={{ padding: '0.5rem 1rem', backgroundColor: '#f9fafb', borderTop: '1px solid #e5e7eb', display: 'flex', gap: '8px', overflowX: 'auto' }}>
          {suggestedPrompts.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              className="btn btn-outline"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem', whiteSpace: 'nowrap' }}
              onClick={() => handleSend(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ padding: '1rem', borderTop: '1px solid #e5e7eb', display: 'flex', gap: '10px' }}
        >
          <input
            type="text"
            className="form-control"
            placeholder="Ask WasteAI anything about waste sorting, recycling, or disposal..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !input.trim()}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <FiSend /> Send
          </button>
        </form>
      </div>
    </div>
  );
}
