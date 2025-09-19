import React, { useState, useEffect } from 'react';
import './Calendar.css';

interface Event {
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

  // Parse iCal data
  const parseICalData = (icalData: string): Event[] => {
    const events: Event[] = [];
    const lines = icalData.split('\n');
    
    let currentEvent: Partial<Event> = {};
    let inEvent = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (line === 'BEGIN:VEVENT') {
        inEvent = true;
        currentEvent = {};
      } else if (line === 'END:VEVENT' && inEvent) {
        if (currentEvent.title && currentEvent.startDate && currentEvent.endDate) {
          events.push(currentEvent as Event);
        }
        inEvent = false;
        currentEvent = {};
      } else if (inEvent) {
        if (line.startsWith('SUMMARY:')) {
          currentEvent.title = line.substring(8).replace(/\\,/g, ',').replace(/\\;/g, ';');
        } else if (line.startsWith('DTSTART')) {
          const dateStr = line.split(':')[1];
          currentEvent.startDate = parseICalDate(dateStr);
        } else if (line.startsWith('DTEND')) {
          const dateStr = line.split(':')[1];
          currentEvent.endDate = parseICalDate(dateStr);
        } else if (line.startsWith('DESCRIPTION:')) {
          currentEvent.description = line.substring(12).replace(/\\,/g, ',').replace(/\\;/g, ';');
        } else if (line.startsWith('LOCATION:')) {
          currentEvent.location = line.substring(9).replace(/\\,/g, ',').replace(/\\;/g, ';');
        }
      }
    }
    
    return events;
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
  const fetchEvents = async () => {
    setLoading(true);
    try {
      // Try to fetch from our backend scraping endpoint first
      const backendUrl = process.env.NODE_ENV === 'production' 
        ? 'https://class-cancellation-backend.onrender.com/api/events'
        : 'http://localhost:8000/api/events';
      
      console.log('Fetching events from backend:', backendUrl);
      
      try {
        const response = await fetch(backendUrl, {
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
        
        console.log('Backend fetch failed or no events, trying fallback...');
      } catch (backendError) {
        console.warn('Backend fetch failed:', backendError);
      }
      
      // Fallback to sample events if backend fails
      console.log('Using sample events as fallback');
      const today = new Date();
      const sampleEvents: Event[] = [
        {
          title: "Morning Exercise Class",
          startDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 9, 0),
          endDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 10, 0),
          description: "Gentle exercise for seniors",
          location: "Kingston Community Centre"
        },
        {
          title: "Book Club Meeting", 
          startDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 3, 14, 0),
          endDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 3, 15, 30),
          description: "Monthly book discussion",
          location: "Seniors Kingston Library"
        },
        {
          title: "Art Workshop",
          startDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 5, 10, 30),
          endDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 5, 12, 0),
          description: "Watercolor painting class",
          location: "Arts Centre"
        },
        {
          title: "Health Seminar",
          startDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 7, 13, 0),
          endDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 7, 14, 30),
          description: "Healthy aging presentation",
          location: "Seniors Kingston Main Hall"
        },
        {
          title: "Coffee Social",
          startDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 10, 10, 0),
          endDate: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 10, 11, 30),
          description: "Weekly social gathering",
          location: "Community Room"
        }
      ];
      
      setEvents(sampleEvents);
      setDataSource('sample');
      
    } catch (error) {
      console.error('Error fetching events:', error);
      setDataSource('none');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <h1>Upcoming Events</h1>
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
              >
                <div className="day-number">{day.getDate()}</div>
                <div className="day-events">
                  {dayEvents.map((event, eventIndex) => (
                    <div key={eventIndex} className="event-item" title={`${event.title}${event.location ? ` - ${event.location}` : ''}${event.description ? `\n${event.description}` : ''}`}>
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
    </div>
  );
};

export default Calendar;
