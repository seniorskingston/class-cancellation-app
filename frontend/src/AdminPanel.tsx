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

        {/* Event Management Section */}
        <div style={{
          background: '#f8f9fa',
          padding: '25px',
          borderRadius: '15px',
          border: '2px solid #e9ecef',
          maxWidth: '600px',
          margin: '0 auto'
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
