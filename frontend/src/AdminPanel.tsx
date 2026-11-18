import React, { useEffect, useState } from 'react';
import { apiOrigin } from './apiOrigin';

interface AdminPanelProps {
  onBackToMain: () => void;
  onViewPrintList?: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ onBackToMain, onViewPrintList }) => {
  const [programMessage, setProgramMessage] = useState('');
  const [programBusy, setProgramBusy] = useState(false);
  const [selectedEventsFile, setSelectedEventsFile] = useState<File | null>(null);
  const [eventsMessage, setEventsMessage] = useState('');

  const showProgramStatus = (result: { status?: string; message?: string }) => {
    const message = result.message || 'Waiting for PerfectMind.';
    if (result.status === 'success') {
      setProgramMessage(`✅ ${message}`);
      setProgramBusy(false);
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

  const handleGetPrograms = async () => {
    setProgramBusy(true);
    setProgramMessage('Asking PerfectMind for the program list. A window will open on this computer.');
    try {
      const response = await fetch(`${apiOrigin()}/api/perfectmind/sync`, { method: 'POST' });
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
              This reads Session 1 and Session 2 for 2026 from PerfectMind and saves them on the test website. It does not use an Excel file, and it does not change the live website. Notes and cancellation dates already entered are kept.
            </p>
            <div style={{
              border: '2px dashed #007bff',
              borderRadius: '10px',
              padding: '20px',
              textAlign: 'center',
              background: 'white'
            }}>
              <p style={{ color: '#666', marginBottom: '15px' }}>
                A window opens on this computer. Stay nearby if PerfectMind asks you to check the login.
              </p>
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


      </div>
    </div>
  );
};

export default AdminPanel;
