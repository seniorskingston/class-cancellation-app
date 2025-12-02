import React, { useState } from 'react';

interface AdminPanelProps {
  onBackToMain: () => void;
  onViewPrintList?: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ onBackToMain, onViewPrintList }) => {
  // Separate state for each section
  const [selectedExcelFile, setSelectedExcelFile] = useState<File | null>(null);
  const [excelMessage, setExcelMessage] = useState('');
  
  const [selectedEventsFile, setSelectedEventsFile] = useState<File | null>(null);
  const [eventsMessage, setEventsMessage] = useState('');
  
  const [gcsMessage, setGcsMessage] = useState('');

  // Excel file handlers
  const handleExcelFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedExcelFile(file);
      setExcelMessage(`Selected: ${file.name}`);
    }
  };

  const handleExcelUpload = async () => {
    if (!selectedExcelFile) {
      setExcelMessage('Please select a file first');
      return;
    }

    setExcelMessage('📤 Uploading Excel file...');

    try {
      const formData = new FormData();
      formData.append('file', selectedExcelFile);

      const response = await fetch('https://class-cancellation-backend.onrender.com/api/import-excel', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        if (result.status === 'success') {
          setExcelMessage(`✅ Successfully uploaded ${selectedExcelFile.name}!\n${result.message || ''}\n\n💡 Now click "Upload Excel to GCS" in the Google Cloud section to save permanently.`);
        } else {
          setExcelMessage(`❌ Upload failed: ${result.message || 'Unknown error'}`);
        }
      } else {
        setExcelMessage(`❌ Upload failed: ${response.statusText}`);
      }
    } catch (error) {
      setExcelMessage(`❌ Upload error: ${error}`);
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

      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events/import', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setEventsMessage(`✅ Successfully uploaded ${selectedEventsFile.name}!\n${result.message || ''}\nTotal events: ${result.total_events || 0}\n\n💡 Now click "Upload Events to GCS" in the Google Cloud section to save permanently.`);
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
                🖨️ Print Program List
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
          
          {/* ==================== EXCEL FILE UPLOAD SECTION ==================== */}
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
              📊 Excel File Upload
            </h2>
            <p style={{ 
              color: '#666', 
              marginBottom: '20px',
              lineHeight: '1.6'
            }}>
              Upload your Excel file to update the program schedule data. After uploading, click "Upload Excel to GCS" below to save permanently.
            </p>
            <div style={{
              border: '2px dashed #007bff',
              borderRadius: '10px',
              padding: '20px',
              textAlign: 'center',
              background: 'white'
            }}>
              <p style={{ color: '#666', marginBottom: '15px' }}>
                Select your Excel file (.xlsx, .xls)
              </p>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleExcelFileSelect}
                style={{
                  margin: '10px 0',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '5px',
                  width: '100%'
                }}
              />
              <button 
                onClick={handleExcelUpload}
                disabled={!selectedExcelFile}
                style={{
                  background: selectedExcelFile ? '#007bff' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: selectedExcelFile ? 'pointer' : 'not-allowed',
                  fontSize: '16px',
                  marginTop: '10px',
                  width: '100%'
                }}
              >
                Upload Excel File
              </button>
            </div>
            
            {/* Excel Status Message */}
            {excelMessage && (
              <div style={{
                marginTop: '15px',
                padding: '12px',
                background: excelMessage.includes('✅') ? '#d4edda' : excelMessage.includes('❌') ? '#f8d7da' : '#d1ecf1',
                border: `1px solid ${excelMessage.includes('✅') ? '#c3e6cb' : excelMessage.includes('❌') ? '#f5c6cb' : '#bee5eb'}`,
                borderRadius: '8px',
                color: excelMessage.includes('✅') ? '#155724' : excelMessage.includes('❌') ? '#721c24' : '#0c5460',
                whiteSpace: 'pre-line',
                fontSize: '14px'
              }}>
                {excelMessage}
                <button 
                  onClick={() => setExcelMessage('')}
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
              💡 After uploading, click <strong>"Upload Events to GCS"</strong> in the Google Cloud section below to save permanently.
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

        {/* ==================== GOOGLE CLOUD STORAGE SECTION ==================== */}
        <div style={{
          background: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)',
          padding: '25px',
          borderRadius: '15px',
          border: '2px solid #4caf50',
          marginTop: '30px'
        }}>
          <h2 style={{ 
            color: '#2e7d32', 
            marginBottom: '20px',
            fontSize: '1.5rem'
          }}>
            ☁️ Google Cloud Storage (Permanent Storage)
          </h2>
          <p style={{ 
            color: '#1b5e20', 
            marginBottom: '20px',
            lineHeight: '1.6'
          }}>
            <strong>🔒 Permanent Storage:</strong> After uploading Excel or Events files above, click the buttons below to save them to Google Cloud Storage. 
            Data stored here will <strong>NEVER disappear</strong>.
          </p>
          
          {/* Two Column Layout - Excel Left, Events Right */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '15px',
            marginBottom: '20px'
          }}>
            {/* Excel Column - LEFT */}
            <div style={{
              background: 'rgba(255,255,255,0.7)',
              padding: '15px',
              borderRadius: '10px',
              border: '1px solid #ff9800'
            }}>
              <h4 style={{ color: '#e65100', marginBottom: '10px', fontSize: '14px' }}>📊 Excel Data</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button 
                  onClick={async () => {
                    try {
                      setGcsMessage('☁️ Uploading Excel data to Google Cloud Storage...');
                      const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/upload-excel', {
                        method: 'POST'
                      });
                      const result = await response.json();
                      if (result.success) {
                        setGcsMessage(`✅ ${result.message}\n\n☁️ Bucket: ${result.bucket}\n📁 File: ${result.filename}\n📊 Total programs: ${result.total_programs}`);
                      } else {
                        setGcsMessage(`❌ Failed to upload Excel to GCS: ${result.error}`);
                      }
                    } catch (error) {
                      setGcsMessage(`❌ Error uploading to GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                  }}
                  style={{
                    background: '#ff9800',
                    color: 'white',
                    border: 'none',
                    padding: '10px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 'bold',
                    width: '100%'
                  }}
                >
                  ☁️ Upload Excel to GCS
                </button>
                
                <button 
                  onClick={async () => {
                    try {
                      setGcsMessage('☁️ Downloading Excel data from Google Cloud Storage...');
                      const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/download-excel', {
                        method: 'POST'
                      });
                      const result = await response.json();
                      if (result.success) {
                        setGcsMessage(`✅ ${result.message}\n\n☁️ Downloaded from: ${result.bucket}/${result.filename}\n📊 Total programs: ${result.total_programs}`);
                      } else {
                        setGcsMessage(`❌ Failed to download Excel from GCS: ${result.error}`);
                      }
                    } catch (error) {
                      setGcsMessage(`❌ Error downloading from GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                  }}
                  style={{
                    background: '#9c27b0',
                    color: 'white',
                    border: 'none',
                    padding: '10px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 'bold',
                    width: '100%'
                  }}
                >
                  📥 Download Excel from GCS
                </button>
              </div>
            </div>
            
            {/* Events Column - RIGHT */}
            <div style={{
              background: 'rgba(255,255,255,0.7)',
              padding: '15px',
              borderRadius: '10px',
              border: '1px solid #4caf50'
            }}>
              <h4 style={{ color: '#2e7d32', marginBottom: '10px', fontSize: '14px' }}>📅 Events Data</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button 
                  onClick={async () => {
                    try {
                      setGcsMessage('☁️ Uploading events to Google Cloud Storage...');
                      const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/upload-events', {
                        method: 'POST'
                      });
                      const result = await response.json();
                      if (result.success) {
                        setGcsMessage(`✅ ${result.message}\n\n☁️ Bucket: ${result.bucket}\n📁 File: ${result.filename}\n📊 Total events: ${result.total_events}`);
                      } else {
                        setGcsMessage(`❌ Failed to upload events to GCS: ${result.error}`);
                      }
                    } catch (error) {
                      setGcsMessage(`❌ Error uploading to GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                  }}
                  style={{
                    background: '#4caf50',
                    color: 'white',
                    border: 'none',
                    padding: '10px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 'bold',
                    width: '100%'
                  }}
                >
                  ☁️ Upload Events to GCS
                </button>
                
                <button 
                  onClick={async () => {
                    try {
                      setGcsMessage('☁️ Downloading events from Google Cloud Storage...');
                      const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/download-events', {
                        method: 'POST'
                      });
                      const result = await response.json();
                      if (result.success) {
                        setGcsMessage(`✅ ${result.message}\n\n☁️ Downloaded from: ${result.bucket}/${result.filename}\n📊 Total events: ${result.total_events}`);
                      } else {
                        setGcsMessage(`❌ Failed to download events from GCS: ${result.error}`);
                      }
                    } catch (error) {
                      setGcsMessage(`❌ Error downloading from GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                  }}
                  style={{
                    background: '#2196f3',
                    color: 'white',
                    border: 'none',
                    padding: '10px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 'bold',
                    width: '100%'
                  }}
                >
                  📥 Download Events from GCS
                </button>
              </div>
            </div>
          </div>
          
          {/* Sync All - When to use explanation */}
          <div style={{
            background: '#fff8e1',
            border: '1px solid #ffc107',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '15px'
          }}>
            <p style={{ color: '#856404', margin: 0, fontSize: '13px' }}>
              <strong>🔄 When to use "Sync ALL Data from GCS":</strong><br/>
              Use this button when the app <strong>restarts</strong> or when data appears <strong>missing/empty</strong>. 
              It loads both Excel and Events data from Google Cloud back into the app.
            </p>
          </div>
          
          {/* Sync and Status Row */}
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap'
          }}>
            <button 
              onClick={async () => {
                try {
                  setGcsMessage('☁️ Syncing ALL data from Google Cloud Storage...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/sync-all', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    let message = '✅ Sync completed!\n\n';
                    if (result.results?.events?.success) {
                      message += `📅 Events: ${result.results.events.total_events} events loaded\n`;
                    } else {
                      message += `📅 Events: ${result.results?.events?.error || 'Failed'}\n`;
                    }
                    if (result.results?.excel?.success) {
                      message += `📊 Excel: ${result.results.excel.total_programs} programs loaded`;
                    } else {
                      message += `📊 Excel: ${result.results?.excel?.error || 'Failed'}`;
                    }
                    setGcsMessage(message);
                  } else {
                    setGcsMessage(`❌ Sync failed: ${result.error}`);
                  }
                } catch (error) {
                  setGcsMessage(`❌ Error syncing from GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                }
              }}
              style={{
                background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
                color: 'white',
                border: 'none',
                padding: '15px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold',
                flex: '1',
                minWidth: '200px',
                boxShadow: '0 4px 15px rgba(76, 175, 80, 0.4)'
              }}
            >
              🔄 Sync ALL Data from GCS
            </button>
            
            <button 
              onClick={async () => {
                try {
                  setGcsMessage('☁️ Checking Google Cloud Storage status...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/status');
                  const status = await response.json();
                  
                  if (status.success && status.connected) {
                    let message = '☁️ Google Cloud Storage Status:\n\n';
                    message += `✅ Connected to bucket: ${status.bucket_name}\n\n`;
                    message += `📁 Files in bucket: ${status.files_count}\n`;
                    message += `📅 Events file: ${status.events_file_exists ? '✅ Exists' : '❌ Not found'}\n`;
                    message += `📊 Excel file: ${status.excel_file_exists ? '✅ Exists' : '❌ Not found'}\n`;
                    
                    if (status.files && status.files.length > 0) {
                      message += '\n📋 Files:\n';
                      status.files.slice(0, 5).forEach((file: any) => {
                        message += `  • ${file.name} (${file.size} bytes)\n`;
                      });
                      if (status.files.length > 5) {
                        message += `  ... and ${status.files.length - 5} more files`;
                      }
                    }
                    
                    setGcsMessage(message);
                  } else {
                    let errorMsg = `❌ GCS not connected\n\n`;
                    errorMsg += status.error || 'Unknown error';
                    
                    if (status.debug) {
                      errorMsg += `\n\n🔍 Debug Info:\n`;
                      errorMsg += `• GCS_CREDENTIALS set: ${status.debug.GCS_CREDENTIALS_env_set ? 'Yes' : 'No'}\n`;
                      errorMsg += `• Credentials length: ${status.debug.GCS_CREDENTIALS_length || 0} chars\n`;
                      errorMsg += `• Bucket name: ${status.debug.GCS_BUCKET_NAME || 'Not set'}\n`;
                      errorMsg += `• Library available: ${status.debug.GCS_AVAILABLE_library ? 'Yes' : 'No'}`;
                    }
                    
                    setGcsMessage(errorMsg);
                  }
                } catch (error) {
                  setGcsMessage(`❌ Error checking GCS status: ${error instanceof Error ? error.message : 'Unknown error'}`);
                }
              }}
              style={{
                background: '#607d8b',
                color: 'white',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                flex: '1',
                minWidth: '180px'
              }}
            >
              📊 Check GCS Status
            </button>
          </div>
          
          {/* GCS Status Message */}
          {gcsMessage && (
            <div style={{
              marginTop: '15px',
              padding: '12px',
              background: gcsMessage.includes('✅') ? '#d4edda' : gcsMessage.includes('❌') ? '#f8d7da' : '#d1ecf1',
              border: `1px solid ${gcsMessage.includes('✅') ? '#c3e6cb' : gcsMessage.includes('❌') ? '#f5c6cb' : '#bee5eb'}`,
              borderRadius: '8px',
              color: gcsMessage.includes('✅') ? '#155724' : gcsMessage.includes('❌') ? '#721c24' : '#0c5460',
              whiteSpace: 'pre-line',
              fontSize: '14px'
            }}>
              {gcsMessage}
              <button 
                onClick={() => setGcsMessage('')}
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
          
          {/* Setup Instructions */}
          <div style={{ 
            marginTop: '20px',
            padding: '15px',
            background: '#fff8e1',
            border: '1px solid #ffcc02',
            borderRadius: '8px',
            fontSize: '0.85rem'
          }}>
            <strong>📋 Setup Instructions for Render:</strong>
            <ol style={{ margin: '10px 0 0 0', paddingLeft: '20px' }}>
              <li>Go to Render Dashboard → Your Backend Service → Environment</li>
              <li>Add environment variable: <code>GCS_BUCKET_NAME</code> = your-bucket-name</li>
              <li>Add environment variable: <code>GCS_CREDENTIALS</code> = (paste the ENTIRE content of your Google service account JSON key file)</li>
              <li>Save and wait for redeploy</li>
              <li>Click "Check GCS Status" to verify connection</li>
            </ol>
          </div>
        </div>

      </div>
    </div>
  );
};

export default AdminPanel;
