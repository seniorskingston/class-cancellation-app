import React, { useState, useEffect } from 'react';
import './Calendar.css';
import logo from './logo.png';
import homeIcon from './assets/home-icon.png';
import rachelChatbotIcon from './assets/rachel-chatbot-icon.svg';
import EventViewModal from './EventViewModal';

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
  }, [viewMode, isMobile]);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [showRachelComingSoon, setShowRachelComingSoon] = useState(false);

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
      // Filter out past events
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (eventDate < today) {
        return false;
      }
      return eventDate.toDateString() === date.toDateString();
    });
  };
  
  // Get events within a date range (for week/day views)
  const getEventsInRange = (startDate: Date, endDate: Date): Event[] => {
    return events.filter(event => {
      const eventDate = new Date(event.startDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Filter out past events
      if (eventDate < today) {
        return false;
      }
      
      // Check if event is within the range
      return eventDate >= startDate && eventDate <= endDate;
    });
  };

  // Build a local date key YYYY-MM-DD without timezone shifts
  const toLocalDateKey = (d: Date): string => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Handle event click
  const handleEventClick = (event: Event) => {
    console.log('🎯 Event clicked:', event.title);
    setSelectedEvent(event);
    setIsModalOpen(true);
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
            location: event.location || '',
            dateStr: event.dateStr || '',
            timeStr: event.timeStr || '',
            image_url: event.image_url || "/event-schedule-banner.png",
            price: event.price || '',
            instructor: event.instructor || '',
            registration: event.registration || ''
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
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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


  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedEvent(null);
    setSelectedDate(undefined);
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
          <button 
            onClick={() => setShowRachelComingSoon(true)} 
            className="rachel-chatbot-button custom-tooltip"
            data-tooltip="Chat with Rachel (Coming Soon)"
          >
            <img src={rachelChatbotIcon} alt="Rachel Chatbot" className="rachel-chatbot-icon" />
          </button>
        </div>
        <h1>Event Schedule Update (Beta)</h1>
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
          
          {/* Edit Events Button */}
          
        </div>
        
        
        <h2 className="month-year">
          {getViewTitle()}
        </h2>
        <div className="data-source-indicator">
          {loading ? (
            <span className="loading-data">🔄 Events Loading...</span>
          ) : dataSource === 'real' ? (
            <span className="real-data">✅ Live from Seniors Association Kingston Website</span>
          ) : dataSource === 'sample' ? (
            <span className="sample-data">📅 Seniors Kingston events (based on real events from their website)</span>
          ) : (
            <span className="loading-data">🔄 Events Loading...</span>
          )}
        </div>
      </div>

      {/* Mobile List View - Show when mobile view is active */}
      {isMobile ? (
        <div className="mobile-list-view">
          {/* Show events filtered by view mode and date range for mobile */}
          {(() => {
            // Get the date range based on current view mode
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            let startDate: Date;
            let endDate: Date;
            
            if (viewMode === 'day') {
              startDate = new Date(currentDate);
              startDate.setHours(0, 0, 0, 0);
              endDate = new Date(startDate);
              endDate.setHours(23, 59, 59, 999);
            } else if (viewMode === 'week') {
              const startOfWeek = new Date(currentDate);
              startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
              startOfWeek.setHours(0, 0, 0, 0);
              startDate = startOfWeek;
              endDate = new Date(startOfWeek);
              endDate.setDate(endDate.getDate() + 6);
              endDate.setHours(23, 59, 59, 999);
            } else {
              // Month view - show all events from today onwards in the current month
              startDate = today;
              const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
              endDate = new Date(lastDayOfMonth);
              endDate.setHours(23, 59, 59, 999);
            }
            
            // Filter events to only show future events within the selected range
            const filteredEvents = events.filter(event => {
              const eventDate = new Date(event.startDate);
              eventDate.setHours(0, 0, 0, 0);
              
              // Filter out past events
              if (eventDate < today) {
                return false;
              }
              
              // Filter by date range based on view mode
              return eventDate >= startDate && eventDate <= endDate;
            });
            
            // Group events by individual date (using LOCAL date, not UTC)
            const eventsByDate: { [key: string]: Event[] } = {};
            filteredEvents.forEach(event => {
              const eventDate = new Date(event.startDate);
              eventDate.setHours(0, 0, 0, 0);
              const dateKey = toLocalDateKey(eventDate); // YYYY-MM-DD (local)
              if (!eventsByDate[dateKey]) {
                eventsByDate[dateKey] = [];
              }
              eventsByDate[dateKey].push(event);
            });

            // Sort dates
            const sortedDates = Object.keys(eventsByDate).sort();
            
            return sortedDates.map(dateKey => {
              const dayEvents = eventsByDate[dateKey];
              const [y, m, d] = dateKey.split('-').map(Number);
              const eventDate = new Date(y, (m || 1) - 1, d || 1);
              const monthName = monthNames[eventDate.getMonth()];
              const dayName = dayNames[eventDate.getDay()];
              const day = eventDate.getDate();
              
              return (
                <React.Fragment key={dateKey}>
                  {/* Date Header */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '8px',
                    padding: '8px 12px'
                  }}>
                    <span style={{ fontWeight: 'bold', color: '#333' }}>{dayName}</span>
                    <span style={{ fontWeight: 'bold', color: '#333' }}>{day} {monthName.substring(0, 3)}</span>
                  </div>
                  
                  {/* Events - Old Simple Style */}
                  {dayEvents.length === 0 ? (
                    <div style={{ 
                      textAlign: 'center', 
                      color: '#999', 
                      padding: '16px',
                      marginBottom: '20px'
                    }}>
                      No events
                    </div>
                  ) : (
                    dayEvents
                    .sort((a, b) => new Date(a.startDate).getTime() - new Date(b.startDate).getTime())
                    .map((event, eventIndex) => {
                        const evtDate = new Date(event.startDate);
                      
                      return (
                        <div 
                          key={eventIndex} 
                          onClick={() => handleEventClick(event)}
                            style={{ 
                              backgroundColor: '#0072ce',
                              borderRadius: '8px',
                              padding: '16px',
                              marginBottom: '12px',
                              cursor: 'pointer',
                              textAlign: 'center',
                              color: 'white'
                            }}
                          >
                            <div style={{ 
                              fontWeight: 'bold', 
                              fontSize: '1rem',
                              marginBottom: '4px'
                            }}>
                              {event.timeStr || evtDate.toLocaleTimeString('en-US', { 
                              hour: 'numeric', 
                              minute: '2-digit',
                              hour12: true 
                            })}
                          </div>
                            <div style={{ 
                              fontWeight: 'bold', 
                              fontSize: '1rem'
                            }}>
                              {event.title}
                            </div>
                        </div>
                      );
                      })
                  )}
                </React.Fragment>
              );
            });
          })()}
        </div>
      ) : (
        /* Desktop Grid View */
        <div className={`calendar-grid ${viewMode}-view`} data-view-mode={viewMode}>
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

      <EventViewModal
        isOpen={isModalOpen && selectedEvent !== null}
        onClose={closeModal}
        event={selectedEvent}
      />

      {/* Rachel Coming Soon Modal */}
      {showRachelComingSoon && (
        <div style={{
          position: 'fixed',
          top: '0',
          left: '0',
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          zIndex: 9999999999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}
        onClick={() => setShowRachelComingSoon(false)}
        >
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '40px',
            maxWidth: '500px',
            maxHeight: '90vh',
            overflow: 'auto',
            position: 'relative',
            border: '4px solid #00b388',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)',
            textAlign: 'center'
          }}
          onClick={e => e.stopPropagation()}
          >
            <div style={{ marginBottom: '20px' }}>
              <img 
                src={rachelChatbotIcon} 
                alt="Rachel Chatbot" 
                style={{ 
                  width: '120px', 
                  height: '120px', 
                  margin: '0 auto 20px',
                  display: 'block'
                }} 
              />
            </div>
            <h2 style={{ color: '#00b388', marginBottom: '15px', fontSize: '2rem' }}>
              Rachel
            </h2>
            <h3 style={{ color: '#333', marginBottom: '20px', fontSize: '1.5rem' }}>
              Coming Soon
            </h3>
            <p style={{ 
              color: '#666', 
              fontSize: '1.1rem', 
              lineHeight: '1.6',
              marginBottom: '30px'
            }}>
              Rachel, your AI assistant, will be here soon!
            </p>
            <button
              onClick={() => setShowRachelComingSoon(false)}
              style={{
                background: '#00b388',
                color: 'white',
                padding: '12px 30px',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: 'bold',
                transition: 'background 0.3s ease'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = '#009973'}
              onMouseOut={(e) => e.currentTarget.style.background = '#00b388'}
            >
              Got it!
            </button>
          </div>
        </div>
      )}

    </div>
  );
};

export default Calendar;
