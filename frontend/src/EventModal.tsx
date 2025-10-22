import React from 'react';
import './EventViewModal.css';

interface Event {
  id?: string;
  title: string;
  startDate: Date;
  endDate: Date;
  description?: string;
  location?: string;
  banner?: string;
  image_url?: string;
  dateStr?: string;
  timeStr?: string;
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
  if (!isOpen || !event) return null;

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getEventImage = () => {
    // Try different image sources
    if (event.banner) return event.banner;
    if (event.image_url) return event.image_url;
    
    // Default event banner
    return '/assets/event-schedule-banner.png';
  };

  const getEventDescription = () => {
    if (event.description) return event.description;
    return 'No description available for this event.';
  };

  return (
    <div className="event-view-modal-overlay" onClick={onClose}>
      <div className="event-view-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="event-view-modal-header">
          <h2 className="event-view-title">{event.title}</h2>
          <button className="event-view-close-button" onClick={onClose}>×</button>
        </div>

        <div className="event-view-modal-body">
          {/* Event Banner/Image */}
          <div className="event-view-banner">
            <img 
              src={getEventImage()} 
              alt={event.title}
              className="event-banner-image"
              onError={(e) => {
                // Fallback to default banner if image fails to load
                const target = e.target as HTMLImageElement;
                target.src = '/assets/event-schedule-banner.png';
              }}
            />
          </div>

          {/* Event Details */}
          <div className="event-view-details">
            <div className="event-detail-row">
              <div className="event-detail-label">📅 Date:</div>
              <div className="event-detail-value">
                {event.dateStr || formatDate(event.startDate)}
              </div>
            </div>

            <div className="event-detail-row">
              <div className="event-detail-label">🕐 Time:</div>
              <div className="event-detail-value">
                {event.timeStr || `${formatTime(event.startDate)} - ${formatTime(event.endDate)}`}
              </div>
            </div>

            {event.location && (
              <div className="event-detail-row">
                <div className="event-detail-label">📍 Location:</div>
                <div className="event-detail-value">{event.location}</div>
              </div>
            )}

            <div className="event-detail-row">
              <div className="event-detail-label">📝 Description:</div>
              <div className="event-detail-description">
                {getEventDescription()}
              </div>
            </div>
          </div>
        </div>

        <div className="event-view-modal-footer">
          <button className="event-view-close-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default EventViewModal;
