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
  dateStr?: string;
  timeStr?: string;
  image_url?: string;
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
  
  // Debug: Log view mode changes
  useEffect(() => {
    console.log('🔍 View mode changed to:', viewMode);
    console.log('📱 Is mobile:', isMobile);
    console.log('📱 Window width:', window.innerWidth);
    console.log('📱 isMobileView prop:', isMobileView);
  }, [viewMode, isMobile, isMobileView]);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);

  // Handle event click
  const handleEventClick = (event: Event) => {
    setSelectedEvent(event);
    setIsModalOpen(true);
  };

  // Close modal
  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedEvent(null);
  };

  // Generate calendar days based on view mode
  const generateCalendarDays = (): Date[] => {
    console.log('🔄 Generating calendar days for view mode:', viewMode);
    
    if (viewMode === 'day') {
      const day = [new Date(currentDate)];
      console.log('📅 Day view: 1 day generated');
      return day;
    } else if (viewMode === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const days = [];
      for (let i = 0; i < 7; i++) {
        const day = new Date(startOfWeek);
        day.setDate(startOfWeek.getDate() + i);
        days.push(day);
      }
      console.log('📅 Week view: 7 days generated:', days.map(d => d.toDateString()));
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

  // Debug: Log calendar days count after generation
  useEffect(() => {
    console.log('📅 Calendar days count:', calendarDays.length);
  }, [calendarDays.length]);

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
    // Temporarily force local API for testing
    return 'http://localhost:8000/api';
    // return process.env.NODE_ENV === 'production' 
    //   ? 'https://class-cancellation-backend.onrender.com/api'
    //   : 'http://localhost:8000/api';
  };

  const fetchEvents = async () => {
    setLoading(true);
    const apiUrl = getApiUrl();
    console.log('🔍 Fetching events from:', apiUrl);
    try {
      const response = await fetch(`${apiUrl}/events`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Backend response:', data);
        
        if (data.events && data.events.length > 0) {
          console.log(`📅 Processing ${data.events.length} events from backend`);
          
          // Convert backend events to frontend format
          const convertedEvents: Event[] = data.events.map((event: any) => ({
            id: event.id,
            title: event.title,
            startDate: new Date(event.startDate),
            endDate: new Date(event.endDate),
            description: event.description || '',
            location: event.location || '',
            // Preserve additional fields from scraped events
            dateStr: event.dateStr,
            timeStr: event.timeStr,
            image_url: event.image_url
          }));
          
          // Check for November events
          const novEvents = convertedEvents.filter(event => 
            event.dateStr && event.dateStr.includes('November')
          );
          console.log(`🍂 November events found: ${novEvents.length}`);
          
          // Check for banner images
          const bannerEvents = convertedEvents.filter(event => 
            event.image_url && event.image_url.includes('cms.seniorskingston.ca')
          );
          console.log(`🖼️ Events with banners: ${bannerEvents.length}`);
          
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
      
      // Auto-set view mode for mobile only
      if (useMobileView && viewMode === 'month') {
        setViewMode('week');
      }
      // Removed automatic month override for desktop - let user choose
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobileView]); // Add isMobileView to dependencies

  // Respond to isMobileView prop changes
  useEffect(() => {
    if (isMobileView !== undefined) {
      setIsMobile(isMobileView);
      
      // Auto-set view mode for mobile only
      if (isMobileView && viewMode === 'month') {
        setViewMode('week');
      }
      // Removed automatic month override for desktop - let user choose
    }
  }, [isMobileView, viewMode]);

  const handleDayClick = (day: number) => {
    const clickedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    setSelectedDate(clickedDate);
    setSelectedEvent(null);
    setIsModalOpen(true);
  };



  const isHoliday = (eventTitle: string): boolean => {
    const holidays = [
      // 2025 Holidays
      'New Year\'s Day',
      'Good Friday',
      'Easter Monday',
      'Victoria Day',
      'Saint-Jean-Baptiste Day',
      'Canada Day',
      'Civic Holiday',
      'Labour Day',
      'National Day for Truth and Reconciliation',
      'Thanksgiving Day',
      'Christmas Day',
      'Boxing Day',
      // 2026 Holidays
      'Family Day'
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
            className="app-logo clickable-logo custom-tooltip"
            onClick={() => window.open('https://www.seniorskingston.ca/', '_blank')}
            data-tooltip="Visit Seniors Kingston Website"
          />
          <button 
            onClick={() => onBackToMain ? onBackToMain() : window.history.back()} 
            className="back-to-home-button custom-tooltip"
            data-tooltip="Back to Program Schedule Update"
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
          <button onClick={goToPreviousMonth} className="nav-button custom-tooltip" data-tooltip="Previous Month/Week/Day">‹</button>
          <button onClick={goToToday} className="today-button custom-tooltip" data-tooltip="Go to Today">Today</button>
          <button onClick={goToNextMonth} className="nav-button custom-tooltip" data-tooltip="Next Month/Week/Day">›</button>
          
          {/* View Mode Controls - moved next to Today button */}
          {!isMobile && (
            <>
              <button 
                className={`view-button custom-tooltip ${viewMode === 'month' ? 'active' : ''}`}
                onClick={() => {
                  console.log('🔘 Month button clicked!');
                  setViewMode('month');
                }}
                data-tooltip="Month View"
              >
                Month
              </button>
              <button 
                className={`view-button custom-tooltip ${viewMode === 'week' ? 'active' : ''}`}
                onClick={() => {
                  console.log('🔘 Week button clicked!');
                  setViewMode('week');
                }}
                data-tooltip="Week View"
              >
                Week
              </button>
              <button 
                className={`view-button custom-tooltip ${viewMode === 'day' ? 'active' : ''}`}
                onClick={() => {
                  console.log('🔘 Day button clicked!');
                  setViewMode('day');
                }}
                data-tooltip="Day View"
              >
                Day
              </button>
            </>
          )}
          {isMobile && (
            <>
              <button 
                className={`view-button custom-tooltip ${viewMode === 'week' ? 'active' : ''}`}
                onClick={() => setViewMode('week')}
                data-tooltip="Week View"
              >
                Week
              </button>
              <button 
                className={`view-button custom-tooltip ${viewMode === 'day' ? 'active' : ''}`}
                onClick={() => setViewMode('day')}
                data-tooltip="Day View"
              >
                Day
              </button>
            </>
          )}
          
        </div>
        
        
        <h2 className="month-year">
          {getViewTitle()}
        </h2>
        <div className="data-source-indicator">
          {dataSource === 'real' ? (
            <span className="real-data">✅ Live from Seniors Association Kingston Website ({events.length} events)</span>
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
          <div style={{background: 'yellow', padding: '10px', margin: '10px'}}>
            DEBUG: Mobile view active, events: {events.length}
          </div>
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
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="mobile-event-time">
                          {event.timeStr || event.startDate.toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit',
                            hour12: true 
                          })}
                        </div>
                        <div className="mobile-event-title">{event.title}</div>
                        {event.dateStr && (
                          <div className="mobile-event-date">📅 {event.dateStr}</div>
                        )}
                        {event.location && (
                          <div className="mobile-event-location">📍 {event.location}</div>
                        )}
                        {event.description && event.description.length > 50 && (
                          <div className="mobile-event-description" title={event.description}>
                            {event.description.substring(0, 50)}...
                          </div>
                        )}
                        {/* Banner images removed from event list - only show in modal */}
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
        <div className={`calendar-grid ${viewMode}-view`} data-view-mode={viewMode}>
          <div style={{background: 'lightblue', padding: '10px', margin: '10px'}}>
            DEBUG: Desktop view active, events: {events.length}
          </div>
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
                  // onClick={() => {
                  //   if (viewMode === 'day') {
                  //     setSelectedDate(day);
                  //     setSelectedEvent(null);
                  //     setIsModalOpen(true);
                  //   } else {
                  //     handleDayClick(day.getDate());
                  //   }
                  // }} // Disabled - calendar is read-only
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
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="event-time">
                          {event.timeStr || event.startDate.toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit',
                            hour12: true 
                          })}
                        </div>
                        <div className="event-title">{event.title}</div>
                        {event.dateStr && (
                          <div className="event-date">📅 {event.dateStr}</div>
                        )}
                        {event.location && (
                          <div className="event-location">📍 {event.location}</div>
                        )}
                        {event.description && event.description.length > 30 && (
                          <div className="event-description" title={event.description}>
                            {event.description.substring(0, 30)}...
                          </div>
                        )}
                        {/* Banner images removed from event list - only show in modal */}
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
        isReadOnly={true}
      />
    </div>
  );
};

export default Calendar;
