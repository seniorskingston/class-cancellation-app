// Simple Analytics for Class Cancellation App
// This will track user visits and show you clear numbers

interface AnalyticsEvent {
  event: string;
  timestamp: number;
  userAgent: string;
  url: string;
  referrer: string;
}

class SimpleAnalytics {
  private apiUrl = 'https://class-cancellation-backend.onrender.com';
  private sessionId: string;
  private userId: string;

  constructor() {
    // Generate unique session ID
    this.sessionId = this.generateId();
    
    // Get or create user ID
    this.userId = localStorage.getItem('analytics_user_id') || this.generateId();
    localStorage.setItem('analytics_user_id', this.userId);
    
    // Track page view on load
    this.trackPageView();
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  private async sendEvent(eventData: AnalyticsEvent) {
    try {
      await fetch(`${this.apiUrl}/api/analytics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...eventData,
          sessionId: this.sessionId,
          userId: this.userId,
        }),
      });
    } catch (error) {
      console.log('Analytics error (non-critical):', error);
    }
  }

  trackPageView() {
    this.sendEvent({
      event: 'page_view',
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      referrer: document.referrer,
    });
  }

  trackEvent(eventName: string, data?: any) {
    this.sendEvent({
      event: eventName,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      referrer: document.referrer,
    });
  }

  // Track specific app actions
  trackMessageSent() {
    this.trackEvent('message_sent');
  }

  trackProgramFavorited() {
    this.trackEvent('program_favorited');
  }

  trackQRCodeShared() {
    this.trackEvent('qr_code_shared');
  }

  trackAppInstalled() {
    this.trackEvent('app_installed');
  }

  trackEventCalendarViewed() {
    this.trackEvent('event_calendar_viewed');
  }
}

// Create global analytics instance
const analytics = new SimpleAnalytics();

export default analytics;


