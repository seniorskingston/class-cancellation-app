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
}

interface EventEditorProps {
  isOpen: boolean;
  onClose: () => void;
}

const EventEditor: React.FC<EventEditorProps> = ({ isOpen, onClose }) => {
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
    image_url: '/assets/event-schedule-banner.png'
  });

  // Load events from backend
  const loadEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events');
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
        setMessage('Events loaded successfully');
        setMessageType('success');
      } else {
        throw new Error('Failed to load events');
      }
    } catch (error) {
      console.error('Error loading events:', error);
      setMessage('Failed to load events');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  // Save events to backend
  const saveEvents = async () => {
    setSaving(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ events }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setMessage(`Successfully saved ${events.length} events`);
          setMessageType('success');
        } else {
          throw new Error(result.error || 'Save failed');
        }
      } else {
        throw new Error('Save failed');
      }
    } catch (error) {
      console.error('Error saving events:', error);
      setMessage('Failed to save events');
      setMessageType('error');
    } finally {
      setSaving(false);
    }
  };

  // Add new event
  const addEvent = () => {
    if (!newEvent.title || !newEvent.startDate || !newEvent.endDate) {
      setMessage('Please fill in required fields (title, start date, end date)');
      setMessageType('error');
      return;
    }

    const event: Event = {
      ...newEvent,
      id: `event_${Date.now()}`,
    };

    setEvents([...events, event]);
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: '/assets/event-schedule-banner.png'
    });
    setMessage('Event added successfully');
    setMessageType('success');
  };

  // Edit event
  const editEvent = (index: number) => {
    setEditingIndex(index);
    setNewEvent(events[index]);
  };

  // Update event
  const updateEvent = () => {
    if (editingIndex === null || !newEvent.title || !newEvent.startDate || !newEvent.endDate) {
      setMessage('Please fill in required fields');
      setMessageType('error');
      return;
    }

    const updatedEvents = [...events];
    updatedEvents[editingIndex] = { ...newEvent };
    setEvents(updatedEvents);
    setEditingIndex(null);
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: '/assets/event-schedule-banner.png'
    });
    setMessage('Event updated successfully');
    setMessageType('success');
  };

  // Delete event
  const deleteEvent = (index: number) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      const updatedEvents = events.filter((_, i) => i !== index);
      setEvents(updatedEvents);
      setMessage('Event deleted successfully');
      setMessageType('success');
    }
  };

  // Cancel edit
  const cancelEdit = () => {
    setEditingIndex(null);
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: '/assets/event-schedule-banner.png'
    });
  };

  // Load events when modal opens
  useEffect(() => {
    if (isOpen) {
      loadEvents();
    }
  }, [isOpen]);

  // Clear message after 3 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage('');
        setMessageType('');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  if (!isOpen) return null;

  return (
    <div className="event-editor-overlay" onClick={onClose}>
      <div className="event-editor-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="event-editor-header">
          <h2>Event Editor</h2>
          <button className="event-editor-close" onClick={onClose}>×</button>
        </div>

        {/* Message */}
        {message && (
          <div className={`event-editor-message ${messageType}`}>
            {message}
          </div>
        )}

        {/* Controls */}
        <div className="event-editor-controls">
          <button 
            onClick={loadEvents} 
            disabled={loading}
            className="event-editor-button event-editor-button-secondary"
          >
            {loading ? 'Loading...' : 'Load Events'}
          </button>
          <button 
            onClick={saveEvents} 
            disabled={saving || events.length === 0}
            className="event-editor-button event-editor-button-primary"
          >
            {saving ? 'Saving...' : `Save ${events.length} Events`}
          </button>
        </div>

        {/* Add/Edit Event Form */}
        <div className="event-editor-form">
          <h3>{editingIndex !== null ? 'Edit Event' : 'Add New Event'}</h3>
          
          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Title *</label>
              <input
                type="text"
                value={newEvent.title}
                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                placeholder="Event title"
              />
            </div>
            <div className="event-editor-form-group">
              <label>Location</label>
              <input
                type="text"
                value={newEvent.location || ''}
                onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                placeholder="Event location"
              />
            </div>
          </div>

          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Start Date *</label>
              <input
                type="datetime-local"
                value={newEvent.startDate}
                onChange={(e) => setNewEvent({ ...newEvent, startDate: e.target.value })}
              />
            </div>
            <div className="event-editor-form-group">
              <label>End Date *</label>
              <input
                type="datetime-local"
                value={newEvent.endDate}
                onChange={(e) => setNewEvent({ ...newEvent, endDate: e.target.value })}
              />
            </div>
          </div>

          <div className="event-editor-form-group">
            <label>Description</label>
            <textarea
              value={newEvent.description || ''}
              onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
              placeholder="Event description"
              rows={3}
            />
          </div>

          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Date String</label>
              <input
                type="text"
                value={newEvent.dateStr || ''}
                onChange={(e) => setNewEvent({ ...newEvent, dateStr: e.target.value })}
                placeholder="e.g., November 15"
              />
            </div>
            <div className="event-editor-form-group">
              <label>Time String</label>
              <input
                type="text"
                value={newEvent.timeStr || ''}
                onChange={(e) => setNewEvent({ ...newEvent, timeStr: e.target.value })}
                placeholder="e.g., 2:00 PM"
              />
            </div>
          </div>

          <div className="event-editor-form-actions">
            {editingIndex !== null ? (
              <>
                <button onClick={updateEvent} className="event-editor-button event-editor-button-primary">
                  Update Event
                </button>
                <button onClick={cancelEdit} className="event-editor-button event-editor-button-secondary">
                  Cancel
                </button>
              </>
            ) : (
              <button onClick={addEvent} className="event-editor-button event-editor-button-primary">
                Add Event
              </button>
            )}
          </div>
        </div>

        {/* Events List */}
        <div className="event-editor-list">
          <h3>Current Events ({events.length})</h3>
          {events.length === 0 ? (
            <p className="event-editor-empty">No events found. Add some events above.</p>
          ) : (
            <div className="event-editor-events">
              {events.map((event, index) => (
                <div key={event.id || index} className="event-editor-event">
                  <div className="event-editor-event-info">
                    <h4>{event.title}</h4>
                    <p><strong>Date:</strong> {new Date(event.startDate).toLocaleDateString()}</p>
                    <p><strong>Time:</strong> {new Date(event.startDate).toLocaleTimeString()}</p>
                    {event.location && <p><strong>Location:</strong> {event.location}</p>}
                    {event.description && <p><strong>Description:</strong> {event.description.substring(0, 100)}...</p>}
                  </div>
                  <div className="event-editor-event-actions">
                    <button 
                      onClick={() => editEvent(index)}
                      className="event-editor-button event-editor-button-small event-editor-button-secondary"
                    >
                      Edit
                    </button>
                    <button 
                      onClick={() => deleteEvent(index)}
                      className="event-editor-button event-editor-button-small event-editor-button-danger"
                    >
                      Delete
                    </button>
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

export default EventEditor;
