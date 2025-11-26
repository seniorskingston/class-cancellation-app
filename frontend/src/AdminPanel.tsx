import React, { useState } from 'react';
import EventEditor from './EventEditor';
import EventEditorFixed from './EventEditorFixed';

interface AdminPanelProps {
  onBackToMain: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ onBackToMain }) => {
  const [showEventEditor, setShowEventEditor] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadMessage(`Selected: ${file.name}`);
    }
  };

  const clearMessage = () => {
    setUploadMessage('');
  };

  const handleExcelUpload = async () => {
    if (!selectedFile) {
      setUploadMessage('Please select a file first');
      return;
    }

    setUploadMessage('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Use the working upload endpoint that accepts Excel files
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/import-excel', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        if (result.status === 'success') {
          setUploadMessage(`✅ Successfully uploaded ${selectedFile.name}! ${result.message || ''}`);
        } else {
          setUploadMessage(`❌ Upload failed: ${result.message || 'Unknown error'}`);
        }
      } else {
        setUploadMessage(`❌ Upload failed: ${response.statusText}`);
      }
    } catch (error) {
      setUploadMessage(`❌ Upload error: ${error}`);
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

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '30px'
        }}>
          {/* Excel Upload Section */}
          <div style={{
            background: '#f8f9fa',
            padding: '25px',
            borderRadius: '15px',
            border: '2px solid #e9ecef'
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
              Upload your Excel file to update the program schedule data. Data is saved to the database and fallback files.
            </p>
            <div style={{
              border: '2px dashed #007bff',
              borderRadius: '10px',
              padding: '20px',
              textAlign: 'center',
              background: 'white'
            }}>
              <p style={{ color: '#666', marginBottom: '15px' }}>
                Select your Excel file to upload
              </p>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                style={{
                  margin: '10px 0',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '5px',
                  width: '100%'
                }}
              />
              {uploadMessage && (
                <div style={{ marginTop: '10px' }}>
                  <p style={{ 
                    color: uploadMessage.includes('✅') ? '#28a745' : uploadMessage.includes('❌') ? '#dc3545' : '#666',
                    margin: '0 0 10px 0',
                    fontSize: '14px',
                    whiteSpace: 'pre-line'
                  }}>
                    {uploadMessage}
                  </p>
                  <button 
                    onClick={clearMessage}
                    style={{
                      background: '#6c757d',
                      color: 'white',
                      border: 'none',
                      padding: '5px 10px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    Clear Message
                  </button>
                </div>
              )}
              <button 
                onClick={handleExcelUpload}
                disabled={!selectedFile}
                style={{
                  background: selectedFile ? '#007bff' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: selectedFile ? 'pointer' : 'not-allowed',
                  fontSize: '16px',
                  marginTop: '10px'
                }}
              >
                Upload Excel File
              </button>
            </div>
          </div>

          {/* Event Management Section */}
          <div style={{
            background: '#f8f9fa',
            padding: '25px',
            borderRadius: '15px',
            border: '2px solid #e9ecef'
          }}>
            <h2 style={{ 
              color: '#28a745', 
              marginBottom: '20px',
              fontSize: '1.5rem'
            }}>
              📅 Event Management
            </h2>
            <p style={{ 
              color: '#666', 
              marginBottom: '20px',
              lineHeight: '1.6'
            }}>
              Scrape events from the website, save them locally, and upload them to the app.
            </p>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '15px'
            }}>
              {/* Main Event Management Button */}
              <button 
                onClick={() => setShowEventEditor(true)}
                style={{
                  background: '#007bff',
                  color: 'white',
                  border: 'none',
                  padding: '15px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  boxShadow: '0 2px 8px rgba(0, 123, 255, 0.3)'
                }}
              >
                🔄 Scrape & Edit Events
              </button>
              
              <p style={{ 
                color: '#666', 
                fontSize: '0.9rem',
                margin: '10px 0',
                textAlign: 'center'
              }}>
                Click above to open the Event Editor where you can:<br/>
                • Scrape events and save to local file<br/>
                • Upload scraped events JSON file<br/>
                • Edit and manage events
              </p>
            </div>
          </div>
        </div>

        {/* Fallback Data Management Section */}
        <div style={{
          background: '#f8f9fa',
          padding: '25px',
          borderRadius: '15px',
          border: '2px solid #e9ecef',
          marginTop: '30px'
        }}>
          <h2 style={{ 
            color: '#6f42c1', 
            marginBottom: '20px',
            fontSize: '1.5rem'
          }}>
            💾 Save Data as Fallback (Online Storage)
          </h2>
          <p style={{ 
            color: '#666', 
            marginBottom: '20px',
            lineHeight: '1.6'
          }}>
            <strong>Important:</strong> Save your current data as fallback files. These files are stored online on Render's persistent storage (<code>/tmp</code> directory) and will <strong>NOT disappear</strong> when the app restarts. 
            When scraping fails, the app will automatically use this saved data instead of showing empty results.
          </p>
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap'
          }}>
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('💾 Saving current events as fallback...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/fallback/save-events', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    setUploadMessage(`✅ ${result.message}\n\n📁 Saved to: ${result.fallback_file}\n📊 Total events: ${result.total_events}\n\n💡 This data is stored online and will persist across restarts.`);
                    setTimeout(() => setUploadMessage(''), 8000);
                  } else {
                    setUploadMessage(`❌ Failed to save events fallback: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error saving events fallback: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#6f42c1',
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
              💾 Save Events as Fallback
            </button>
            
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('💾 Saving current Excel data as fallback...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/fallback/save-excel', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    setUploadMessage(`✅ ${result.message}\n\n📁 Saved to: ${result.fallback_file}\n📊 Total programs: ${result.total_programs}\n\n💡 This data is stored online and will persist across restarts.`);
                    setTimeout(() => setUploadMessage(''), 8000);
                  } else {
                    setUploadMessage(`❌ Failed to save Excel fallback: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error saving Excel fallback: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#fd7e14',
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
              💾 Save Excel as Fallback
            </button>
            
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('📊 Checking fallback status...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/fallback/status');
                  const status = await response.json();
                  
                  let message = '📊 Fallback Data Status (Stored Online):\n\n';
                  if (status.events_fallback.file_exists) {
                    message += `✅ Events: ${status.events_fallback.total_events} events\n   Last updated: ${status.events_fallback.last_updated}\n\n`;
                  } else {
                    message += `❌ Events: No fallback data saved yet\n\n`;
                  }
                  
                  if (status.excel_fallback.file_exists) {
                    message += `✅ Excel: ${status.excel_fallback.total_programs} programs\n   Last updated: ${status.excel_fallback.last_updated}`;
                  } else {
                    message += `❌ Excel: No fallback data saved yet`;
                  }
                  
                  message += `\n\n💡 Location: Files are stored in /tmp on Render (persistent storage)`;
                  
                  setUploadMessage(message);
                  setTimeout(() => setUploadMessage(''), 10000);
                } catch (error) {
                  setUploadMessage(`❌ Error checking fallback status: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#20c997',
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
              📊 Check Fallback Status
            </button>
          </div>
        </div>

        {/* Google Cloud Storage Section */}
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
            <strong>🔒 Most Reliable Storage:</strong> Upload your data to Google Cloud Storage for permanent, reliable storage. 
            Data stored here will <strong>NEVER disappear</strong> - even if the app restarts or Render resets. 
            Click "Sync from GCS" to load the latest data from Google Cloud.
          </p>
          
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
            marginBottom: '15px'
          }}>
            {/* Upload Events to GCS */}
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('☁️ Uploading events to Google Cloud Storage...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/upload-events', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    setUploadMessage(`✅ ${result.message}\n\n☁️ Bucket: ${result.bucket}\n📁 File: ${result.filename}\n📊 Total events: ${result.total_events}`);
                    setTimeout(() => setUploadMessage(''), 8000);
                  } else {
                    setUploadMessage(`❌ Failed to upload events to GCS: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error uploading to GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#4caf50',
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
              ☁️ Upload Events to GCS
            </button>
            
            {/* Upload Excel to GCS */}
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('☁️ Uploading Excel data to Google Cloud Storage...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/upload-excel', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    setUploadMessage(`✅ ${result.message}\n\n☁️ Bucket: ${result.bucket}\n📁 File: ${result.filename}\n📊 Total programs: ${result.total_programs}`);
                    setTimeout(() => setUploadMessage(''), 8000);
                  } else {
                    setUploadMessage(`❌ Failed to upload Excel to GCS: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error uploading to GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#ff9800',
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
              ☁️ Upload Excel to GCS
            </button>
          </div>
          
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
            marginBottom: '15px'
          }}>
            {/* Download Events from GCS */}
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('☁️ Downloading events from Google Cloud Storage...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/download-events', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    setUploadMessage(`✅ ${result.message}\n\n☁️ Downloaded from: ${result.bucket}/${result.filename}\n📊 Total events: ${result.total_events}`);
                    setTimeout(() => setUploadMessage(''), 8000);
                  } else {
                    setUploadMessage(`❌ Failed to download events from GCS: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error downloading from GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#2196f3',
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
              📥 Download Events from GCS
            </button>
            
            {/* Download Excel from GCS */}
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('☁️ Downloading Excel data from Google Cloud Storage...');
                  const response = await fetch('https://class-cancellation-backend.onrender.com/api/gcs/download-excel', {
                    method: 'POST'
                  });
                  
                  const result = await response.json();
                  
                  if (result.success) {
                    setUploadMessage(`✅ ${result.message}\n\n☁️ Downloaded from: ${result.bucket}/${result.filename}\n📊 Total programs: ${result.total_programs}`);
                    setTimeout(() => setUploadMessage(''), 8000);
                  } else {
                    setUploadMessage(`❌ Failed to download Excel from GCS: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error downloading from GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
                }
              }}
              style={{
                background: '#9c27b0',
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
              📥 Download Excel from GCS
            </button>
          </div>
          
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap'
          }}>
            {/* Sync All from GCS */}
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('☁️ Syncing ALL data from Google Cloud Storage...');
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
                    setUploadMessage(message);
                    setTimeout(() => setUploadMessage(''), 10000);
                  } else {
                    setUploadMessage(`❌ Sync failed: ${result.error}`);
                    setTimeout(() => setUploadMessage(''), 5000);
                  }
                } catch (error) {
                  setUploadMessage(`❌ Error syncing from GCS: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
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
            
            {/* Check GCS Status */}
            <button 
              onClick={async () => {
                try {
                  setUploadMessage('☁️ Checking Google Cloud Storage status...');
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
                    
                    setUploadMessage(message);
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
                    
                    setUploadMessage(errorMsg);
                  }
                  setTimeout(() => setUploadMessage(''), 15000);
                } catch (error) {
                  setUploadMessage(`❌ Error checking GCS status: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  setTimeout(() => setUploadMessage(''), 5000);
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

        {uploadMessage && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: uploadMessage.includes('✅') ? '#d4edda' : uploadMessage.includes('❌') ? '#f8d7da' : '#d1ecf1',
            border: `1px solid ${uploadMessage.includes('✅') ? '#c3e6cb' : uploadMessage.includes('❌') ? '#f5c6cb' : '#bee5eb'}`,
            borderRadius: '8px',
            color: uploadMessage.includes('✅') ? '#155724' : uploadMessage.includes('❌') ? '#721c24' : '#0c5460'
          }}>
            {uploadMessage}
          </div>
        )}

      </div>

      {/* Event Editor Modal - Using Fixed Version */}
      <EventEditorFixed
        isOpen={showEventEditor}
        onClose={() => setShowEventEditor(false)}
      />
    </div>
  );
};

export default AdminPanel;
