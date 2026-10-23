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

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Try backend FastAPI Gemini proxy via central API client
    try {
      const data = await api.queryWasteAI(query);
      if (data && (data.reply || data.response)) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            sender: 'ai',
            text: data.reply || data.response,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        setLoading(false);
        return;
      }
    } catch {
      // Fall back to client-side knowledge base
    }

    // Client-side fallback knowledge base
    setTimeout(() => {
      let reply = '';
      const q = query.toLowerCase();

      if (q.includes('battery') || q.includes('batteries')) {
        reply =
          '⚠️ Batteries (especially Lithium-ion and Lead-Acid) must NEVER be placed in ordinary dry or wet bins due to chemical leakage and fire risk. Take them to designated E-Waste / Battery Drop-off depots for specialized hydrometallurgical recycling.';
      } else if (q.includes('pizza') || q.includes('grease')) {
        reply =
          '🍕 Cardboard pizza boxes soiled with heavy grease and cheese cannot be recycled because the oil prevents paper fibers from binding during pulping. Tear off the clean top lid for the Cardboard bin, and put the greasy base in Organic / Compost or general waste.';
      } else if (q.includes('plastic') || q.includes('milk')) {
        reply =
          '🧴 Rinse plastic containers thoroughly with water to remove residue. Remove labels if easily detachable. If the plastic is marked HDPE (#2) or PET (#1), place it in the Recyclable / Dry Waste bin.';
      } else if (q.includes('tube') || q.includes('fluorescent') || q.includes('glass')) {
        reply =
          '💡 Fluorescent tubes contain trace amounts of mercury vapor and belong in Hazardous/E-Waste collection, NOT regular glass bins. Regular glass bottles (clear, brown, green) should be rinsed and placed in their specific glass bins.';
      } else {
        reply =
          `♻️ For "${query}": Generally, ensure materials are clean, dry, and free of food contamination before placing into the Recyclable bin. Organic food scraps belong in the Wet/Compost bin. Hazardous and electronic components require specialized drop-offs. (Connected to WasteAI knowledge base).`;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'ai',
          text: reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      setLoading(false);
    }, 900);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">WasteAI Assistant</h1>
        <p className="page-subtitle">
          Interactive AI guidance on waste segregation rules, recycling protocols, and hazardous materials
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
              <div style={{ fontSize: '0.75rem', color: '#10b981' }}>● Ready (Gemini API Integration Interface)</div>
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
