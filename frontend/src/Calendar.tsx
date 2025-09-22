import React, { useState, useEffect } from 'react';
import './Calendar.css';
import logo from './logo.png';
import EventModal from './EventModal';

interface Event {
  id?: string;
  title: string;
  startDate: Date;
  endDate: Date;
  description?: string;
  location?: string;
}

const Calendar: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState<'real' | 'sample' | 'none'>('none');
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);

  // Get the first day of the current month
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
  const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
  
  // Get the first day of the calendar grid (might be from previous month)
  const firstDayOfCalendar = new Date(firstDayOfMonth);
  firstDayOfCalendar.setDate(firstDayOfCalendar.getDate() - firstDayOfMonth.getDay());
  
  // Get the last day of the calendar grid (might be from next month)
  const lastDayOfCalendar = new Date(lastDayOfMonth);
  lastDayOfCalendar.setDate(lastDayOfCalendar.getDate() + (6 - lastDayOfMonth.getDay()));

  // Generate calendar days
  const calendarDays = [];
  const currentDay = new Date(firstDayOfCalendar);
  
  while (currentDay <= lastDayOfCalendar) {
    calendarDays.push(new Date(currentDay));
    currentDay.setDate(currentDay.getDate() + 1);
  }

  // Get events for a specific date
  const getEventsForDate = (date: Date): Event[] => {
    return events.filter(event => {
      const eventDate = new Date(event.startDate);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  // Navigate months
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };


  // Parse iCal date format (YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS or YYYYMMDD)
  const parseICalDate = (dateStr: string): Date => {
    try {
      // Remove timezone info if present
      const cleanDateStr = dateStr.replace(/Z$/, '').replace(/[+-]\d{4}$/, '');
      
      // Handle different formats
      if (cleanDateStr.length === 8) {
        // Format: YYYYMMDD (date only)
        const year = parseInt(cleanDateStr.substring(0, 4));
        const month = parseInt(cleanDateStr.substring(4, 6)) - 1; // Month is 0-indexed
        const day = parseInt(cleanDateStr.substring(6, 8));
        return new Date(year, month, day);
      } else if (cleanDateStr.length >= 15 && cleanDateStr.includes('T')) {
        // Format: YYYYMMDDTHHMMSS
        const year = parseInt(cleanDateStr.substring(0, 4));
        const month = parseInt(cleanDateStr.substring(4, 6)) - 1; // Month is 0-indexed
        const day = parseInt(cleanDateStr.substring(6, 8));
        const hour = parseInt(cleanDateStr.substring(9, 11)) || 0;
        const minute = parseInt(cleanDateStr.substring(11, 13)) || 0;
        const second = parseInt(cleanDateStr.substring(13, 15)) || 0;
        
        return new Date(year, month, day, hour, minute, second);
      } else {
        // Fallback: try to parse as regular date string
        return new Date(cleanDateStr);
      }
    } catch (error) {
      console.warn('Error parsing iCal date:', dateStr, error);
      return new Date(); // Fallback to current date
    }
  };

  // Fetch events from Seniors Kingston iCal feed
  const getApiUrl = () => {
    return process.env.NODE_ENV === 'production' 
      ? 'https://class-cancellation-backend.onrender.com/api'
      : 'http://localhost:8000/api';
  };

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${getApiUrl()}/events`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Backend response:', data);
        
        if (data.events && data.events.length > 0) {
          // Convert backend events to frontend format
          const convertedEvents: Event[] = data.events.map((event: any) => ({
            id: event.id,
            title: event.title,
            startDate: new Date(event.startDate),
            endDate: new Date(event.endDate),
            description: event.description || '',
            location: event.location || ''
          }));
          
          console.log('Converted events:', convertedEvents);
          setEvents(convertedEvents);
          setDataSource('real');
          return;
        }
      }
      
      console.log('Backend fetch failed or no events');
      setDataSource('none');
      
    } catch (error) {
      console.error('Error fetching events:', error);
      setDataSource('none');
    } finally {
      setLoading(false);
    }
  };

  const saveEvent = async (event: Event) => {
    try {
      const eventData = {
        title: event.title,
        description: event.description || '',
        location: event.location || '',
        startDate: event.startDate.toISOString(),
        endDate: event.endDate.toISOString()
      };

      let response;
      if (event.id) {
        // Update existing event
        response = await fetch(`${getApiUrl()}/events/${event.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(eventData)
        });
      } else {
        // Create new event
        response = await fetch(`${getApiUrl()}/events`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(eventData)
        });
      }

      if (response.ok) {
        console.log('Event saved successfully');
        fetchEvents(); // Refresh events list
        setIsModalOpen(false);
        setSelectedEvent(null);
        setSelectedDate(undefined);
      } else {
        console.error('Failed to save event');
      }
    } catch (error) {
      console.error('Error saving event:', error);
    }
  };

  const deleteEvent = async (eventId: string) => {
    try {
      const response = await fetch(`${getApiUrl()}/events/${eventId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        console.log('Event deleted successfully');
        fetchEvents(); // Refresh events list
        setIsModalOpen(false);
        setSelectedEvent(null);
      } else {
        console.error('Failed to delete event');
      }
    } catch (error) {
      console.error('Error deleting event:', error);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDayClick = (day: number) => {
    const clickedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    setSelectedDate(clickedDate);
    setSelectedEvent(null);
    setIsModalOpen(true);
  };

  const handleEventClick = (event: Event) => {
    setSelectedEvent(event);
    setSelectedDate(undefined);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedEvent(null);
    setSelectedDate(undefined);
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="calendar-container">
      <header className="app-header">
        <div className="header-left">
          <img 
            src={logo} 
            alt="Company Logo" 
            className="app-logo clickable-logo"
            onClick={() => window.open('https://www.seniorskingston.ca/', '_blank')}
            title="Visit Seniors Kingston Website"
          />
          <img 
            src={logo} 
            alt="Event Schedule" 
            className="calendar-icon"
            title="Event Schedule"
          />
          <button 
            onClick={() => window.history.back()} 
            className="back-to-home-button"
            title="Back to Home"
          >
            🏠
          </button>
        </div>
        <h1>Event Schedule Update</h1>
        <div className="datetime-display">
          {new Date().toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })} {new Date().toLocaleTimeString('en-CA', { timeZone: 'America/Toronto' })}
        </div>
      </header>
      
      <div className="calendar-header">
        <div className="calendar-controls">
          <button onClick={goToPreviousMonth} className="nav-button">‹</button>
          <button onClick={goToToday} className="today-button">Today</button>
          <button onClick={goToNextMonth} className="nav-button">›</button>
          <button onClick={fetchEvents} className="refresh-button" disabled={loading}>
            {loading ? '⟳' : '🔄'} Refresh Events
          </button>
        </div>
        <h2 className="month-year">
          {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
        </h2>
        <div className="data-source-indicator">
          {dataSource === 'real' ? (
            <span className="real-data">✅ Live events from Seniors Kingston</span>
          ) : dataSource === 'sample' ? (
            <span className="sample-data">📅 Seniors Kingston events (based on real events from their website)</span>
          ) : (
            <span className="no-data">❌ No events loaded</span>
          )}
        </div>
      </div>

      {loading && (
        <div className="loading-message">
          Loading events...
        </div>
      )}

      <div className="calendar-grid">
        {/* Day headers */}
        <div className="calendar-weekdays">
          {dayNames.map(day => (
            <div key={day} className="weekday-header">{day}</div>
          ))}
        </div>

        {/* Calendar days */}
        <div className="calendar-days">
          {calendarDays.map((day, index) => {
            const isCurrentMonth = day.getMonth() === currentDate.getMonth();
            const isToday = day.toDateString() === new Date().toDateString();
            const dayEvents = getEventsForDate(day);

            return (
              <div
                key={index}
                className={`calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                onClick={() => handleDayClick(day.getDate())}
              >
                <div className="day-number">{day.getDate()}</div>
                <div className="day-events">
                  {dayEvents.map((event, eventIndex) => (
                    <div 
                      key={eventIndex} 
                      className="event-item" 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEventClick(event);
                      }}
                      title={`${event.title}${event.location ? ` - ${event.location}` : ''}${event.description ? `\n${event.description}` : ''}`}
                    >
                      <div className="event-time">
                        {event.startDate.toLocaleTimeString('en-US', { 
                          hour: 'numeric', 
                          minute: '2-digit',
                          hour12: true 
                        })}
                      </div>
                      <div className="event-title">{event.title}</div>
                      {event.location && (
                        <div className="event-location">📍 {event.location}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <EventModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSave={saveEvent}
        onDelete={selectedEvent?.id ? deleteEvent : undefined}
        event={selectedEvent}
        selectedDate={selectedDate}
      />
    </div>
  );
};

export default Calendar;
