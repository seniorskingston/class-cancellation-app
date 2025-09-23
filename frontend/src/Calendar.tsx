import React, { useState, useEffect } from 'react';
import './Calendar.css';
import logo from './logo.png';
import homeIcon from './assets/home-icon.png';
import EventModal from './EventModal';

interface Event {
  id?: string;
  title: string;
  startDate: Date;
  endDate: Date;
  description?: string;
  location?: string;
}

type ViewMode = 'month' | 'week' | 'day';

interface CalendarProps {
  onBackToMain?: () => void;
  isMobileView?: boolean;
}

const Calendar: React.FC<CalendarProps> = ({ onBackToMain, isMobileView }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState<'real' | 'sample' | 'none'>('none');
  const [viewMode, setViewMode] = useState<ViewMode>('month');
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);

  // Generate calendar days based on view mode
  const generateCalendarDays = (): Date[] => {
    if (viewMode === 'day') {
      return [new Date(currentDate)];
    } else if (viewMode === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const days = [];
      for (let i = 0; i < 7; i++) {
        const day = new Date(startOfWeek);
        day.setDate(startOfWeek.getDate() + i);
        days.push(day);
      }
      return days;
    } else {
      // Month view
      const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      
      // Get the first day of the calendar grid (might be from previous month)
      const firstDayOfCalendar = new Date(firstDayOfMonth);
      firstDayOfCalendar.setDate(firstDayOfCalendar.getDate() - firstDayOfMonth.getDay());
      
      // Get the last day of the calendar grid (might be from next month)
      const lastDayOfCalendar = new Date(lastDayOfMonth);
      lastDayOfCalendar.setDate(lastDayOfCalendar.getDate() + (6 - lastDayOfMonth.getDay()));

      const calendarDays = [];
      const currentDay = new Date(firstDayOfCalendar);
      
      while (currentDay <= lastDayOfCalendar) {
        calendarDays.push(new Date(currentDay));
        currentDay.setDate(currentDay.getDate() + 1);
      }
      return calendarDays;
    }
  };

  const calendarDays = generateCalendarDays();

  // Get events for a specific date
  const getEventsForDate = (date: Date): Event[] => {
    return events.filter(event => {
      const eventDate = new Date(event.startDate);
      return eventDate.toDateString() === date.toDateString();
    });
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
    
    // Set initial view mode based on screen size and mobile view setting
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      // Always use the isMobileView prop if provided, otherwise use screen size
      const useMobileView = isMobileView !== undefined ? isMobileView : mobile;
      setIsMobile(useMobileView);
      
      // Auto-set view mode for mobile
      if (useMobileView && viewMode === 'month') {
        setViewMode('week');
      } else if (!useMobileView && viewMode === 'week') {
        setViewMode('month');
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Respond to isMobileView prop changes
  useEffect(() => {
    if (isMobileView !== undefined) {
      setIsMobile(isMobileView);
      
      // Auto-set view mode for mobile
      if (isMobileView && viewMode === 'month') {
        setViewMode('week');
      } else if (!isMobileView && viewMode === 'week') {
        setViewMode('month');
      }
    }
  }, [isMobileView, viewMode]);

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

  const isHoliday = (eventTitle: string): boolean => {
    const holidays = [
      'Labour Day',
      'Thanksgiving Day', 
      'Remembrance Day',
      'Christmas Day',
      'National Day of Truth and Reconciliation'
    ];
    return holidays.some(holiday => eventTitle.includes(holiday));
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Navigation functions
  const navigateDate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1));
    } else if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    } else {
      // Month view
      newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    }
    
    setCurrentDate(newDate);
  };

  const goToPreviousMonth = () => navigateDate('prev');
  const goToNextMonth = () => navigateDate('next');
  
  const goToToday = () => setCurrentDate(new Date());

  // Get title for current view
  const getViewTitle = () => {
    if (viewMode === 'day') {
      return `${monthNames[currentDate.getMonth()]} ${currentDate.getDate()}, ${currentDate.getFullYear()}`;
    } else if (viewMode === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      
      if (startOfWeek.getMonth() === endOfWeek.getMonth()) {
        return `${monthNames[startOfWeek.getMonth()]} ${startOfWeek.getDate()}-${endOfWeek.getDate()}, ${startOfWeek.getFullYear()}`;
      } else {
        return `${startOfWeek.getDate()} ${monthNames[startOfWeek.getMonth()]} - ${endOfWeek.getDate()} ${monthNames[endOfWeek.getMonth()]}, ${startOfWeek.getFullYear()}`;
      }
    } else {
      return `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
    }
  };

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
          <button 
            onClick={() => onBackToMain ? onBackToMain() : window.history.back()} 
            className="back-to-home-button"
            title="Back to Program Schedule Update"
          >
            <img src={homeIcon} alt="Home" className="home-icon" />
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
          
          {/* View Mode Controls - moved next to Today button */}
          {!isMobile && (
            <>
              <button 
                className={`view-button ${viewMode === 'month' ? 'active' : ''}`}
                onClick={() => setViewMode('month')}
              >
                Month
              </button>
              <button 
                className={`view-button ${viewMode === 'week' ? 'active' : ''}`}
                onClick={() => setViewMode('week')}
              >
                Week
              </button>
              <button 
                className={`view-button ${viewMode === 'day' ? 'active' : ''}`}
                onClick={() => setViewMode('day')}
              >
                Day
              </button>
            </>
          )}
          {isMobile && (
            <>
              <button 
                className={`view-button ${viewMode === 'week' ? 'active' : ''}`}
                onClick={() => setViewMode('week')}
              >
                Week
              </button>
              <button 
                className={`view-button ${viewMode === 'day' ? 'active' : ''}`}
                onClick={() => setViewMode('day')}
              >
                Day
              </button>
            </>
          )}
          
          {/* Desktop/Mobile Switch - moved to same line */}
          <div className="desktop-mobile-switch">
            <button 
              className={`switch-button ${!isMobile ? 'active' : ''}`}
              onClick={() => setIsMobile(false)}
            >
              {isMobile ? '🖥️ Desktop' : '📱 Mobile'}
            </button>
          </div>
        </div>
        
        
        <h2 className="month-year">
          {getViewTitle()}
        </h2>
        <div className="data-source-indicator">
          {dataSource === 'real' ? (
            <span className="real-data">✅ Live from Seniors Association Kingston Website</span>
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

      {/* Mobile List View - Show when mobile view is active */}
      {isMobile ? (
        <div className="mobile-list-view">
          {calendarDays.map((day, index) => {
            const isCurrentMonth = day.getMonth() === currentDate.getMonth();
            const isToday = day.toDateString() === new Date().toDateString();
            const dayEvents = getEventsForDate(day);

            return (
              <div key={index} className={`mobile-list-day ${isToday ? 'today' : ''}`}>
                <div className="mobile-day-header">
                  <div className="mobile-day-name">{dayNames[day.getDay()]}</div>
                  <div className="mobile-day-date">
                    {day.getDate()} {monthNames[day.getMonth()].substring(0, 3)}
                  </div>
                </div>
                <div className="mobile-day-events">
                  {dayEvents.length > 0 ? (
                    dayEvents.map((event, eventIndex) => (
                      <div 
                        key={eventIndex} 
                        className={`mobile-event-item ${isHoliday(event.title) ? 'holiday-event' : ''}`}
                        onClick={() => handleEventClick(event)}
                      >
                        <div className="mobile-event-time">
                          {event.startDate.toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit',
                            hour12: true 
                          })}
                        </div>
                        <div className="mobile-event-title">{event.title}</div>
                        {event.location && (
                          <div className="mobile-event-location">📍 {event.location}</div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="mobile-no-events">No events</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Desktop Grid View */
        <div className={`calendar-grid ${viewMode}-view`}>
          {/* Day headers */}
          {viewMode !== 'day' && (
            <div className="calendar-weekdays">
              {dayNames.map(day => (
                <div key={day} className="weekday-header">{day}</div>
              ))}
            </div>
          )}

          {/* Calendar days */}
          <div className={`calendar-days ${viewMode}-days`}>
            {calendarDays.map((day, index) => {
              const isCurrentMonth = day.getMonth() === currentDate.getMonth();
              const isToday = day.toDateString() === new Date().toDateString();
              const dayEvents = getEventsForDate(day);

              return (
                <div
                  key={index}
                  className={`calendar-day ${viewMode}-day ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                  onClick={() => {
                    if (viewMode === 'day') {
                      setSelectedDate(day);
                      setSelectedEvent(null);
                      setIsModalOpen(true);
                    } else {
                      handleDayClick(day.getDate());
                    }
                  }}
                >
                  <div className="day-number">{day.getDate()}</div>
                  <div className="day-events">
                    {dayEvents.map((event, eventIndex) => (
                      <div 
                        key={eventIndex} 
                        className={`event-item ${isHoliday(event.title) ? 'holiday-event' : ''}`}
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
      )}

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
