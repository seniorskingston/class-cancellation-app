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
      
      const firstDayOfCalendar = new Date(firstDayOfMonth);
      firstDayOfCalendar.setDate(firstDayOfCalendar.getDate() - firstDayOfMonth.getDay());
      
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

  // Get API URL based on environment
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
          const convertedEvents: Event[] = data.events.map((event: any) => ({
            id: event.id,
            title: event.title,
            startDate: new Date(event.startDate),
            endDate: new Date(event.endDate),
            description: event.description || '',
            location: event.location || '',
            dateStr: event.dateStr,
            timeStr: event.timeStr,
            image_url: event.image_url
          }));
          
          console.log('Converted events:', convertedEvents);
          setEvents(convertedEvents);
          setDataSource('real');
          return;
        }
      }
      
      // Fallback to sample data
      setEvents([]);
      setDataSource('sample');
    } catch (error) {
      console.error('Error fetching events:', error);
      setEvents([]);
      setDataSource('none');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const goToPreviousMonth = () => {
    const newDate = new Date(currentDate);
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() - 1);
    } else if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setMonth(newDate.getMonth() - 1);
    }
    setCurrentDate(newDate);
  };

  const goToNextMonth = () => {
    const newDate = new Date(currentDate);
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() + 1);
    } else if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const getViewTitle = () => {
    if (viewMode === 'day') {
      return currentDate.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    } else if (viewMode === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      
      return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    } else {
      return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    }
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isHoliday = (title: string) => {
    const holidays = ['Christmas', 'New Year', 'Thanksgiving', 'Easter', 'Halloween'];
    return holidays.some(holiday => title.toLowerCase().includes(holiday.toLowerCase()));
  };

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  if (loading) {
    return (
      <div className="calendar-container">
        <div className="loading-message">Loading events...</div>
      </div>
    );
  }

  return (
    <div className="calendar-container">
      <header className="app-header">
        <div className="header-left">
          <img
            src={logo}
            alt="Seniors Kingston Logo"
            className="logo"
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
          {new Date().toLocaleString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </header>
      
      <div className="calendar-header">
        <div className="calendar-controls">
          <button onClick={goToPreviousMonth} className="nav-button custom-tooltip" data-tooltip="Previous Month/Week/Day">‹</button>
          <button onClick={goToToday} className="today-button custom-tooltip" data-tooltip="Go to Today">Today</button>
          <button onClick={goToNextMonth} className="nav-button custom-tooltip" data-tooltip="Next Month/Week/Day">›</button>
        </div>
        
        <div className="view-controls">
          <button
            className={`view-button custom-tooltip ${viewMode === 'month' ? 'active' : ''}`}
            onClick={() => setViewMode('month')}
            data-tooltip="Month View"
          >
            Month
          </button>
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
      
      <div className="loading-message">
        {loading ? 'Loading events...' : ''}
      </div>
      
      {isMobile ? (
        <div className="mobile-list-view">
          {calendarDays.map((day, index) => {
            const dayEvents = getEventsForDate(day);
            const isTodayDate = isToday(day);
            
            return (
              <div key={index} className={`mobile-list-day ${isTodayDate ? 'today' : ''}`}>
                <div className="mobile-day-header">
                  <div className="mobile-day-name">{dayNames[day.getDay()]}</div>
                  <div className="mobile-day-date">
                    {day.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </div>
                </div>
                <div className="mobile-day-events">
                  {dayEvents.length > 0 ? (
                    dayEvents.map((event, eventIndex) => (
                      <div 
                        key={eventIndex} 
                        className={`mobile-event-item ${isHoliday(event.title) ? 'holiday-event' : ''}`}
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
                        {event.image_url && event.image_url !== '/assets/event-schedule-banner.png' && (
                          <div className="mobile-event-image">
                            <img src={event.image_url} alt={event.title} className="event-banner-image" />
                          </div>
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
        <div className={`calendar-grid ${viewMode}-view`} data-view-mode={viewMode}>
          {viewMode !== 'day' && (
            <div className="calendar-weekdays">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="weekday-header">{day}</div>
              ))}
            </div>
          )}
          <div className={`calendar-days ${viewMode}-days`}>
            {calendarDays.map((day, index) => {
              const dayEvents = getEventsForDate(day);
              const isTodayDate = isToday(day);
              const isCurrentMonth = day.getMonth() === currentDate.getMonth();
              
              return (
                <div
                  key={index}
                  className={`calendar-day ${viewMode}-day ${isTodayDate ? 'today' : ''} ${!isCurrentMonth ? 'other-month' : ''}`}
                >
                  <div className="day-number">{day.getDate()}</div>
                  <div className="day-events">
                    {dayEvents.map((event, eventIndex) => (
                      <div
                        key={eventIndex}
                        className={`event-item ${isHoliday(event.title) ? 'holiday-event' : ''}`}
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
                        {event.image_url && event.image_url !== '/assets/event-schedule-banner.png' && (
                          <div className="event-image">
                            <img src={event.image_url} alt={event.title} className="event-banner-image" />
                          </div>
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
        onClose={() => setIsModalOpen(false)}
        onSave={() => {}}
        event={selectedEvent}
        selectedDate={selectedDate}
      />
    </div>
  );
};

export default Calendar;
