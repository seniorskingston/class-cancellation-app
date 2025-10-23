import React, { useState } from 'react';
import EventEditor from './EventEditor';

interface AdminPanelProps {
  onBackToMain: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ onBackToMain }) => {
  const [showEventEditor, setShowEventEditor] = useState(false);

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
              Upload your Excel file to update the program schedule data.
            </p>
            <div style={{
              border: '2px dashed #007bff',
              borderRadius: '10px',
              padding: '20px',
              textAlign: 'center',
              background: 'white'
            }}>
              <p style={{ color: '#666', marginBottom: '15px' }}>
                Drag & drop your Excel file here or click to browse
              </p>
              <input
                type="file"
                accept=".xlsx,.xls"
                style={{
                  margin: '10px 0',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '5px',
                  width: '100%'
                }}
              />
              <button style={{
                background: '#007bff',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                marginTop: '10px'
              }}>
                Upload Excel File
              </button>
            </div>
          </div>

          {/* Event Editor Section */}
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
              Manage events, upload scraped data, and edit event details.
            </p>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '15px'
            }}>
              <button 
                onClick={() => setShowEventEditor(true)}
                style={{
                  background: '#28a745',
                  color: 'white',
                  border: 'none',
                  padding: '15px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              >
                📥 Load Scraped Events (151 events)
              </button>
              <button 
                onClick={() => setShowEventEditor(true)}
                style={{
                  background: '#17a2b8',
                  color: 'white',
                  border: 'none',
                  padding: '15px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              >
                ✏️ Edit Events
              </button>
              <button style={{
                background: '#ffc107',
                color: '#212529',
                border: 'none',
                padding: '15px 20px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold'
              }}>
                💾 Save All Changes
              </button>
            </div>
          </div>
        </div>

        <div style={{
          marginTop: '30px',
          padding: '20px',
          background: '#e9ecef',
          borderRadius: '10px'
        }}>
          <h3 style={{ color: '#495057', marginBottom: '15px' }}>
            📋 Quick Actions
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '15px'
          }}>
            <button style={{
              background: '#6f42c1',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}>
              🔄 Sync with Website
            </button>
            <button style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}>
              🗑️ Clear All Events
            </button>
            <button style={{
              background: '#20c997',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}>
              📊 View Statistics
            </button>
            <button style={{
              background: '#fd7e14',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}>
              🔧 System Settings
            </button>
          </div>
        </div>
      </div>

      {/* Event Editor Modal */}
      <EventEditor
        isOpen={showEventEditor}
        onClose={() => setShowEventEditor(false)}
      />
    </div>
  );
};

export default AdminPanel;
