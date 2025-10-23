import React from 'react';
import './EventViewModal.css';

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
  price?: string;
  instructor?: string;
  registration?: string;
}

interface EventViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  event: Event | null;
}

const EventViewModal: React.FC<EventViewModalProps> = ({
  isOpen,
  onClose,
  event
}) => {
  if (!isOpen || !event) {
    return null;
  }

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };


  return (
    <div className="event-view-modal-overlay" onClick={onClose}>
      <div className="event-view-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="event-view-modal-header">
          <h2 className="event-view-modal-title">{event.title}</h2>
          <button 
            className="event-view-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Event Image */}
        {event.image_url && (
          <div className="event-view-modal-image">
            <img 
              src={event.image_url} 
              alt={event.title}
              onError={(e) => {
                // Show a placeholder instead of hiding the image
                e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkV2ZW50IEltYWdlPC90ZXh0Pjwvc3ZnPg==';
                e.currentTarget.alt = 'Event Image Placeholder';
              }}
            />
          </div>
        )}

        {/* Event Details */}
        <div className="event-view-modal-body">
          {/* Date and Time */}
          <div className="event-detail-section">
            <div className="event-detail-item">
              <span className="event-detail-label">📅 Date:</span>
              <span className="event-detail-value">{event.dateStr || formatDate(event.startDate)}</span>
            </div>
            <div className="event-detail-item">
              <span className="event-detail-label">🕐 Time:</span>
              <span className="event-detail-value">{event.timeStr || formatTime(event.startDate)}</span>
            </div>
            {event.location && (
              <div className="event-detail-item">
                <span className="event-detail-label">📍 Location:</span>
                <span className="event-detail-value">{event.location}</span>
              </div>
            )}
            {event.price && (
              <div className="event-detail-item">
                <span className="event-detail-label">💰 Price:</span>
                <span className="event-detail-value">{event.price}</span>
              </div>
            )}
            {event.instructor && (
              <div className="event-detail-item">
                <span className="event-detail-label">👨‍🏫 Instructor:</span>
                <span className="event-detail-value">{event.instructor}</span>
              </div>
            )}
            {event.registration && (
              <div className="event-detail-item">
                <span className="event-detail-label">📝 Registration:</span>
                <span className="event-detail-value">{event.registration}</span>
              </div>
            )}
          </div>

          {/* Description */}
          {event.description && (
            <div className="event-detail-section">
              <h3 className="event-detail-section-title">About this event</h3>
              <p className="event-description">{event.description}</p>
              {event.instructor && (
                <p className="event-description"><strong>Instructor:</strong> {event.instructor}</p>
              )}
              {event.registration && (
                <p className="event-description"><strong>Registration:</strong> {event.registration}</p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="event-view-modal-footer">
          <button 
            className="event-view-modal-button event-view-modal-button-primary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default EventViewModal;