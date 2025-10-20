import React, { useState, useEffect } from 'react';
import './EventModal.css';

interface Event {
  id?: string;
  title: string;
  startDate: Date;
  endDate: Date;
  description?: string;
  location?: string;
  dateStr?: string;
  timeStr?: string;
  image_url?: string;
}

interface EventModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (event: Event) => void;
  onDelete?: (eventId: string) => void;
  event?: Event | null;
  selectedDate?: Date;
  isReadOnly?: boolean; // New prop for read-only mode (for events)
}

const EventModal: React.FC<EventModalProps> = ({
  isOpen,
  onClose,
  onSave,
  onDelete,
  event,
  selectedDate,
  isReadOnly = false
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    location: '',
    startDate: '',
    startTime: '',
    endDate: '',
    endTime: ''
  });

  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (isOpen) {
      if (event) {
        // Editing existing event
        setFormData({
          title: event.title,
          description: event.description || '',
          location: event.location || '',
          startDate: event.startDate.toISOString().split('T')[0],
          startTime: event.startDate.toTimeString().slice(0, 5),
          endDate: event.endDate.toISOString().split('T')[0],
          endTime: event.endDate.toTimeString().slice(0, 5)
        });
      } else if (selectedDate) {
        // Creating new event
        const dateStr = selectedDate.toISOString().split('T')[0];
        setFormData({
          title: '',
          description: '',
          location: '',
          startDate: dateStr,
          startTime: '09:00',
          endDate: dateStr,
          endTime: '10:00'
        });
      }
      setErrors([]);
    }
  }, [isOpen, event, selectedDate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const newErrors: string[] = [];
    
    if (!formData.title.trim()) {
      newErrors.push('Title is required');
    }
    if (!formData.startDate) {
      newErrors.push('Start date is required');
    }
    if (!formData.endDate) {
      newErrors.push('End date is required');
    }
    if (!formData.startTime) {
      newErrors.push('Start time is required');
    }
    if (!formData.endTime) {
      newErrors.push('End time is required');
    }

    if (newErrors.length > 0) {
      setErrors(newErrors);
      return;
    }

    const startDateTime = new Date(`${formData.startDate}T${formData.startTime}:00`);
    const endDateTime = new Date(`${formData.endDate}T${formData.endTime}:00`);

    if (endDateTime <= startDateTime) {
      setErrors(['End time must be after start time']);
      return;
    }

    const eventData: Event = {
      id: event?.id,
      title: formData.title.trim(),
      description: formData.description.trim(),
      location: formData.location.trim(),
      startDate: startDateTime,
      endDate: endDateTime
    };

    onSave(eventData);
  };

  const handleDelete = () => {
    if (event?.id && onDelete) {
      onDelete(event.id);
    }
  };

  if (!isOpen) return null;

  // Read-only mode for events (showing banner and description)
  if (isReadOnly && event) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content event-view-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>{event.title}</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>

          <div className="event-view-content">
            {/* Event Banner Image */}
            {event.image_url && event.image_url !== '/assets/event-schedule-banner.png' && (
              <div className="event-banner-container">
                <img 
                  src={event.image_url} 
                  alt={event.title} 
                  className="event-banner-image-large"
                />
              </div>
            )}

            {/* Event Details */}
            <div className="event-details">
              <div className="event-detail-row">
                <span className="event-detail-label">📅 Date:</span>
                <span className="event-detail-value">{event.dateStr || 'TBA'}</span>
              </div>
              
              <div className="event-detail-row">
                <span className="event-detail-label">🕐 Time:</span>
                <span className="event-detail-value">{event.timeStr || 'TBA'}</span>
              </div>
              
              {event.location && (
                <div className="event-detail-row">
                  <span className="event-detail-label">📍 Location:</span>
                  <span className="event-detail-value">{event.location}</span>
                </div>
              )}
            </div>

            {/* Event Description */}
            {event.description && (
              <div className="event-description-container">
                <h3>Description</h3>
                <div className="event-description-text">
                  {event.description}
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button type="button" onClick={onClose} className="close-button">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Edit mode for programs
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{event ? 'Edit Event' : 'Add New Event'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Event Title *</label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              placeholder="Enter event title"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="startDate">Start Date *</label>
              <input
                type="date"
                id="startDate"
                value={formData.startDate}
                onChange={(e) => setFormData({...formData, startDate: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="startTime">Start Time *</label>
              <input
                type="time"
                id="startTime"
                value={formData.startTime}
                onChange={(e) => setFormData({...formData, startTime: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="endDate">End Date *</label>
              <input
                type="date"
                id="endDate"
                value={formData.endDate}
                onChange={(e) => setFormData({...formData, endDate: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="endTime">End Time *</label>
              <input
                type="time"
                id="endTime"
                value={formData.endTime}
                onChange={(e) => setFormData({...formData, endTime: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="location">Location</label>
            <input
              type="text"
              id="location"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              placeholder="Enter location"
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Enter event description"
              rows={3}
            />
          </div>

          {errors.length > 0 && (
            <div className="error-messages">
              {errors.map((error, index) => (
                <div key={index} className="error-message">{error}</div>
              ))}
            </div>
          )}

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancel
            </button>
            {event && onDelete && (
              <button type="button" onClick={handleDelete} className="delete-button">
                Delete
              </button>
            )}
            <button type="submit" className="save-button">
              {event ? 'Update Event' : 'Add Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EventModal;
