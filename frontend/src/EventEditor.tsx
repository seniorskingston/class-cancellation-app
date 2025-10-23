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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
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

  // Check if user is authenticated (simple password check)
  const checkAuthentication = () => {
    const correctPassword = 'rebecca2025'; // Change this to your preferred password
    return password === correctPassword;
  };

  const handleLogin = () => {
    if (checkAuthentication()) {
      setIsAuthenticated(true);
      setMessage('Access granted! You can now edit events.');
      setMessageType('success');
    } else {
      setMessage('Incorrect password. Only authorized users can edit events.');
      setMessageType('error');
    }
  };

  // Load events from backend
  const loadEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events');
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
        setMessage(`Loaded ${data.events?.length || 0} events from backend`);
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

  // Load scraped events from local file
  const loadScrapedEvents = async () => {
    setLoading(true);
    try {
      // Try to load from the scraped events file
      const response = await fetch('/editable_events.json');
      if (response.ok) {
        const data = await response.json();
        const scrapedEvents = data.events || [];
        setEvents(scrapedEvents);
        setMessage(`Loaded ${scrapedEvents.length} scraped events with complete details!`);
        setMessageType('success');
      } else {
        // Fallback: create sample events with November data
        const sampleEvents = [
          {
            title: "Daylight Savings Ends",
            startDate: "2025-11-02T08:00:00Z",
            endDate: "2025-11-02T09:00:00Z",
            description: "Daylight saving time ends. Clocks fall back one hour.",
            location: "Everywhere",
            dateStr: "November 2",
            timeStr: "8:00 AM",
            image_url: "/assets/event-schedule-banner.png"
          },
          {
            title: "Online Registration Begins",
            startDate: "2025-11-03T08:00:00Z",
            endDate: "2025-11-03T09:00:00Z",
            description: "Online Program Registration Starts Today",
            location: "Online",
            dateStr: "November 3",
            timeStr: "8:00 AM",
            image_url: "/assets/event-schedule-banner.png"
          },
          {
            title: "Assistive Listening Solutions",
            startDate: "2025-11-03T12:00:00Z",
            endDate: "2025-11-03T13:00:00Z",
            description: "Removing communication barriers leads to engagement within the community. Learn about how assistive listening solutions can help hard-of-hearing members remove background noise and hear what they are intended to.",
            location: "Seniors Kingston Centre",
            dateStr: "November 3",
            timeStr: "12:00 PM",
            image_url: "/assets/event-schedule-banner.png"
          },
          {
            title: "Fresh Food Market",
            startDate: "2025-11-04T10:00:00Z",
            endDate: "2025-11-04T11:00:00Z",
            description: "Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
            location: "Seniors Kingston Centre",
            dateStr: "November 4",
            timeStr: "10:00 AM",
            image_url: "/assets/event-schedule-banner.png"
          },
          {
            title: "Fraud Awareness",
            startDate: "2025-11-05T13:00:00Z",
            endDate: "2025-11-05T14:00:00Z",
            description: "Protect your money and identity from phone, internet, and in-person fraudsters. Learn how to spot and avoid scams.",
            location: "Seniors Kingston Centre",
            dateStr: "November 5",
            timeStr: "1:00 PM",
            image_url: "/assets/event-schedule-banner.png"
          }
        ];
        setEvents(sampleEvents);
        setMessage(`Loaded ${sampleEvents.length} sample November events. Upload the scraped events file to see all 151 events.`);
        setMessageType('success');
      }
    } catch (error) {
      console.error('Error loading scraped events:', error);
      setMessage('Failed to load scraped events');
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

        {/* Authentication */}
        {!isAuthenticated ? (
          <div className="event-editor-auth">
            <h3>🔒 Admin Access Required</h3>
            <p>Enter password to edit events:</p>
            <div className="auth-form">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
              />
              <button onClick={handleLogin}>Login</button>
            </div>
            <p className="auth-note">Only authorized users can edit events</p>
          </div>
        ) : (
          <>
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
            {loading ? 'Loading...' : 'Load Backend Events'}
          </button>
          <button 
            onClick={loadScrapedEvents} 
            disabled={loading}
            className="event-editor-button event-editor-button-success"
          >
            {loading ? 'Loading...' : '📥 Load Scraped Events (151)'}
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
          </>
        )}
      </div>
    </div>
  );
};

export default EventEditor;
