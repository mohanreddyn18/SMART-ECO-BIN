import React, { useState, useRef, useEffect } from 'react';
import {
  FiCpu,
  FiSend,
  FiTool,
  FiCheckCircle,
  FiDatabase,
  FiTerminal,
  FiRefreshCw
} from 'react-icons/fi';
import { api } from '../../services/api';

export default function SanitationAIPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: 'Greetings, Administrator. I am SanitationAI, an enterprise analytics agent with function-calling capabilities. I query real system telemetry to answer operational sanitation inquiries without hallucinating metrics.',
      toolUsed: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const messagesEndRef = useRef(null);

  const functionTriggers = [
    { label: 'Query Sanitation Status', query: 'What is our current overall sanitation posture?' },
    { label: 'Audit Active Anomalies', query: 'List all active statistical anomalies and their severities.' },
    { label: 'Check Waste Breakdown', query: 'What is the category distribution across logged waste?' },
    { label: 'Location Volume Statistics', query: 'Which department has logged the highest waste volume?' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const executeControlledQuery = async (queryText) => {
    const q = queryText.toLowerCase();

    if (q.includes('status') || q.includes('posture')) {
      try {
        const intel = await api.getSanitation();
        return {
          tool: 'get_sanitation_status()',
          data: intel,
          reply: `Current System Sanitation Posture is "${intel.currentStatus || 'UNAVAILABLE'}".\n\nSupporting Telemetry: ${intel.reason || 'Software evaluation based on event frequency.'} (Hardware sensors deployed: ${intel.hardwareSensorsDeployed ? 'Yes' : 'No - Pure Software Evaluation'}).`
        };
      } catch (err) {
        return {
          tool: 'get_sanitation_status()',
          data: null,
          reply: `Error retrieving sanitation telemetry: ${err.message}`
        };
      }
    } else if (q.includes('anomal') || q.includes('outlier')) {
      try {
        const anom = await api.getAnomalies();
        const list = anom.anomalies || [];
        return {
          tool: 'get_anomalies()',
          data: anom,
          reply: `Isolation Forest status: "${anom.status || 'Active'}". Sampled records: ${anom.recordsSampled || 0}.\n` +
            (list.length === 0
              ? 'No anomalies detected within nominal confidence bounds.'
              : list.map((a) => `• [${a.severity}] ${a.type}: "${a.reason}" -> ${a.recommendation}`).join('\n'))
        };
      } catch (err) {
        return {
          tool: 'get_anomalies()',
          data: null,
          reply: `Error retrieving anomaly telemetry: ${err.message}`
        };
      }
    } else if (q.includes('distribution') || q.includes('breakdown') || q.includes('category')) {
      try {
        const stats = await api.getAnalytics();
        const total = stats.totalClassifications || 0;
        const bd = stats.categoryBreakdown || {};
        return {
          tool: 'get_waste_distribution()',
          data: stats,
          reply: `Aggregate Waste Distribution across ${total} verified events in storage:\n` +
            `• Recyclable / Dry: ${bd.recyclable || 0}\n` +
            `• Organic / Wet: ${bd.organic || 0}\n` +
            `• Hazardous / E-Waste: ${bd.hazardous || 0}\n` +
            `• Residual Trash: ${bd.trash || 0}`
        };
      } catch (err) {
        return {
          tool: 'get_waste_distribution()',
          data: null,
          reply: `Error retrieving distribution statistics: ${err.message}`
        };
      }
    } else {
      try {
        const stats = await api.getAnalytics();
        return {
          tool: 'get_total_classifications()',
          data: stats,
          reply: `Active storage provider (${stats.storageProvider || 'Local Storage'}) reports ${stats.totalClassifications || 0} verified classification records. Today's intake: ${stats.todayActivity || 0} events. Average model confidence: ${(stats.averageConfidence || 0).toFixed(1)}%.`
        };
      } catch (err) {
        return {
          tool: 'get_total_classifications()',
          data: null,
          reply: `Database reports operational baseline. Error: ${err.message}`
        };
      }
    }
  };

  const handleSend = async (customQuery) => {
    const query = customQuery || input;
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

    // Try FastAPI SanitationAI endpoint if live
    try {
      const data = await api.querySanitationAI(query);
      if (data && (data.reply || data.response)) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            sender: 'ai',
            text: data.reply || data.response,
            toolUsed: data.function_called || 'backend_telemetry_query',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        setLoading(false);
        return;
      }
    } catch {
      // Fallback
    }

    // Client-side controlled execution with real backend data
    const q = query.toLowerCase();
    const toolName = q.includes('status') || q.includes('posture') ? 'get_sanitation_status()' :
                     q.includes('anomal') || q.includes('outlier') ? 'get_anomalies()' :
                     q.includes('distribution') || q.includes('breakdown') ? 'get_waste_distribution()' : 'get_total_classifications()';
    setActiveTool(toolName);

    const execution = await executeControlledQuery(query);

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + 1,
        sender: 'ai',
        text: execution.reply,
        toolUsed: execution.tool,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setActiveTool(null);
    setLoading(false);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">SanitationAI Operations Agent</h1>
        <p className="page-subtitle">
          Administrative intelligence engine grounded in real database queries & function calling (Zero hallucination policy)
        </p>
      </div>

      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Grounded Reasoning:</strong> SanitationAI is constrained to execute verified backend telemetry functions
        (<code>get_sanitation_status</code>, <code>get_anomalies</code>, <code>get_waste_distribution</code>).
        It explains strictly verified telemetry values and never invents database figures.
      </div>

      <div className="card" style={{ height: '68vh', display: 'flex', flexDirection: 'column', padding: 0 }}>
        {/* Header */}
        <div style={{ padding: '0.85rem 1.25rem', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#ef4444', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FiTerminal />
            </div>
            <div>
              <div style={{ fontWeight: 600, color: '#111827' }}>SanitationAI Admin Agent</div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                Tools: get_sanitation_status, get_anomalies, get_waste_distribution
              </div>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-outline"
            style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}
            onClick={() => setMessages([messages[0]])}
          >
            <FiRefreshCw style={{ marginRight: '4px' }} /> Clear
          </button>
        </div>

        {/* Messages Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {messages.map((m) => (
            <div
              key={m.id}
              style={{
                alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%'
              }}
            >
              {m.toolUsed && (
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#2563eb', background: '#eff6ff', padding: '2px 8px', borderRadius: '4px', marginBottom: '6px' }}>
                  <FiTool /> Function executed: <code>{m.toolUsed}</code>
                </div>
              )}
              <div
                style={{
                  backgroundColor: m.sender === 'user' ? '#ef4444' : '#f3f4f6',
                  color: m.sender === 'user' ? '#ffffff' : '#1f2937',
                  padding: '0.75rem 1rem',
                  borderRadius: m.sender === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                  fontSize: '0.9rem',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap'
                }}
              >
                {m.text}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '3px', textAlign: m.sender === 'user' ? 'right' : 'left' }}>
                {m.timestamp}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ alignSelf: 'flex-start' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#2563eb', background: '#eff6ff', padding: '2px 8px', borderRadius: '4px', marginBottom: '6px' }}>
                <FiTool /> Calling database function: <code>{activeTool || 'executing...'}</code>
              </div>
              <div style={{ backgroundColor: '#f3f4f6', padding: '0.75rem 1rem', borderRadius: '12px 12px 12px 2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
                <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>Querying Firestore telemetry & synthesizing response...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Function Trigger Buttons */}
        <div style={{ padding: '0.5rem 1rem', backgroundColor: '#f9fafb', borderTop: '1px solid #e5e7eb', display: 'flex', gap: '8px', overflowX: 'auto' }}>
          {functionTriggers.map((trig, idx) => (
            <button
              key={idx}
              type="button"
              className="btn btn-outline"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem', whiteSpace: 'nowrap' }}
              onClick={() => handleSend(trig.query)}
            >
              <FiTool style={{ marginRight: '4px' }} /> {trig.label}
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
            placeholder="Ask SanitationAI regarding telemetry, anomalies, or category volume..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary"
            style={{ backgroundColor: '#ef4444', borderColor: '#ef4444' }}
            disabled={loading || !input.trim()}
          >
            <FiSend /> Query
          </button>
        </form>
      </div>
    </div>
  );
}
