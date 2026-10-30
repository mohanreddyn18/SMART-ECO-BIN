import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { classifyImage, classNames } from './model.js';
import { clearHistory, readHistory, readProfile, saveClassification, saveProfile } from './storage.js';

const navigation = [
  ['dashboard', 'Overview', '⌂'],
  ['classify', 'Classify waste', '＋'],
  ['history', 'Classification history', '◷'],
  ['analytics', 'Analytics', '▥'],
  ['sanitation', 'Sanitation intelligence', '⌁'],
  ['anomalies', 'Anomaly detection', '△'],
  ['insights', 'Predictive insights', '↗']
];

const titleByRoute = Object.fromEntries(navigation.map(([route, title]) => [route, title]));

function routeFromHash() {
  const route = window.location.hash.replace(/^#\/?/, '').split('/')[0];
  if (route === 'login') return 'login';
  return titleByRoute[route] ? route : 'dashboard';
}

function formatDate(value) {
  return new Date(value).toLocaleString();
}

function getBucketCounts(records, days = 7) {
  const buckets = Array.from({ length: days }, (_, index) => {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - (days - index - 1));
    return { label: date.toLocaleDateString(undefined, { weekday: 'short' }), date, count: 0 };
  });
  for (const record of records) {
    const timestamp = new Date(record.timestamp);
    const bucket = buckets.find(({ date }) => date.toDateString() === timestamp.toDateString());
    if (bucket) bucket.count += 1;
  }
  return buckets;
}

function Chart({ records }) {
  const data = getBucketCounts(records);
  const max = Math.max(1, ...data.map((bucket) => bucket.count));
  return (
    <div className="chart" role="img" aria-label="Classification activity for the last seven days based on this browser's saved history">
      {data.map((bucket) => (
        <div className="chart-column" key={bucket.label}>
          <strong>{bucket.count || ''}</strong>
          <div className="chart-track"><span style={{ height: `${Math.max(3, (bucket.count / max) * 100)}%` }} /></div>
          <small>{bucket.label}</small>
        </div>
      ))}
    </div>
  );
}

function ResultCard({ result }) {
  if (!result) return null;
  return (
    <section className="result-card" aria-live="polite">
      <div className="result-head">
        <div><span className="eyebrow">Browser model result</span><h2>{result.predictedClass.replaceAll('-', ' ')}</h2></div>
        <span className={`confidence ${result.requiresManualReview ? 'review' : ''}`}>{result.confidence}%</span>
      </div>
      <p><strong>Stream:</strong> {result.category}</p>
      <p><strong>Disposal:</strong> {result.disposalBin}</p>
      <p>{result.recommendation}</p>
      <small>{result.model} · {result.inference}</small>
      <div className="notice">This is a 12-class single-item classifier. Its output may be wrong, especially on mixed, unusual, or non-waste images. Confirm locally before disposal.</div>
    </section>
  );
}

function ClassifyPage({ onSave }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const selectFile = useCallback((nextFile) => {
    setError('');
    setResult(null);
    if (!nextFile) return;
    const ext = nextFile.name.split('.').pop()?.toLowerCase();
    if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
      if (preview) URL.revokeObjectURL(preview);
      setFile(null);
      setPreview('');
      setError('Choose a JPG, JPEG, PNG, or WebP image.');
      return;
    }
    if (nextFile.size > 10 * 1024 * 1024) {
      if (preview) URL.revokeObjectURL(preview);
      setFile(null);
      setPreview('');
      setError('Image must be 10 MB or smaller.');
      return;
    }
    if (preview) URL.revokeObjectURL(preview);
    setFile(nextFile);
    setPreview(URL.createObjectURL(nextFile));
  }, [preview]);

  const classify = async () => {
    if (!file) return;
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const prediction = await classifyImage(file);
      setResult(prediction);
      onSave(prediction, file.name);
    } catch (failure) {
      setError(`In-browser inference failed: ${failure.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-stack">
      <div><span className="eyebrow">Private on-device analysis</span><h1>Classify an item</h1><p className="muted">Images are processed in this browser and are never uploaded to a server.</p></div>
      <div className="two-column">
        <div>
          <div
            className={`drop-zone ${dragging ? 'dragging' : ''}`}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => { event.preventDefault(); setDragging(false); selectFile(event.dataTransfer.files?.[0]); }}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click(); }}
            role="button"
            tabIndex={0}
            aria-label="Choose or drop a waste image"
          >
            {preview ? <img className="preview" src={preview} alt="Selected image preview" /> : <><span className="drop-icon">⇧</span><h2>Drop an image here</h2><p>or click to browse · JPG, PNG, WebP · up to 10 MB</p></>}
            <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" hidden onChange={(event) => { selectFile(event.target.files?.[0]); event.target.value = ''; }} />
          </div>
          {file && <div className="selected-file">{file.name}<button className="text-button" onClick={() => { setFile(null); setResult(null); setPreview(''); }}>Clear</button></div>}
          {error && <div className="alert error" role="alert">{error}</div>}
          <button className="button primary wide" disabled={!file || busy} onClick={classify}>{busy ? 'Running browser inference…' : 'Classify image'}</button>
          <p className="fine-print">No account or backend is needed. The model runs locally using WebAssembly.</p>
        </div>
        <div className="panel model-panel">
          <span className="eyebrow">Model card</span>
          <h2>MobileNetV2 · 12 classes</h2>
          <p>Converted from the project’s existing trained PyTorch checkpoint. The browser model recognizes the same twelve labels as the original classifier.</p>
          <div className="class-list">{classNames.map((name) => <span key={name}>{name}</span>)}</div>
          <p className="fine-print">The reported training benchmark is not an independent guarantee of real-world accuracy. Use manual review for uncertain items.</p>
        </div>
      </div>
      <ResultCard result={result} />
    </div>
  );
}

function Dashboard({ records }) {
  const counts = useMemo(() => {
    const categories = {};
    for (const record of records) categories[record.category] = (categories[record.category] || 0) + 1;
    return categories;
  }, [records]);
  return (
    <div className="page-stack">
      <div className="page-heading"><div><span className="eyebrow">Local browser data</span><h1>Waste intelligence</h1><p className="muted">A private dashboard based only on classifications saved in this browser.</p></div><a className="button primary" href="#/classify">＋ Classify item</a></div>
      <div className="stat-grid">
        <div className="stat-card"><span>Classifications</span><strong>{records.length}</strong><small>Saved on this device</small></div>
        <div className="stat-card"><span>Waste streams</span><strong>{Object.keys(counts).length}</strong><small>Observed locally</small></div>
        <div className="stat-card"><span>Needs review</span><strong>{records.filter((item) => item.requiresManualReview).length}</strong><small>Low confidence results</small></div>
      </div>
      <div className="content-grid">
        <section className="panel"><div className="section-heading"><div><h2>Recent activity</h2><p>Seven-day history · no synthetic records</p></div><a href="#/analytics">Details →</a></div><Chart records={records} />{records.length === 0 && <p className="empty-note">No classifications yet. Classify an image to populate this chart.</p>}</section>
        <section className="panel"><h2>Stream distribution</h2><p className="muted">Based on saved model outputs</p>{Object.entries(counts).length ? Object.entries(counts).map(([name, count]) => <div className="distribution-row" key={name}><span>{name}</span><strong>{count}</strong></div>) : <p className="empty-note">Category counts appear after you save a classification.</p>}</section>
      </div>
      <div className="notice">Sanitation, anomaly, and trend panels use only this browser’s locally stored classifications. They are informational and do not represent municipal sensors or a validated operational forecast.</div>
    </div>
  );
}

function History({ records, refresh }) {
  return <div className="page-stack"><div className="page-heading"><div><span className="eyebrow">Private local storage</span><h1>Classification history</h1><p className="muted">Records stay in this browser’s localStorage. Clearing browser data will remove them.</p></div><button className="button secondary" onClick={() => { if (window.confirm('Delete locally saved classifications from this browser?')) { clearHistory(); refresh(); } }} disabled={!records.length}>Clear history</button></div>{records.length ? <div className="table-wrap"><table><thead><tr><th>Item</th><th>Classification</th><th>Stream</th><th>Confidence</th><th>Timestamp</th></tr></thead><tbody>{records.map((record) => <tr key={record.id}><td>{record.fileName}</td><td>{record.predictedClass}</td><td>{record.category}</td><td>{record.confidence}%</td><td>{formatDate(record.timestamp)}</td></tr>)}</tbody></table></div> : <div className="panel empty-state"><span>◷</span><h2>No history yet</h2><p>Successful browser model predictions are saved here.</p><a className="button primary" href="#/classify">Classify an image</a></div>}</div>;
}

function Analytics({ records }) {
  const grouped = useMemo(() => {
    const map = new Map();
    records.forEach((record) => map.set(record.category, (map.get(record.category) || 0) + 1));
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [records]);
  return <div className="page-stack"><div><span className="eyebrow">Observed data only</span><h1>Analytics</h1><p className="muted">Counts and activity derive from local classification history.</p></div><div className="content-grid"><section className="panel"><h2>Daily activity</h2><Chart records={records} />{!records.length && <p className="empty-note">No data available yet.</p>}</section><section className="panel"><h2>Category totals</h2>{grouped.length ? grouped.map(([category, count]) => <div className="distribution-row" key={category}><span>{category}</span><strong>{count}</strong></div>) : <p className="empty-note">No category data available yet.</p>}</section></div><p className="notice">No backend analytics are connected. This page summarizes this device only.</p></div>;
}

function Sanitation({ records }) {
  const hazardous = records.filter((r) => r.category.toLowerCase().includes('hazardous')).length;
  return <div className="page-stack"><div><span className="eyebrow">Browser-derived indicators</span><h1>Sanitation intelligence</h1><p className="muted">Informational signals based on this browser’s classification history, not sensor readings.</p></div><div className="content-grid"><div className="panel"><span className="eyebrow">Local sanitation signal</span><h2>{records.length ? 'History available' : 'Awaiting local data'}</h2><p>{records.length ? `${records.length} locally saved classification${records.length === 1 ? '' : 's'} available for review.` : 'No records are available to summarize yet.'}</p></div><div className="panel"><span className="eyebrow">Hazardous-stream labels</span><h2>{hazardous}</h2><p>Count of saved classifications routed to a hazardous stream.</p></div></div><div className="notice">This static website has no municipal feed, IoT sensors, service dispatch, cloud synchronization, or live sanitation status.</div></div>;
}

function Anomalies({ records }) {
  const needsReview = records.filter((record) => record.requiresManualReview);
  const sufficient = records.length >= 20;
  return <div className="page-stack"><div><span className="eyebrow">Exploratory local checks</span><h1>Anomaly detection</h1><p className="muted">Highlights low-confidence saved classifications; this is not a statistical municipal anomaly service.</p></div><div className="panel"><h2>{sufficient ? 'Local review signals' : 'Insufficient history'}</h2><p>{sufficient ? `${needsReview.length} of ${records.length} saved classifications are marked for manual review.` : `${records.length}/20 local records available. No anomaly conclusion is made until the minimum count is met.`}</p>{needsReview.slice(0, 10).map((record) => <div className="distribution-row" key={record.id}><span>{record.fileName} · {record.predictedClass}</span><strong>{record.confidence}%</strong></div>)}</div></div>;
}

function Insights({ records }) {
  const days = new Set(records.map((record) => new Date(record.timestamp).toDateString())).size;
  const enough = records.length >= 100 && days >= 30;
  return <div className="page-stack"><div><span className="eyebrow">No synthetic forecasting</span><h1>Predictive insights</h1><p className="muted">Forecasting is withheld until local data meets a minimum observation threshold.</p></div><div className="panel"><span className="eyebrow">Readiness</span><h2>{enough ? 'Exploratory trend may be considered' : 'Insufficient history'}</h2><p>{records.length}/100 classifications and {days}/30 distinct days observed in this browser.</p>{enough ? <p>Required history is available, but this static build does not provide a validated forecasting model.</p> : <p>No forecast is generated from insufficient observations.</p>}</div><div className="notice">Records are device-local and can be deleted by clearing local browser storage. No records are shared with other users.</div></div>;
}

function Login({ profile, onLogin }) {
  const [name, setName] = useState(profile?.name || '');
  const [email, setEmail] = useState(profile?.email || '');
  return <div className="login-wrap"><form className="panel login-card" onSubmit={(event) => { event.preventDefault(); if (name.trim() && email.trim()) onLogin(name.trim(), email.trim()); }}><span className="brand-mark">♻</span><span className="eyebrow">Local profile only</span><h1>Welcome</h1><p className="muted">Create a display profile stored on this device. This is not secure authentication and does not create an account.</p><label>Name<input value={name} onChange={(event) => setName(event.target.value)} required /></label><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><button className="button primary wide">Continue locally</button><a className="text-link" href="#/">Return to overview</a></form></div>;
}

export default function App() {
  const [route, setRoute] = useState(routeFromHash);
  const [records, setRecords] = useState(readHistory);
  const [profile, setProfile] = useState(readProfile);
  const [mobileMenu, setMobileMenu] = useState(false);

  useEffect(() => {
    const onHashChange = () => { setRoute(routeFromHash()); setMobileMenu(false); };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const refreshHistory = () => setRecords(readHistory());
  const handleSave = (result, fileName) => setRecords(saveClassification(result, fileName));
  const handleLogin = (name, email) => { setProfile(saveProfile(name, email)); window.location.hash = '#/dashboard'; };

  if (route === 'login') return <Login profile={profile} onLogin={handleLogin} />;

  const page = {
    dashboard: <Dashboard records={records} />,
    classify: <ClassifyPage onSave={handleSave} />,
    history: <History records={records} refresh={refreshHistory} />,
    analytics: <Analytics records={records} />,
    sanitation: <Sanitation records={records} />,
    anomalies: <Anomalies records={records} />,
    insights: <Insights records={records} />
  }[route] || <Dashboard records={records} />;

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? 'open' : ''}`}>
        <a className="brand" href="#/"><span className="brand-mark">♻</span><span>Smart Eco Bin<small>Waste intelligence</small></span></a>
        <div className="nav-label">WORKSPACE</div>
        <nav>{navigation.map(([key, title, icon]) => <a key={key} href={`#/${key}`} className={route === key ? 'active' : ''}><span className="nav-icon">{icon}</span>{title}</a>)}</nav>
        <div className="sidebar-bottom"><div className="local-badge"><span /> Runs on this device</div><a href="#/login" className="profile-link">{profile?.name ? `Profile · ${profile.name}` : 'Create local profile'}</a></div>
      </aside>
      {mobileMenu && <button className="menu-backdrop" aria-label="Close menu" onClick={() => setMobileMenu(false)} />}
      <main className="main-area">
        <header className="topbar"><button className="menu-toggle" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Toggle navigation">☰</button><span>{titleByRoute[route] || 'Overview'}</span><a className="top-profile" href="#/login">{profile?.name || 'Local profile'}</a></header>
        <div className="page-content">{page}</div>
        <footer>Smart Waste Segregation and Sanitation System <span>· Images stay in your browser</span></footer>
      </main>
    </div>
  );
}
