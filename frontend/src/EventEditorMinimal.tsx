import React from 'react';

interface EventEditorMinimalProps {
  isOpen: boolean;
  onClose: () => void;
}

const EventEditorMinimal: React.FC<EventEditorMinimalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      zIndex: 1000,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <div style={{
        background: 'white',
        padding: '50px',
        borderRadius: '10px',
        maxWidth: '90%',
        maxHeight: '90%',
        overflow: 'auto'
      }}>
        <h1 style={{ color: 'red', fontSize: '30px', textAlign: 'center' }}>
          🚨 MINIMAL EVENT EDITOR 🚨
        </h1>
        <p style={{ fontSize: '20px', margin: '20px 0', textAlign: 'center' }}>
          This is a minimal test version of the Event Editor.
        </p>
        <p style={{ fontSize: '16px', margin: '20px 0', textAlign: 'center' }}>
          If you see this, the component system is working!
        </p>
        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <button 
            onClick={() => {
              alert('MINIMAL TEST BUTTON WORKS!');
            }}
            style={{
              background: 'green',
              color: 'white',
              padding: '20px 40px',
              fontSize: '20px',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              marginRight: '20px'
            }}
          >
            🧪 TEST BUTTON
          </button>
          <button 
            onClick={onClose}
            style={{
              background: 'red',
              color: 'white',
              padding: '20px 40px',
              fontSize: '20px',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            ❌ CLOSE
          </button>
        </div>
      </div>
    </div>
  );
};

export default EventEditorMinimal;
