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
  const [saving, setSaving] = useState(false);
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

  // Save all events to backend
  const saveAllEvents = async () => {
    setSaving(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events/bulk-update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ events }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setMessage(`✅ Successfully saved ${events.length} events to backend!`);
          setMessageType('success');
        } else {
          throw new Error(result.error || 'Save failed');
        }
      } else {
        const errorText = await response.text();
        throw new Error(`Save failed: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error saving events:', error);
      setMessage(`❌ Failed to save events: ${error}`);
      setMessageType('error');
    } finally {
      setSaving(false);
    }
  };

  // Save individual event
  const saveEvent = () => {
    if (!newEvent.title.trim()) {
      setMessage('❌ Please enter a title');
      setMessageType('error');
      return;
    }

    if (!newEvent.startDate) {
      setMessage('❌ Please enter a start date');
      setMessageType('error');
      return;
    }

    if (!newEvent.endDate) {
      setMessage('❌ Please enter an end date');
      setMessageType('error');
      return;
    }

    const eventToSave: Event = {
      ...newEvent,
      id: newEvent.id || `event_${Date.now()}`,
    };

    if (editingIndex !== null) {
      // Update existing event
      const updatedEvents = [...events];
      updatedEvents[editingIndex] = eventToSave;
      setEvents(updatedEvents);
      setMessage('✅ Event updated successfully!');
    } else {
      // Add new event
      setEvents([...events, eventToSave]);
      setMessage('✅ Event added successfully!');
    }

    setMessageType('success');
    setEditingIndex(null);
    setNewEvent({
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
  };

  // Edit event
  const editEvent = (index: number) => {
    setEditingIndex(index);
    setNewEvent(events[index]);
  };

  // Delete event
  const deleteEvent = (index: number) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      const updatedEvents = events.filter((_, i) => i !== index);
      setEvents(updatedEvents);
      setMessage('✅ Event deleted successfully!');
      setMessageType('success');
    }
  };

  // Clear message
  const clearMessage = () => {
    setMessage('');
    setMessageType('');
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 10000,
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '30px',
        maxWidth: '800px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 20px 40px rgba(0,0,0,0.3)'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          borderBottom: '2px solid #f0f0f0',
          paddingBottom: '15px'
        }}>
          <h2 style={{ margin: 0, color: '#333' }}>📅 Event Editor</h2>
          <button
            onClick={onClose}
            style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              padding: '8px 15px',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            ✕ Close
          </button>
        </div>

        {/* Message */}
        {message && (
          <div style={{
            padding: '10px',
            marginBottom: '20px',
            borderRadius: '5px',
            background: messageType === 'success' ? '#d4edda' : '#f8d7da',
            color: messageType === 'success' ? '#155724' : '#721c24',
            border: `1px solid ${messageType === 'success' ? '#c3e6cb' : '#f5c6cb'}`
          }}>
            {message}
            <button
              onClick={clearMessage}
              style={{
                float: 'right',
                background: 'none',
                border: 'none',
                color: 'inherit',
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '20px',
          flexWrap: 'wrap'
        }}>
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
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? '⏳ Loading...' : '🔄 Load Events'}
          </button>
          
          <button
            onClick={saveAllEvents}
            disabled={saving || events.length === 0}
            style={{
              background: '#28a745',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: (saving || events.length === 0) ? 'not-allowed' : 'pointer',
              opacity: (saving || events.length === 0) ? 0.6 : 1
            }}
          >
            {saving ? '⏳ Saving...' : '💾 Save All Events'}
          </button>
        </div>

        {/* Event Form */}
        <div style={{
          background: '#f8f9fa',
          padding: '20px',
          borderRadius: '10px',
          marginBottom: '20px'
        }}>
          <h3 style={{ marginTop: 0, color: '#333' }}>
            {editingIndex !== null ? '✏️ Edit Event' : '➕ Add New Event'}
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Title *</label>
              <input
                type="text"
                value={newEvent.title}
                onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
                placeholder="Event title"
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Location</label>
              <input
                type="text"
                value={newEvent.location || ''}
                onChange={(e) => setNewEvent({...newEvent, location: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
                placeholder="Event location"
              />
            </div>
          </div>

          {/* SUPER PROMINENT IMAGE EDITOR */}
          <div style={{ 
            border: '5px solid #ff0000', 
            padding: '25px', 
            borderRadius: '15px',
            backgroundColor: '#ffe6e6',
            marginBottom: '30px',
            position: 'relative',
            zIndex: 9999,
            boxShadow: '0 0 20px rgba(255,0,0,0.3)'
          }}>
            <div style={{ 
              position: 'absolute',
              top: '-15px',
              left: '25px',
              backgroundColor: '#ff0000',
              color: 'white',
              padding: '8px 20px',
              borderRadius: '20px',
              fontSize: '1rem',
              fontWeight: 'bold',
              boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
            }}>
              🖼️ IMAGE EDITOR - CHANGE EVENT BANNERS HERE
            </div>
            <label style={{ 
              fontSize: '1.4rem', 
              fontWeight: 'bold', 
              color: '#ff0000', 
              marginBottom: '20px', 
              display: 'block',
              marginTop: '15px',
              textAlign: 'center'
            }}>
              🖼️ EVENT BANNER/IMAGE URL 🖼️
            </label>
            <input
              type="text"
              value={newEvent.image_url || ''}
              onChange={(e) => setNewEvent({ ...newEvent, image_url: e.target.value })}
              placeholder="Enter image URL: /event-schedule-banner.png or https://example.com/image.jpg"
              style={{ 
                width: '100%', 
                padding: '20px', 
                fontSize: '1.2rem',
                border: '4px solid #ff0000',
                borderRadius: '10px',
                marginBottom: '20px',
                backgroundColor: 'white',
                fontWeight: 'bold',
                textAlign: 'center',
                boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
              }}
            />
            <div style={{ 
              fontSize: '1.1rem', 
              color: '#ff0000', 
              marginBottom: '20px',
              fontWeight: 'bold',
              backgroundColor: '#fff0f0',
              padding: '15px',
              borderRadius: '8px',
              border: '2px solid #ff0000',
              textAlign: 'center'
            }}>
              💡 Enter a URL or path to the event banner image (e.g., /event-schedule-banner.png)
            </div>
            {newEvent.image_url && (
              <div style={{ 
                marginTop: '25px',
                border: '4px solid #ff0000',
                borderRadius: '15px',
                padding: '25px',
                backgroundColor: 'white',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
              }}>
                <div style={{ 
                  marginBottom: '20px', 
                  fontWeight: 'bold', 
                  color: '#ff0000',
                  fontSize: '1.3rem'
                }}>
                  📸 IMAGE PREVIEW:
                </div>
                <img 
                  src={newEvent.image_url} 
                  alt="Event banner preview"
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '300px', 
                    borderRadius: '15px',
                    border: '4px solid #ddd',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
                  }}
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    const parent = (e.target as HTMLImageElement).parentElement;
                    if (parent) {
                      const errorMsg = document.createElement('div');
                      errorMsg.textContent = '❌ Image not found or invalid URL';
                      errorMsg.style.color = '#d32f2f';
                      errorMsg.style.fontWeight = 'bold';
                      errorMsg.style.fontSize = '1.2rem';
                      errorMsg.style.padding = '25px';
                      errorMsg.style.border = '3px solid #d32f2f';
                      errorMsg.style.borderRadius = '10px';
                      errorMsg.style.backgroundColor = '#ffebee';
                      parent.appendChild(errorMsg);
                    }
                  }}
                />
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Start Date *</label>
              <input
                type="datetime-local"
                value={newEvent.startDate}
                onChange={(e) => setNewEvent({...newEvent, startDate: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>End Date *</label>
              <input
                type="datetime-local"
                value={newEvent.endDate}
                onChange={(e) => setNewEvent({...newEvent, endDate: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Description</label>
            <textarea
              value={newEvent.description || ''}
              onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                boxSizing: 'border-box',
                minHeight: '80px',
                resize: 'vertical'
              }}
              placeholder="Event description"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Price</label>
              <input
                type="text"
                value={newEvent.price || ''}
                onChange={(e) => setNewEvent({...newEvent, price: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
                placeholder="e.g., $10, Free"
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Instructor</label>
              <input
                type="text"
                value={newEvent.instructor || ''}
                onChange={(e) => setNewEvent({...newEvent, instructor: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
                placeholder="Instructor name"
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Registration</label>
              <input
                type="text"
                value={newEvent.registration || ''}
                onChange={(e) => setNewEvent({...newEvent, registration: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxSizing: 'border-box'
                }}
                placeholder="Registration info"
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
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
            
            {editingIndex !== null && (
              <button
                onClick={() => {
                  setEditingIndex(null);
                  setNewEvent({
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
                }}
                style={{
                  background: '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                ❌ Cancel Edit
              </button>
            )}
          </div>
        </div>

        {/* Events List */}
        <div>
          <h3 style={{ color: '#333' }}>📋 Current Events ({events.length})</h3>
          
          {events.length === 0 ? (
            <p style={{ color: '#666', fontStyle: 'italic' }}>No events loaded. Click "Load Events" to load from backend.</p>
          ) : (
            <div style={{ maxHeight: '300px', overflow: 'auto' }}>
              {events.map((event, index) => (
                <div
                  key={event.id || index}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '15px',
                    marginBottom: '10px',
                    background: editingIndex === index ? '#e3f2fd' : 'white'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: '0 0 5px 0', color: '#333' }}>{event.title}</h4>
                      <p style={{ margin: '0 0 5px 0', color: '#666', fontSize: '14px' }}>
                        📅 {new Date(event.startDate).toLocaleDateString()} at {new Date(event.startDate).toLocaleTimeString()}
                      </p>
                      {event.location && (
                        <p style={{ margin: '0 0 5px 0', color: '#666', fontSize: '14px' }}>
                          📍 {event.location}
                        </p>
                      )}
                      {event.description && (
                        <p style={{ margin: '0 0 5px 0', color: '#666', fontSize: '14px' }}>
                          📝 {event.description.substring(0, 100)}...
                        </p>
                      )}
                    </div>
                    
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <button
                        onClick={() => editEvent(index)}
                        style={{
                          background: '#007bff',
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