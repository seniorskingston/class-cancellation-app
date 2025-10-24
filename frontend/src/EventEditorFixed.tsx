import React, { useState, useEffect } from 'react';
import './EventEditor.css';

interface Event {
  id?: string;
  title: string;
  startDate: string;
  endDate: string;
  description?: string;
  location?: string;
  dateStr?: string;
  timeStr?: string;
  image_url?: string;
  price?: string;
  instructor?: string;
  registration?: string;
}

interface EventEditorFixedProps {
  isOpen: boolean;
  onClose: () => void;
}

const EventEditorFixed: React.FC<EventEditorFixedProps> = ({ isOpen, onClose }) => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | ''>('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [newEvent, setNewEvent] = useState<Event>({
    title: '',
    startDate: '',
    endDate: '',
    description: '',
    location: '',
    dateStr: '',
    timeStr: '',
    image_url: "/event-schedule-banner.png",
    price: '',
    instructor: '',
    registration: ''
  });

  // Auto-load events when editor opens
  useEffect(() => {
    if (isOpen) {
      loadEvents();
    }
  }, [isOpen]);

  // Load events from backend
  const loadEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events');
      if (response.ok) {
        const data = await response.json();
        const backendEvents = data.events || [];
        const eventsWithImages = backendEvents.map((event: any) => ({
          ...event,
          image_url: event.image_url || '/event-schedule-banner.png'
        }));
        setEvents(eventsWithImages);
        setMessage(`✅ Loaded ${backendEvents.length} events from backend!`);
        setMessageType('success');
      } else {
        throw new Error('Failed to load events');
      }
    } catch (error) {
      console.error('Error loading events:', error);
      setMessage('❌ Failed to load events');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  // Test events function
  const loadTestEvents = () => {
    const testEvents = [
      {
        id: 'test1',
        title: 'Test Event 1',
        startDate: '2025-01-01T10:00:00Z',
        endDate: '2025-01-01T11:00:00Z',
        description: 'This is a test event',
        location: 'Test Location',
        dateStr: 'January 1, 2025',
        timeStr: '10:00 AM',
        image_url: '/event-schedule-banner.png'
      },
      {
        id: 'test2',
        title: 'Test Event 2',
        startDate: '2025-01-02T14:00:00Z',
        endDate: '2025-01-02T15:00:00Z',
        description: 'This is another test event',
        location: 'Test Location 2',
        dateStr: 'January 2, 2025',
        timeStr: '2:00 PM',
        image_url: '/event-schedule-banner.png'
      }
    ];
    setEvents(testEvents);
    setMessage(`✅ Loaded ${testEvents.length} test events for debugging`);
    setMessageType('success');
  };

  // Edit event function
  const editEvent = (index: number) => {
    const event = events[index];
    setNewEvent({
      id: event.id || '',
      title: event.title,
      startDate: event.startDate,
      endDate: event.endDate,
      description: event.description || '',
      location: event.location || '',
      dateStr: event.dateStr || '',
      timeStr: event.timeStr || '',
      image_url: event.image_url || '/event-schedule-banner.png',
      price: event.price || '',
      instructor: event.instructor || '',
      registration: event.registration || ''
    });
    setEditingIndex(index);
    setMessage(`Editing event: ${event.title}`);
    setMessageType('success');
  };

  // Delete event function
  const deleteEvent = (index: number) => {
    if (window.confirm(`Are you sure you want to delete "${events[index].title}"?`)) {
      const updatedEvents = events.filter((_, i) => i !== index);
      setEvents(updatedEvents);
      setMessage(`✅ Deleted event: ${events[index].title}`);
      setMessageType('success');
    }
  };

  // Save event function
  const saveEvent = () => {
    if (!newEvent.title.trim()) {
      setMessage('❌ Please enter a title');
      setMessageType('error');
      return;
    }

    const updatedEvents = [...events];
    if (editingIndex !== null) {
      // Update existing event
      updatedEvents[editingIndex] = { ...newEvent };
      setMessage(`✅ Updated event: ${newEvent.title}`);
    } else {
      // Add new event
      updatedEvents.push({ ...newEvent });
      setMessage(`✅ Added new event: ${newEvent.title}`);
    }
    
    setEvents(updatedEvents);
    setMessageType('success');
    resetForm();
  };

  // Reset form function
  const resetForm = () => {
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: '/event-schedule-banner.png',
      price: '',
      instructor: '',
      registration: ''
    });
    setEditingIndex(null);
  };

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
        padding: '20px',
        borderRadius: '10px',
        maxWidth: '95%',
        maxHeight: '95%',
        overflow: 'auto',
        width: '90%'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          paddingBottom: '10px',
          borderBottom: '2px solid #eee'
        }}>
          <h2 style={{ margin: 0, color: '#333' }}>Event Editor (Fixed Version)</h2>
          <button 
            onClick={onClose}
            style={{
              background: 'red',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            × Close
          </button>
        </div>

        {/* Message */}
        {message && (
          <div style={{
            padding: '10px',
            marginBottom: '20px',
            borderRadius: '5px',
            backgroundColor: messageType === 'success' ? '#d4edda' : '#f8d7da',
            color: messageType === 'success' ? '#155724' : '#721c24',
            border: `1px solid ${messageType === 'success' ? '#c3e6cb' : '#f5c6cb'}`
          }}>
            {message}
          </div>
        )}

        {/* Controls */}
        <div style={{ marginBottom: '20px' }}>
          <button 
            onClick={loadEvents} 
            disabled={loading}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginRight: '10px',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? 'Loading...' : '📥 Load Backend Events'}
          </button>
          
          <button 
            onClick={loadTestEvents}
            style={{
              background: '#28a745',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            🧪 Test Events
          </button>
          
          <button 
            onClick={() => {
              console.log('Current events state:', events);
              setMessage(`Debug: Events state has ${events.length} events. Check console for details.`);
              setMessageType('success');
            }}
            style={{
              background: '#6c757d',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            🐛 Debug Events
          </button>
          
          <button 
            onClick={resetForm}
            style={{
              background: '#ffc107',
              color: '#212529',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            ➕ Add New Event
          </button>
        </div>

        {/* Add/Edit Event Form */}
        <div style={{
          border: '2px solid #28a745',
          background: '#f8f9fa',
          padding: '20px',
          borderRadius: '5px',
          marginBottom: '20px'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#28a745' }}>
            {editingIndex !== null ? '✏️ Edit Event' : '➕ Add New Event'}
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Event ID</label>
              <input
                type="text"
                value={newEvent.id || ''}
                onChange={(e) => setNewEvent({ ...newEvent, id: e.target.value })}
                placeholder="Event ID (optional)"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Title *</label>
              <input
                type="text"
                value={newEvent.title}
                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                placeholder="Event title"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Date String</label>
              <input
                type="text"
                value={newEvent.dateStr || ''}
                onChange={(e) => setNewEvent({ ...newEvent, dateStr: e.target.value })}
                placeholder="e.g., January 15, 2025"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Time String</label>
              <input
                type="text"
                value={newEvent.timeStr || ''}
                onChange={(e) => setNewEvent({ ...newEvent, timeStr: e.target.value })}
                placeholder="e.g., 10:00 AM"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Location</label>
            <input
              type="text"
              value={newEvent.location || ''}
              onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
              placeholder="Event location"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Description</label>
            <textarea
              value={newEvent.description || ''}
              onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
              placeholder="Event description"
              rows={3}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                resize: 'vertical'
              }}
            />
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Price</label>
              <input
                type="text"
                value={newEvent.price || ''}
                onChange={(e) => setNewEvent({ ...newEvent, price: e.target.value })}
                placeholder="e.g., $15, Free, $25"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Instructor</label>
              <input
                type="text"
                value={newEvent.instructor || ''}
                onChange={(e) => setNewEvent({ ...newEvent, instructor: e.target.value })}
                placeholder="Instructor name"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Registration Info</label>
            <input
              type="text"
              value={newEvent.registration || ''}
              onChange={(e) => setNewEvent({ ...newEvent, registration: e.target.value })}
              placeholder="e.g., Call 613-548-7810, Online registration required"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
          
          <div style={{ textAlign: 'right' }}>
            <button 
              onClick={resetForm}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: 'pointer',
                marginRight: '10px'
              }}
            >
              Cancel
            </button>
            <button 
              onClick={saveEvent}
              style={{
                background: '#28a745',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              {editingIndex !== null ? '💾 Update Event' : '➕ Add Event'}
            </button>
          </div>
        </div>

        {/* Events List */}
        <div style={{
          border: '3px solid red',
          background: 'white',
          minHeight: '200px',
          padding: '20px'
        }}>
          <h3 style={{ color: 'red', fontSize: '20px', marginTop: 0 }}>
            🔴 CURRENT EVENTS ({events.length}) 🔴
          </h3>
          
          {events.length === 0 ? (
            <div style={{
              background: '#ffcdd2',
              border: '2px solid #f44336',
              padding: '15px',
              textAlign: 'center'
            }}>
              <h4 style={{ color: '#d32f2f', margin: '0 0 10px 0' }}>❌ NO EVENTS FOUND</h4>
              <p>No events found. Click "Load Backend Events" or "Test Events" to load events.</p>
            </div>
          ) : (
            <div>
              <div style={{
                background: '#d4edda',
                border: '1px solid #c3e6cb',
                borderRadius: '5px',
                padding: '10px',
                marginBottom: '15px',
                color: '#155724'
              }}>
                <strong>✅ {events.length} events loaded successfully!</strong><br/>
                You can see them listed below.
              </div>
              
              {events.map((event, index) => (
                <div key={event.id || index} style={{
                  border: '2px solid #007bff',
                  marginBottom: '10px',
                  padding: '15px',
                  borderRadius: '5px',
                  background: '#f0f8ff'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <h4 style={{ margin: '0', color: '#007bff', flex: 1 }}>
                      Event {index + 1}: {event.title}
                    </h4>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button 
                        onClick={() => editEvent(index)}
                        style={{
                          background: '#17a2b8',
                          color: 'white',
                          border: 'none',
                          padding: '5px 10px',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        onClick={() => deleteEvent(index)}
                        style={{
                          background: '#dc3545',
                          color: 'white',
                          border: 'none',
                          padding: '5px 10px',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                  <p><strong>ID:</strong> {event.id || 'No ID'}</p>
                  <p><strong>Date:</strong> {event.dateStr || 'No date'}</p>
                  <p><strong>Time:</strong> {event.timeStr || 'No time'}</p>
                  <p><strong>Location:</strong> {event.location || 'No location'}</p>
                  <p><strong>Description:</strong> {event.description || 'No description'}</p>
                  <p><strong>Price:</strong> {event.price || 'No price'}</p>
                  <p><strong>Instructor:</strong> {event.instructor || 'No instructor'}</p>
                  <p><strong>Registration:</strong> {event.registration || 'No registration info'}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventEditorFixed;
