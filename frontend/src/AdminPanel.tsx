import React, { useEffect, useState } from 'react';
import { apiOrigin } from './apiOrigin';

interface AdminPanelProps {
  onBackToMain: () => void;
  onViewPrintList?: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ onBackToMain, onViewPrintList }) => {
  const [programMessage, setProgramMessage] = useState('');
  const [programBusy, setProgramBusy] = useState(false);
  const [sessionInputs, setSessionInputs] = useState<string[]>(['Session 1-2026', 'Session 2-2026']);
  const [frequency, setFrequency] = useState('off');
  const [scheduleTimes, setScheduleTimes] = useState<string[]>(['08:00']);
  const [intervalHours, setIntervalHours] = useState('1');
  const [windowStart, setWindowStart] = useState('08:00');
  const [windowEnd, setWindowEnd] = useState('20:00');
  const [weekday, setWeekday] = useState('monday');
  const [skipWeekends, setSkipWeekends] = useState(false);
  const [storedSessions, setStoredSessions] = useState<Array<{session: string; label: string; count: number; showing: boolean}>>([]);
  const [scheduleSummary, setScheduleSummary] = useState('PerfectMind runs only when you click the button.');
  const [selectedEventsFile, setSelectedEventsFile] = useState<File | null>(null);
  const [eventsMessage, setEventsMessage] = useState('');
  const [locationName, setLocationName] = useState('');
  const [locationAddress, setLocationAddress] = useState('');
  const [addedLocations, setAddedLocations] = useState<Array<{ name: string; address: string }>>([]);
  const [locationMessage, setLocationMessage] = useState('');

  const showProgramStatus = (result: { status?: string; message?: string }) => {
    const message = result.message || 'Waiting for PerfectMind.';
    if (result.status === 'success') {
      setProgramMessage(`✅ ${message}`);
      setProgramBusy(false);
      loadStoredSessions();
      return;
    }
    if (result.status === 'error' || result.status === 'blocked') {
      setProgramMessage(`❌ ${message}`);
      setProgramBusy(false);
      return;
    }
    setProgramMessage(message);
    setProgramBusy(result.status === 'pending' || result.status === 'running');
  };

  useEffect(() => {
    let stopped = false;
    let timer: number | undefined;
    const watch = async () => {
      try {
        const response = await fetch(`${apiOrigin()}/api/perfectmind/sync`);
        if (!response.ok || stopped) return;
        const result = await response.json();
        const active = result.status === 'pending' || result.status === 'running';
        if (active || result.status === 'success' || result.status === 'error') {
          showProgramStatus(result);
        }
        if (active && !stopped) {
          timer = window.setTimeout(watch, 4000);
        }
      } catch {
        if (!stopped) timer = window.setTimeout(watch, 8000);
      }
    };
    watch();
    return () => {
      stopped = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [programBusy]);

  useEffect(() => {
    const loadSchedule = async () => {
      try {
        const response = await fetch(`${apiOrigin()}/api/perfectmind/schedule`);
        if (!response.ok) return;
        const saved = await response.json();
        if (Array.isArray(saved.seasons) && saved.seasons.length) {
          setSessionInputs(saved.seasons);
        }
        if (saved.frequency) setFrequency(saved.frequency);
        if (Array.isArray(saved.times) && saved.times.length) setScheduleTimes(saved.times);
        if (saved.interval_hours) setIntervalHours(String(saved.interval_hours));
        if (saved.window_start) setWindowStart(saved.window_start);
        if (saved.window_end) setWindowEnd(saved.window_end);
        if (saved.weekday) setWeekday(saved.weekday);
        setSkipWeekends(Boolean(saved.skip_weekends));
        if (saved.summary) setScheduleSummary(saved.summary);
      } catch {
        setScheduleSummary('The schedule will appear after the test site finishes updating.');
      }
    };
    loadSchedule();
  }, []);

  const typedSessions = sessionInputs.map((value) => value.trim()).filter(Boolean);

  const handleSaveSchedule = async () => {
    if (typedSessions.length === 0) {
      setProgramMessage('❌ Type a session, such as Session 1-2028.');
      return;
    }
    try {
      const response = await fetch(`${apiOrigin()}/api/perfectmind/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frequency,
          times: scheduleTimes,
          interval_hours: Number(intervalHours),
          window_start: windowStart,
          window_end: windowEnd,
          weekday,
          skip_weekends: skipWeekends,
          seasons: typedSessions,
        }),
      });
      const result = await response.json();
      if (!response.ok) {
        setProgramMessage(`❌ ${result.message || 'The schedule was not saved.'}`);
        return;
      }
      setScheduleSummary(result.summary || 'Schedule saved.');
      setProgramMessage(`✅ ${result.summary}`);
      loadStoredSessions();
    } catch (error) {
      setProgramMessage(`❌ Could not save the schedule: ${error}`);
    }
  };

  const loadStoredSessions = async () => {
    try {
      const response = await fetch(`${apiOrigin()}/api/perfectmind/stored-sessions`);
      if (!response.ok) return;
      const result = await response.json();
      setStoredSessions(Array.isArray(result.sessions) ? result.sessions : []);
    } catch {
      setStoredSessions([]);
    }
  };

  const loadAddedLocations = async () => {
    try {
      const response = await fetch(`${apiOrigin()}/api/locations`);
      if (!response.ok) return;
      const result = await response.json();
      const added = result.added && typeof result.added === 'object' ? result.added : {};
      setAddedLocations(
        Object.entries(added).map(([name, address]) => ({ name, address: String(address) }))
      );
    } catch {
      setAddedLocations([]);
    }
  };

  useEffect(() => {
    loadStoredSessions();
    loadAddedLocations();
  }, []);

  const handleAddLocation = async () => {
    try {
      const response = await fetch(`${apiOrigin()}/api/locations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: locationName, address: locationAddress }),
      });
      const result = await response.json();
      if (!response.ok || result.status === 'error') {
        setLocationMessage(`❌ ${result.message || 'The location was not added.'}`);
        return;
      }
      setLocationName('');
      setLocationAddress('');
      setLocationMessage(`✅ ${result.message}`);
      loadAddedLocations();
    } catch (error) {
      setLocationMessage(`❌ Could not add the location: ${error}`);
    }
  };

  const handleRemoveLocation = async (name: string) => {
    if (!window.confirm(`Remove ${name} from the location list?`)) return;
    try {
      const response = await fetch(`${apiOrigin()}/api/locations/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const result = await response.json();
      if (!response.ok || result.status === 'error') {
        setLocationMessage(`❌ ${result.message || 'The location was not removed.'}`);
        return;
      }
      setLocationMessage(`✅ ${result.message}`);
      loadAddedLocations();
    } catch (error) {
      setLocationMessage(`❌ Could not remove the location: ${error}`);
    }
  };

  const handleDownloadSession = async (sessionName: string, label: string) => {
    try {
      const response = await fetch(`${apiOrigin()}/api/perfectmind/sessions/download?session=${encodeURIComponent(sessionName)}`);
      if (!response.ok) {
        setProgramMessage('❌ The session file could not be saved.');
        return;
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${label.replace(/\s+/g, '-')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setProgramMessage(`✅ Saved ${label} to your computer.`);
    } catch (error) {
      setProgramMessage(`❌ Could not save the file: ${error}`);
    }
  };

  const handleDeleteSession = async (sessionName: string, label: string) => {
    if (!window.confirm(`Delete ${label} from the test database? Save it to your computer first if you still need it.`)) {
      return;
    }
    try {
      const response = await fetch(`${apiOrigin()}/api/perfectmind/sessions/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session: sessionName }),
      });
      const result = await response.json();
      if (!response.ok || result.status === 'error') {
        setProgramMessage(`❌ ${result.message || 'The session was not deleted.'}`);
        return;
      }
      setProgramMessage(`✅ ${result.message}`);
      loadStoredSessions();
    } catch (error) {
      setProgramMessage(`❌ Could not delete the session: ${error}`);
    }
  };

  const handleGetPrograms = async () => {
    if (typedSessions.length === 0) {
      setProgramMessage('❌ Type a session, such as Session 1-2028.');
      return;
    }
    setProgramBusy(true);
    setProgramMessage('Asking PerfectMind for the program list. A window will open on this computer.');
    try {
      const response = await fetch(`${apiOrigin()}/api/perfectmind/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seasons: typedSessions }),
      });
      const result = await response.json();
      if (!response.ok) {
        setProgramMessage(`❌ ${result.message || 'The test site could not start PerfectMind.'}`);
        setProgramBusy(false);
        return;
      }
      showProgramStatus(result);
    } catch (error) {
      setProgramMessage(`❌ Could not reach the test site: ${error}`);
      setProgramBusy(false);
    }
  };

  // Events file handlers
  const handleEventsFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedEventsFile(file);
      setEventsMessage(`Selected: ${file.name}`);
    }
  };

  const handleEventsUpload = async () => {
    if (!selectedEventsFile) {
      setEventsMessage('Please select a file first');
      return;
    }

    setEventsMessage('📤 Uploading Events JSON file...');

    try {
      const formData = new FormData();
      formData.append('file', selectedEventsFile);

      const response = await fetch(`${apiOrigin()}/api/events/import`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setEventsMessage(`✅ Saved ${selectedEventsFile.name} to the database.\n${result.message || ''}\nTotal events: ${result.total_events || 0}`);
      } else {
        setEventsMessage(`❌ Upload failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      setEventsMessage(`❌ Upload error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        background: 'white',
        borderRadius: '20px',
        padding: '30px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
      }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '30px',
          borderBottom: '2px solid #f0f0f0',
          paddingBottom: '20px'
        }}>
          <h1 style={{ 
            color: '#333', 
            margin: 0,
            fontSize: '2rem',
            fontWeight: 'bold'
          }}>
            🔧 Admin Panel
          </h1>
          <div style={{ display: 'flex', gap: '10px' }}>
            {onViewPrintList && (
              <button
                onClick={onViewPrintList}
                style={{
                  background: '#4caf50',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              >
                📋 Program Guide View
              </button>
            )}
            <button
              onClick={onBackToMain}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              ← Back to App
            </button>
          </div>
        </div>

        {/* Two Column Layout for Excel and Events */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '30px'
        }}>
          
          {/* ==================== PERFECTMIND PROGRAMS ==================== */}
          <div style={{
            background: '#f8f9fa',
            padding: '25px',
            borderRadius: '15px',
            border: '2px solid #007bff'
          }}>
            <h2 style={{ 
              color: '#007bff', 
              marginBottom: '20px',
              fontSize: '1.5rem'
            }}>
              Get programs from PerfectMind
            </h2>
            <p style={{ 
              color: '#666', 
              marginBottom: '20px',
              lineHeight: '1.6'
            }}>
              Type each session you want to show, such as Session 2-2026. Other sessions stay saved in the database and are hidden from the class list. You can save a hidden session to your computer, then delete it from the database.
            </p>
            <div style={{
              border: '2px dashed #007bff',
              borderRadius: '10px',
              padding: '20px',
              textAlign: 'left',
              background: 'white'
            }}>
              <p style={{ color: '#666', marginBottom: '15px', textAlign: 'center' }}>
                A window opens on this computer. Stay nearby if PerfectMind asks you to check the login.
              </p>
              {sessionInputs.map((value, index) => (
                <label key={index} style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                  {index === 0 ? 'Session' : `Session ${index + 1}`}
                  <span style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                    <input
                      type="text"
                      value={value}
                      disabled={programBusy}
                      placeholder="Session 1-2028"
                      onChange={(event) => {
                        const next = [...sessionInputs];
                        next[index] = event.target.value;
                        setSessionInputs(next);
                      }}
                      style={{ flex: 1, padding: '8px' }}
                    />
                    {sessionInputs.length > 1 && (
                      <button
                        type="button"
                        disabled={programBusy}
                        onClick={() => setSessionInputs(sessionInputs.filter((_, item) => item !== index))}
                        style={{ padding: '8px 12px' }}
                      >
                        Remove
                      </button>
                    )}
                  </span>
                </label>
              ))}
              <button
                type="button"
                disabled={programBusy}
                onClick={() => setSessionInputs([...sessionInputs, ''])}
                style={{
                  background: 'white',
                  color: '#007bff',
                  border: '1px solid #007bff',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  cursor: programBusy ? 'not-allowed' : 'pointer',
                  marginBottom: '16px'
                }}
              >
                Add another session
              </button>
              <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                Schedule
                <select
                  value={frequency}
                  disabled={programBusy}
                  onChange={(event) => setFrequency(event.target.value)}
                  style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
                >
                  <option value="off">Only when I click</option>
                  <option value="daily">Every day at a time</option>
                  <option value="interval">Every few hours</option>
                  <option value="weekly">Once a week</option>
                </select>
              </label>
              {frequency === 'weekly' && (
                <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                  Day
                  <select
                    value={weekday}
                    disabled={programBusy}
                    onChange={(event) => setWeekday(event.target.value)}
                    style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
                  >
                    <option value="monday">Monday</option>
                    <option value="tuesday">Tuesday</option>
                    <option value="wednesday">Wednesday</option>
                    <option value="thursday">Thursday</option>
                    <option value="friday">Friday</option>
                    <option value="saturday">Saturday</option>
                    <option value="sunday">Sunday</option>
                  </select>
                </label>
              )}
              {(frequency === 'daily' ? scheduleTimes : frequency === 'weekly' ? scheduleTimes.slice(0, 1) : []).map((value, index) => (
                <label key={index} style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                  {frequency === 'daily' && scheduleTimes.length > 1 ? `Time ${index + 1}` : 'Time'}
                  <span style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                    <input
                      type="time"
                      value={value}
                      disabled={programBusy}
                      onChange={(event) => {
                        const next = [...scheduleTimes];
                        next[index] = event.target.value;
                        setScheduleTimes(next);
                      }}
                      style={{ flex: 1, padding: '8px' }}
                    />
                    {frequency === 'daily' && scheduleTimes.length > 1 && (
                      <button
                        type="button"
                        disabled={programBusy}
                        onClick={() => setScheduleTimes(scheduleTimes.filter((_, item) => item !== index))}
                        style={{ padding: '8px 12px' }}
                      >
                        Remove
                      </button>
                    )}
                  </span>
                </label>
              ))}
              {frequency === 'daily' && (
                <button
                  type="button"
                  disabled={programBusy}
                  onClick={() => setScheduleTimes([...scheduleTimes, '13:00'])}
                  style={{
                    background: 'white',
                    color: '#007bff',
                    border: '1px solid #007bff',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    cursor: programBusy ? 'not-allowed' : 'pointer',
                    marginBottom: '12px'
                  }}
                >
                  Add another time
                </button>
              )}
              {frequency === 'interval' && (
                <div>
                  <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                    Every how many hours
                    <input
                      type="number"
                      min={1}
                      max={24}
                      value={intervalHours}
                      disabled={programBusy}
                      onChange={(event) => setIntervalHours(event.target.value)}
                      style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
                    />
                  </label>
                  <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                    From
                    <input
                      type="time"
                      value={windowStart}
                      disabled={programBusy}
                      onChange={(event) => setWindowStart(event.target.value)}
                      style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
                    />
                  </label>
                  <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
                    Until
                    <input
                      type="time"
                      value={windowEnd}
                      disabled={programBusy}
                      onChange={(event) => setWindowEnd(event.target.value)}
                      style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
                    />
                  </label>
                  <p style={{ color: '#666', fontSize: '14px', margin: '0 0 8px' }}>
                    For example, every 12 hours from 8:00 AM until 8:00 PM runs at those two times. Every 1 hour runs once each hour between the times you set.
                  </p>
                </div>
              )}
              <label style={{ display: 'block', color: '#333', fontSize: '15px', margin: '8px 0 12px' }}>
                <input
                  type="checkbox"
                  checked={skipWeekends}
                  disabled={programBusy}
                  onChange={(event) => setSkipWeekends(event.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                Turn off Saturday and Sunday
              </label>
              <p style={{ color: '#333', fontSize: '14px', margin: '8px 0 12px' }}>{scheduleSummary}</p>
              <button
                onClick={handleSaveSchedule}
                disabled={programBusy}
                style={{
                  background: '#0072ce',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: programBusy ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                  width: '100%',
                  marginBottom: '10px'
                }}
              >
                Save schedule
              </button>
              <button 
                onClick={handleGetPrograms}
                disabled={programBusy}
                style={{
                  background: programBusy ? '#6c757d' : '#007bff',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: programBusy ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                  marginTop: '10px',
                  width: '100%'
                }}
              >
                {programBusy ? 'Getting programs...' : 'Get programs from PerfectMind'}
              </button>
            </div>
            
            {storedSessions.length > 0 && (
              <div style={{ marginTop: '20px' }}>
                <h3 style={{ color: '#333', fontSize: '1.1rem', marginBottom: '10px' }}>Saved sessions</h3>
                <p style={{ color: '#666', fontSize: '14px', marginTop: 0 }}>
                  Showing means it is on the class list. Hidden sessions are still in the database.
                </p>
                {storedSessions.map((item) => (
                  <div key={item.session} style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '8px',
                    alignItems: 'center',
                    marginBottom: '10px',
                    padding: '10px',
                    background: 'white',
                    borderRadius: '8px'
                  }}>
                    <span style={{ flex: '1 1 180px', color: '#333' }}>
                      {item.label} ({item.count}) {item.showing ? 'Showing' : 'Hidden'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDownloadSession(item.session, item.label)}
                      style={{ background: '#0072ce', color: 'white', border: 'none', borderRadius: '6px', padding: '8px 12px', cursor: 'pointer' }}
                    >
                      Save to my computer
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteSession(item.session, item.label)}
                      style={{ background: '#b42318', color: 'white', border: 'none', borderRadius: '6px', padding: '8px 12px', cursor: 'pointer' }}
                    >
                      Delete from database
                    </button>
                  </div>
                ))}
              </div>
            )}
            {programMessage && (
              <div style={{
                marginTop: '15px',
                padding: '12px',
                background: programMessage.includes('✅') ? '#d4edda' : programMessage.includes('❌') ? '#f8d7da' : '#d1ecf1',
                border: `1px solid ${programMessage.includes('✅') ? '#c3e6cb' : programMessage.includes('❌') ? '#f5c6cb' : '#bee5eb'}`,
                borderRadius: '8px',
                color: programMessage.includes('✅') ? '#155724' : programMessage.includes('❌') ? '#721c24' : '#0c5460',
                whiteSpace: 'pre-line',
                fontSize: '14px'
              }}>
                {programMessage}
              </div>
            )}
          </div>

          {/* ==================== EVENTS FILE UPLOAD SECTION ==================== */}
          <div style={{
            background: '#f8f9fa',
            padding: '25px',
            borderRadius: '15px',
            border: '2px solid #28a745'
          }}>
            <h2 style={{ 
              color: '#28a745', 
              marginBottom: '20px',
              fontSize: '1.5rem'
            }}>
              📅 Events File Upload
            </h2>
            
            {/* Manual Scraping Instructions */}
            <div style={{
              background: '#e3f2fd',
              border: '2px solid #2196f3',
              borderRadius: '10px',
              padding: '15px',
              marginBottom: '20px'
            }}>
              <p style={{ color: '#1565c0', marginBottom: '10px', fontSize: '14px', fontWeight: 'bold' }}>
                📋 How to Scrape Events (Manual Steps):
              </p>
              <ol style={{ 
                color: '#1565c0', 
                margin: '0', 
                paddingLeft: '20px',
                fontSize: '13px',
                lineHeight: '1.8'
              }}>
                <li>Open <strong>Command Prompt</strong> or <strong>Terminal</strong> on your computer</li>
                <li>Navigate to your project folder:<br/>
                  <code style={{ background: '#bbdefb', padding: '2px 6px', borderRadius: '3px' }}>cd "S:\Rebecca\Class Cancellation app"</code>
                </li>
                <li>Run the scraping script:<br/>
                  <code style={{ background: '#bbdefb', padding: '2px 6px', borderRadius: '3px' }}>python create_uploadable_events_file.py</code>
                </li>
                <li>Wait for scraping to complete (creates <code>scraped_events_for_upload.json</code>)</li>
                <li>Upload the file below</li>
              </ol>
            </div>
            
            {/* File Upload Section */}
            <div style={{
              border: '2px dashed #28a745',
              borderRadius: '10px',
              padding: '20px',
              textAlign: 'center',
              background: 'white'
            }}>
              <p style={{ color: '#666', marginBottom: '15px' }}>
                Select <code>scraped_events_for_upload.json</code> file
              </p>
              <input
                type="file"
                accept=".json"
                onChange={handleEventsFileSelect}
                style={{
                  margin: '10px 0',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '5px',
                  width: '100%'
                }}
              />
              <button 
                onClick={handleEventsUpload}
                disabled={!selectedEventsFile}
                style={{
                  background: selectedEventsFile ? '#28a745' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: selectedEventsFile ? 'pointer' : 'not-allowed',
                  fontSize: '16px',
                  marginTop: '10px',
                  width: '100%'
                }}
              >
                Upload JSON File
              </button>
            </div>
            
            <p style={{ 
              color: '#666', 
              fontSize: '12px',
              marginTop: '15px',
              textAlign: 'center'
            }}>
              The events file is saved to the database as soon as the upload finishes.
            </p>
            
            {/* Events Status Message */}
            {eventsMessage && (
              <div style={{
                marginTop: '15px',
                padding: '12px',
                background: eventsMessage.includes('✅') ? '#d4edda' : eventsMessage.includes('❌') ? '#f8d7da' : '#d1ecf1',
                border: `1px solid ${eventsMessage.includes('✅') ? '#c3e6cb' : eventsMessage.includes('❌') ? '#f5c6cb' : '#bee5eb'}`,
                borderRadius: '8px',
                color: eventsMessage.includes('✅') ? '#155724' : eventsMessage.includes('❌') ? '#721c24' : '#0c5460',
                whiteSpace: 'pre-line',
                fontSize: '14px'
              }}>
                {eventsMessage}
                <button 
                  onClick={() => setEventsMessage('')}
                  style={{
                    display: 'block',
                    marginTop: '10px',
                    background: '#6c757d',
                    color: 'white',
                    border: 'none',
                    padding: '5px 10px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        <div style={{
          background: '#f8f9fa',
          padding: '25px',
          borderRadius: '15px',
          border: '2px solid #007bff',
          marginTop: '30px'
        }}>
          <h2 style={{ color: '#333', marginTop: 0 }}>Add a location</h2>
          <p style={{ color: '#666', fontSize: '14px' }}>
            Type the location the same way it appears on the class, such as Hall - New Room. Then type the address people should see when they click that location. The original locations stay in the list.
          </p>
          <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '8px' }}>
            Location name
            <input
              value={locationName}
              onChange={(event) => setLocationName(event.target.value)}
              placeholder="Hall - New Room"
              style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
            />
          </label>
          <label style={{ display: 'block', color: '#333', fontSize: '15px', marginBottom: '12px' }}>
            Address
            <input
              value={locationAddress}
              onChange={(event) => setLocationAddress(event.target.value)}
              placeholder="12 Main Street, Kingston, ON"
              style={{ display: 'block', width: '100%', marginTop: '6px', padding: '8px' }}
            />
          </label>
          <button
            type="button"
            onClick={handleAddLocation}
            style={{
              background: '#0072ce',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 24px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Add location
          </button>
          {locationMessage && (
            <p style={{ color: '#333', fontSize: '14px' }}>{locationMessage}</p>
          )}
          {addedLocations.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              {addedLocations.map((item) => (
                <div key={item.name} style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                  alignItems: 'center',
                  marginBottom: '10px',
                  padding: '10px',
                  background: 'white',
                  borderRadius: '8px'
                }}>
                  <span style={{ flex: '1 1 220px', color: '#333' }}>{item.name} — {item.address}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveLocation(item.name)}
                    style={{ background: '#b42318', color: 'white', border: 'none', borderRadius: '6px', padding: '8px 12px', cursor: 'pointer' }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>


      </div>
    </div>
  );
};

export default AdminPanel;
