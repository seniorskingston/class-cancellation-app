import React, { useEffect, useState } from 'react';

const API_URL = 'https://class-cancellation-backend.onrender.com';

type WebsiteEvent = {
  external_id: string;
  title: string;
  start_date: string;
  end_date: string;
  address: string;
  price: string;
  description: string;
  categories: string[];
};

type WebsiteStatus = {
  automatic: boolean;
  time: string;
  last_success: string;
  counts: { new: number; updated: number; unchanged: number; failed: number };
  errors: string[];
  window_label: string;
  events: WebsiteEvent[];
  saved?: boolean;
};

const emptyStatus: WebsiteStatus = {
  automatic: false,
  time: '08:00',
  last_success: '',
  counts: { new: 0, updated: 0, unchanged: 0, failed: 0 },
  errors: [],
  window_label: '',
  events: [],
};

function formatWhen(value: string): string {
  if (!value) return 'Not yet';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('en-CA', { timeZone: 'America/Toronto' });
}

function formatEventDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('en-CA', {
    timeZone: 'America/Toronto',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

const WebsiteEvents: React.FC = () => {
  const [status, setStatus] = useState<WebsiteStatus>(emptyStatus);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState('');

  const applyStatus = (data: WebsiteStatus) => {
    setStatus({ ...emptyStatus, ...data, counts: { ...emptyStatus.counts, ...(data.counts || {}) } });
  };

  useEffect(() => {
    fetch(`${API_URL}/api/website-events`)
      .then((response) => response.json())
      .then((data) => applyStatus(data))
      .catch(() => setMessage('The website events list could not be loaded.'));
  }, []);

  const run = async (path: string, body?: object) => {
    setBusy(path);
    setMessage('');
    try {
      const response = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json();
      applyStatus(data);
      if (data.errors && data.errors.length) {
        setMessage(data.errors.join('\n'));
      } else if (path.endsWith('/preview')) {
        setMessage('Preview only. Nothing was saved.');
      } else if (path.endsWith('/sync')) {
        setMessage('Website events saved. The class list was not changed.');
      } else {
        setMessage(data.automatic ? 'Automatic sync is on.' : 'Automatic sync is off.');
      }
    } catch (error) {
      setMessage('That action could not be completed.');
    } finally {
      setBusy('');
    }
  };

  return (
    <div style={{ background: '#f8f9fa', padding: '25px', borderRadius: '15px', border: '2px solid #6f42c1', marginTop: '25px' }}>
      <h2 style={{ color: '#6f42c1', marginBottom: '10px', fontSize: '1.5rem' }}>Website Events</h2>
      <p style={{ color: '#333', fontSize: '14px', lineHeight: 1.5 }}>
        This reads published events from the Seniors Kingston website for {status.window_label || 'this month and next month'}.
        The green upload box above still works. These events are kept separate and do not cancel classes.
      </p>
      <p style={{ color: '#333', fontSize: '14px' }}>
        Last successful sync: {formatWhen(status.last_success)}
      </p>
      <p style={{ color: '#333', fontSize: '14px' }}>
        New {status.counts.new} · Updated {status.counts.updated} · Unchanged {status.counts.unchanged} · Failed {status.counts.failed}
      </p>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', margin: '15px 0' }}>
        <button type="button" onClick={() => run('/api/website-events/preview')} disabled={busy !== ''} style={buttonStyle}>
          {busy.endsWith('/preview') ? 'Checking...' : 'Preview'}
        </button>
        <button type="button" onClick={() => run('/api/website-events/sync')} disabled={busy !== ''} style={buttonStyle}>
          {busy.endsWith('/sync') ? 'Saving...' : 'Sync Now'}
        </button>
      </div>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '15px' }}>
        <label style={{ fontSize: '14px' }}>
          <input
            type="checkbox"
            checked={status.automatic}
            onChange={(event) => setStatus({ ...status, automatic: event.target.checked })}
          />{' '}
          Automatic sync
        </label>
        <input
          type="time"
          value={status.time}
          onChange={(event) => setStatus({ ...status, time: event.target.value })}
        />
        <button
          type="button"
          onClick={() => run('/api/website-events/schedule', { automatic: status.automatic, time: status.time })}
          disabled={busy !== ''}
          style={buttonStyle}
        >
          Save schedule
        </button>
      </div>
      <p style={{ color: '#666', fontSize: '13px' }}>
        Automatic sync is off until you turn it on and save the schedule. Preview does not save anything.
      </p>
      {message && (
        <div style={{ margin: '10px 0', padding: '12px', background: '#fff', border: '1px solid #d6c7f5', borderRadius: '8px', whiteSpace: 'pre-line', fontSize: '14px' }}>
          {message}
        </div>
      )}
      {status.events.map((event) => (
        <div key={event.external_id} style={{ background: 'white', border: '1px solid #ddd', borderRadius: '8px', padding: '12px', marginTop: '10px' }}>
          <strong>{event.title}</strong>
          <div style={{ fontSize: '13px', color: '#555', marginTop: '4px' }}>
            {formatEventDate(event.start_date)}
            {event.address ? ` · ${event.address}` : ''}
            {event.price ? ` · ${event.price}` : ''}
          </div>
          {event.description && (
            <div style={{ fontSize: '14px', marginTop: '8px', whiteSpace: 'pre-line' }}>{event.description}</div>
          )}
        </div>
      ))}
    </div>
  );
};

const buttonStyle: React.CSSProperties = {
  background: '#6f42c1',
  color: 'white',
  border: 'none',
  padding: '8px 14px',
  borderRadius: '6px',
  cursor: 'pointer',
};

export default WebsiteEvents;
