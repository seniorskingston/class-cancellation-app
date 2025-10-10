import React, { useEffect, useState } from "react";
import "./App.css";
import logo from "./logo.png";
import QRCode from 'qrcode';
import Calendar from './Calendar';
import locationData from './locations.json';

type Cancellation = {
  sheet: string;
  program: string;
  program_id: string;
  date_range: string;
  time: string;
  location: string;
  class_room: string;  // Class Room from Facility
  instructor: string;  // Instructor
  program_status: string;
  class_cancellation: string;
  note: string;
  withdrawal: string;
  description: string;  // Description column
  fee: string;         // Fee column
  is_favorite?: boolean;  // Favorite status
};

type Filters = {
  program: string;
  program_id: string;
  day: string;
  location: string;
  program_status: string;
  view_type: string;
};

      const API_URL = "https://class-cancellation-backend.onrender.com";

// Helper function to get full address from location
const getFullAddress = (locationCode: string): string => {
  if (!locationCode || !locationData) {
    return "Address not available";
  }
  
  
  // Clean the location code
  const cleanLocationCode = locationCode.trim();
  
  // Direct mapping for the specific cases you mentioned
  const directMappings: { [key: string]: string } = {
    "SCE – Seniors Centre East": "SCE - Seniors Center East",
    "SCE - Seniors Centre East": "SCE - Seniors Center East", 
    "SCW – Seniors Centre West": "SCW - Seniors Centre West",
    "SCW - Seniors Centre West": "SCW - Seniors Centre West",
    "SCG - Seniors Centre Saint George's": "SCG - Seniors Centre Saint George's",
    "SCL - Seniors Centre Loyalist Amherstview": "SCLA - Seniors Centre Loyalist Amherstview",
    "SCN – Seniors Centre North": "SCN - Seniors Center North",
    "SCN - Seniors Centre North": "SCN - Seniors Center North"
  };
  
  // Try direct mapping first
  if (directMappings[cleanLocationCode]) {
    const mappedKey = directMappings[cleanLocationCode];
    const address = (locationData as any)[mappedKey];
    if (address) {
      return address;
    }
  }
  
  // Try exact match
  if ((locationData as any)[cleanLocationCode]) {
    return (locationData as any)[cleanLocationCode];
  }
  
  // Try case-insensitive exact match
  const lowerLocationCode = cleanLocationCode.toLowerCase();
  for (const [key, value] of Object.entries(locationData)) {
    if (key.toLowerCase() === lowerLocationCode) {
      return value;
    }
  }
  
  // Try to match by first part (before dash)
  const firstPart = cleanLocationCode.split(/[–-]/)[0].trim();
  
  for (const [key, value] of Object.entries(locationData)) {
    const keyFirstPart = key.split(' - ')[0].trim();
    
    if (firstPart === keyFirstPart) {
      return value;
    }
  }
  
  return "Address not available";
};

function App() {
  console.log("API_URL:", API_URL);
  const [cancellations, setCancellations] = useState<Cancellation[]>([]);
  const [filters, setFilters] = useState({
    program: "",
    program_id: "",
    day: "",
    location: "",
    program_status: "",
    view_type: "all", // New: "cancellations" or "all"
  });
  const [lastLoaded, setLastLoaded] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [locations, setLocations] = useState<string[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<Cancellation | null>(null);
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [messageProgram, setMessageProgram] = useState<Cancellation | null>(null);
  const [messageText, setMessageText] = useState("");

  // Debug: Log modal state changes
  useEffect(() => {
    console.log('📱 Modal state changed:', { 
      showMessageModal, 
      messageProgram: messageProgram?.program,
      isMobile: window.innerWidth < 768 
    });
    if (showMessageModal && messageProgram) {
      console.log('✅ MODAL SHOULD BE VISIBLE NOW!');
    }
  }, [showMessageModal, messageProgram]);


  const [showUserGuide, setShowUserGuide] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [mobileSearch, setMobileSearch] = useState<string>("");
  const [showQRCode, setShowQRCode] = useState(false);
  const [showFloatingQR, setShowFloatingQR] = useState(true);
  const [qrCodeDataURL, setQrCodeDataURL] = useState<string>('');
  const [currentView, setCurrentView] = useState<'main' | 'calendar'>('main');


  // Generate QR code for the current URL
  const generateQRCode = async () => {
    try {
      const currentURL = window.location.href;
      console.log('Generating QR code for URL:', currentURL);
      const qrDataURL = await QRCode.toDataURL(currentURL, {
        width: 300,
        margin: 4,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        },
        errorCorrectionLevel: 'M'
      });
      console.log('QR code generated successfully:', qrDataURL ? 'Yes' : 'No');
      setQrCodeDataURL(qrDataURL);
    } catch (error) {
      console.error('Error generating QR code:', error);
    }
  };

  // Load favorites from localStorage on component mount
  useEffect(() => {
    const savedFavorites = localStorage.getItem('classCancellationFavorites');
    if (savedFavorites) {
      try {
        const favoritesArray = JSON.parse(savedFavorites);
        setFavorites(new Set(favoritesArray));
        console.log('Loaded favorites from localStorage:', favoritesArray);
      } catch (error) {
        console.error('Error loading favorites from localStorage:', error);
      }
    }
  }, []);

  // Generate QR code on component mount
  useEffect(() => {
    generateQRCode();
  }, []);

  // Debug QR code state
  useEffect(() => {
    console.log('QR Code state changed:', { showQRCode, qrCodeDataURL: qrCodeDataURL ? 'Generated' : 'Not generated' });
    if (showQRCode) {
      console.log('🚨 MODAL SHOULD BE VISIBLE NOW! 🚨');
      console.log('showQRCode is true, modal should render');
    }
  }, [showQRCode, qrCodeDataURL]);

  // Handle Escape key for QR code modal
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && showQRCode) {
        setShowQRCode(false);
      }
    };

    if (showQRCode) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [showQRCode]);
  const [isMobileView, setIsMobileView] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [isInStandaloneMode, setIsInStandaloneMode] = useState(false);
  const [showIOSBanner, setShowIOSBanner] = useState(false);

  // Update date and time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Detect mobile device
  useEffect(() => {
    const checkMobile = () => {
      const width = window.innerWidth;
      const userAgent = navigator.userAgent;
      
      // More comprehensive mobile detection
      const isMobileWidth = width <= 768;
      const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile/i.test(userAgent);
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      
      const isMobile = isMobileWidth || isMobileUA || isTouchDevice;
      
      console.log('Mobile detection:', {
        width: width,
        userAgent: userAgent,
        isMobileWidth: isMobileWidth,
        isMobileUA: isMobileUA,
        isTouchDevice: isTouchDevice,
        isMobile: isMobile
      });
      
      setIsMobileView(isMobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // PWA Install functionality
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallPrompt(true);
    };

    const handleAppInstalled = () => {
      setShowInstallPrompt(false);
      setDeferredPrompt(null);
      console.log('PWA was installed');
    };

    // Check device type and PWA status
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isAndroid = /Android/.test(navigator.userAgent);
    const standaloneMode = window.matchMedia('(display-mode: standalone)').matches;
    const isMobile = window.innerWidth <= 768 || isIOS || isAndroid;
    
    // Update standalone mode state
    setIsInStandaloneMode(standaloneMode);
    
    console.log('PWA Detection:', {
      isIOS,
      isAndroid,
      isMobile,
      isInStandaloneMode: standaloneMode,
      userAgent: navigator.userAgent
    });
    
    // Show install button for:
    // 1. Android/Chrome (beforeinstallprompt event)
    // 2. iOS Safari (not in standalone mode)
    // 3. Any mobile device not in standalone mode
    if (isMobile && !standaloneMode) {
      setShowInstallPrompt(true);
    }
    
    // Show iOS banner for users not in standalone mode
    if (isIOS && !standaloneMode) {
      setShowIOSBanner(true);
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  // Fix Android PWA text scaling issues - ONLY for saved app
  useEffect(() => {
    // Check if it's Android and in standalone mode (saved app)
    const isAndroid = /Android/i.test(navigator.userAgent);
    if (isInStandaloneMode && isAndroid) {
      // Add Android-specific class for CSS-based scaling
      document.body.classList.add('android-pwa');
      
      // Set viewport for saved app only (allow user scaling)
      const viewport = document.querySelector('meta[name="viewport"]');
      if (viewport) {
        viewport.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes');
      }
    }
  }, [isInStandaloneMode]);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Android/Chrome PWA install
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User response to the install prompt: ${outcome}`);
      setDeferredPrompt(null);
      setShowInstallPrompt(false);
    } else {
      // iOS Safari - show instructions
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      if (isIOS) {
        if (isInStandaloneMode) {
          // We're already in PWA mode, so we can't add to home screen again
          alert('📱 This app is already installed!\n\nYou\'re currently using the installed version.\n\nTo reinstall or update:\n1. Delete the current app from your home screen\n2. Open Safari and visit this website\n3. Use the Share button to add it again\n\n✨ The app is working as intended!');
        } else {
          // We're in Safari, show normal instructions
          alert('📱 To save this app:\n\n1. Look for the Share button at the BOTTOM of Safari\n   (Square with arrow up: [share icon])\n2. Tap the Share button\n3. Scroll down and tap "Add to Home Screen"\n4. Tap "Add" to confirm\n\n✨ The app will then work like a native app!');
        }
      } else {
        alert('📱 To save this app:\n\n1. Look for the install icon in your browser\n2. Or use your browser\'s menu to "Add to Home Screen"\n3. Follow the prompts to install\n\n✨ The app will then work like a native app!');
      }
    }
  };

  const fetchCancellations = async (customFilters: Filters | null = null) => {
    setLoading(true);
    try {
    const params = new URLSearchParams();
      
      // Use custom filters if provided, otherwise use current filters
      const filtersToUse = customFilters || filters;
      Object.entries(filtersToUse).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
      if (filtersToUse.view_type === "cancellations") params.append("has_cancellation", "true");
      
      const url = `${API_URL}/api/cancellations?${params.toString()}`;
      console.log("Fetching from:", url);
      console.log("Filters being used:", filtersToUse);
      console.log("URL parameters:", params.toString());
      
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
    const data = await res.json();
      console.log("Received data:", data);
      console.log("Data count:", data.data ? data.data.length : 0);
      console.log("Is mobile view:", isMobileView);
      console.log("API URL:", url);
      
    setCancellations(data.data);
    setLastLoaded(data.last_loaded);
      
      // Extract unique locations for filter dropdown
      const uniqueLocations = Array.from(new Set(data.data.map((item: any) => item.location).filter((loc: any) => loc && loc !== ''))).sort() as string[];
      setLocations(uniqueLocations);
    } catch (error) {
      console.error("Error fetching cancellations:", error);
      setCancellations([]);
    } finally {
    setLoading(false);
    }
  };

  useEffect(() => {
    fetchCancellations();
    fetchAllcancellations(); // Also fetch all cancellations for pinned items
    const interval = setInterval(() => fetchCancellations(), 5 * 60 * 1000); // 5 min
    return () => clearInterval(interval);
    // eslint-disable-next-line
  }, [filters, isMobileView]);

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (name === "program") {
      // For unified search, set both program and program_id
      const newFilters = { 
        ...filters, 
        program: value, 
        program_id: value,
        view_type: "all" // Always search all cancellations to show pinned classes
      };
      setFilters(newFilters);
      
      // Trigger search immediately for program search
      await fetchCancellations(newFilters);
    } else {
      setFilters({ ...filters, [name]: value });
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      console.log('🔄 REFRESH: Starting data refresh...');
      // Force fresh data fetch with timestamp to prevent caching
      const timestamp = new Date().getTime();
      await fetch(`${API_URL}/api/cancellations?t=${timestamp}`, {
        method: 'GET',
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }).then(res => res.json()).then(data => {
        console.log('🔄 REFRESH: Data refreshed successfully');
        setCancellations(data.data);
        setLastLoaded(data.last_loaded);
      });
    } catch (error) {
      console.error("🔄 REFRESH ERROR:", error);
      alert("Refresh failed. Please try refreshing the browser page instead.");
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (programId: string) => {
    console.log('Toggling favorite for program ID:', programId);
    setFavorites(prev => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(programId)) {
        newFavorites.delete(programId);
        console.log('Removed from favorites:', programId);
      } else {
        newFavorites.add(programId);
        console.log('Added to favorites:', programId);
      }
      
      // Save to localStorage
      const favoritesArray = Array.from(newFavorites);
      localStorage.setItem('classCancellationFavorites', JSON.stringify(favoritesArray));
      console.log('Saved favorites to localStorage:', favoritesArray);
      
      return newFavorites;
    });
  };

  const handleSendMessage = async (program: Cancellation, message: string) => {
    console.log('🚀 Sending message:', { program: program.program, message });
    
    try {
      const subject = `${program.program} (ID: ${program.program_id.split('.')[0]}) - ${program.instructor}`;
      
      console.log('📧 API URL:', API_URL);
      console.log('📧 Subject:', subject);
      
      const response = await fetch(`${API_URL}/api/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject: subject,
          message: message,
          program_name: program.program,
          program_id: program.program_id.split('.')[0],
          instructor: program.instructor
        })
      });

      console.log('📧 Response status:', response.status);
      const responseData = await response.json();
      console.log('📧 Response data:', responseData);

      if (response.ok) {
        if (responseData.status === 'warning') {
          alert(`⚠️ ${responseData.message}\n\nYour message has been logged on the server. Please check with the administrator.`);
        } else {
          alert('✅ Message sent successfully to info@seniorskingston.ca!');
        }
        setShowMessageModal(false);
        setMessageText("");
        setMessageProgram(null);
      } else {
        alert(`❌ Failed to send message: ${responseData.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('❌ Error sending message:', error);
      if (error instanceof TypeError && error.message.includes('fetch')) {
        alert('❌ Cannot connect to server. Backend might be down. Please try again later.');
      } else {
        alert(`❌ Error sending message: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  };

  // Normalize program ID by stripping leading zeros
  const normalizeProgramId = (id: string): string => {
    return id.replace(/^0+/, '') || '0';
  };

  // Mobile search function
  const handleMobileSearch = async () => {
    const searchTerm = mobileSearch.trim();
    
    // Always search all cancellations to show pinned classes
    const newFilters = { 
      ...filters, 
      program: searchTerm, 
      program_id: searchTerm, // Use original search term for ID search
      view_type: "all" // Always search all cancellations to show pinned classes
    };
    setFilters(newFilters);
    
    // Trigger data fetch after setting filters
    await fetchCancellations(newFilters);
  };

  // Get all cancellations (for pinned cancellations that might not be in filtered results)
  const [allcancellations, setAllcancellations] = useState<Cancellation[]>([]);

  // Fetch all cancellations (without filters) to ensure pinned cancellations are always available
  const fetchAllcancellations = async () => {
    try {
      const url = `${API_URL}/api/cancellations`;
      const res = await fetch(url);
      
      if (res.ok) {
        const data = await res.json();
        setAllcancellations(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch all cancellations:", error);
    }
  };

  // Fetch all cancellations when favorites change (to ensure pinned cancellations are available)
  useEffect(() => {
    if (favorites.size > 0) {
      fetchAllcancellations();
    }
  }, [favorites]);

  // Combine pinned cancellations with current filtered results
  const sortedCancellations = (() => {
    const currentResults = [...cancellations];
    const allcancellationsList = [...allcancellations];
    
    // Get pinned cancellations from all cancellations
    const pinnedResults = allcancellationsList.filter(p => favorites.has(p.program_id));
    
    // Remove duplicates (pinned cancellations that are already in current results)
    const currentIds = new Set(currentResults.map(p => p.program_id));
    const uniquePinned = pinnedResults.filter(p => !currentIds.has(p.program_id));
    
    // Combine: unique pinned cancellations first, then current results
    const combined = [...uniquePinned, ...currentResults];
    
    // Sort within each group (pinned first, then regular)
    return combined.sort((a, b) => {
      const aIsFavorite = favorites.has(a.program_id);
      const bIsFavorite = favorites.has(b.program_id);
      
      if (aIsFavorite && !bIsFavorite) return -1;
      if (!aIsFavorite && bIsFavorite) return 1;
      return 0;
    });
  })();

  // Debug logging
  console.log('Favorites state:', Array.from(favorites));
  console.log('All cancellations count:', allcancellations.length);
  console.log('Current filtered results count:', cancellations.length);
  console.log('Sorted cancellations count:', sortedCancellations.length);
  console.log('Pinned cancellations in results:', sortedCancellations.filter(p => favorites.has(p.program_id)).length);

  const handleExport = async (format: 'excel' | 'pdf') => {
    try {
      setLoading(true);
      
      // Build query parameters based on current filters
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      if (filters.view_type === "cancellations") params.append("has_cancellation", "true");
      
      // Call export endpoint
      const res = await fetch(`${API_URL}/export-${format}?${params.toString()}`);
      
      if (!res.ok) {
        throw new Error(`Export failed: ${res.status}`);
      }
      
      if (format === 'excel') {
        // Handle Excel export
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `class_cancellations_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        // Handle PDF export
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `class_cancellations_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
      
    } catch (error) {
      console.error(`Error exporting to ${format}:`, error);
      alert(`Export to ${format.toUpperCase()} failed. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

        // Calendar view
        if (currentView === 'calendar') {
          return (
            <div className="App">
              <Calendar 
                onBackToMain={() => setCurrentView('main')} 
                isMobileView={isMobileView}
              />
            </div>
          );
        }

  // Mobile view
  if (isMobileView) {
    return (
      <div className="App mobile-view">
        <header className="mobile-header">
          <div className="mobile-header-left">
            <img 
            src={logo} 
            alt="Company Logo" 
            className="mobile-logo clickable-logo custom-tooltip"
            onClick={() => window.open('https://www.seniorskingston.ca/', '_blank')}
            data-tooltip="Visit Seniors Kingston Website"
            />
            <button 
              onClick={() => setCurrentView('calendar')} 
              className="mobile-events-schedule-image-button custom-tooltip"
              data-tooltip="View Event Schedule"
            >
              <img src={require('./assets/event-schedule-banner.png')} alt="Event Schedule" className="mobile-events-schedule-image" />
            </button>
          </div>
          <h1>Program Schedule Update</h1>
          <div className="mobile-datetime">
            {currentDateTime.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })}
          </div>
          <div className="mobile-header-buttons">
            <button 
              onClick={() => setIsMobileView(false)} 
              className="mobile-to-desktop-button custom-tooltip"
              data-tooltip="Switch to Desktop View"
            >
              🖥️ Desktop
            </button>
            
            <button 
              onClick={() => {
                console.log('🔄 MOBILE REFRESH clicked');
                handleRefresh();
              }} 
              className="refresh-button custom-tooltip"
              data-tooltip="Refresh Data"
            >
              🔄 Refresh
            </button>
            <button 
              onClick={() => {
                console.log('📱 MOBILE QR CODE clicked');
                console.log('Current showQRCode state:', showQRCode);
                console.log('Current qrCodeDataURL:', qrCodeDataURL ? 'Generated' : 'Not generated');
                
                // Generate QR code if not already generated
                if (!qrCodeDataURL) {
                  console.log('Generating QR code...');
                  generateQRCode();
                }
                
                console.log('Setting showQRCode to true');
                setShowQRCode(true);
              }} 
              className="mobile-share-button custom-tooltip"
              data-tooltip="Share App QR Code"
            >
              <img src="/users-icon-white.svg" alt="Share" style={{ height: '1.2em', verticalAlign: 'middle', marginRight: '5px' }} />
              Share
            </button>
            {!isInStandaloneMode && (
              <button 
                onClick={handleInstallClick} 
                className="install-button custom-tooltip"
                data-tooltip="Install App on Device"
              >
                📲 Save
              </button>
            )}
          </div>
        </header>
        
        <div className="mobile-controls">
          <div className="mobile-search-container">
            <input
              type="text"
              placeholder="Search by program name or ID..."
              value={mobileSearch}
              onChange={(e) => setMobileSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleMobileSearch()}
              className="mobile-search-input"
            />
            <button 
              onClick={handleMobileSearch}
              className="mobile-search-button custom-tooltip"
              data-tooltip="Search cancellations"
            >
              🔍
            </button>
          </div>
        </div>



        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading program data...</p>
          </div>
        )}

        
        {/* iOS Installation Banner */}
        {showIOSBanner && (
          <div className="ios-banner">
            <div className="ios-banner-content">
              <span>📱 Save the app: tap Share <img src="/share-icon-white.svg" alt="Share" style={{width: '16px', height: '16px', verticalAlign: 'middle', margin: '0 2px'}} /> → Add to Home Screen</span>
              <button 
                onClick={() => setShowIOSBanner(false)}
                className="ios-banner-close"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Debug info for mobile */}
        <div className="mobile-debug" style={{ fontSize: '12px', color: '#666', padding: '5px', textAlign: 'center' }}>
          Mobile View: {isMobileView ? 'Yes' : 'No'} | Data: {sortedCancellations.length} cancellations
          {selectedLocation && (
            <div style={{ background: 'yellow', color: 'black', padding: '5px', margin: '5px' }}>
              🚨 MODAL SHOULD BE VISIBLE! selectedLocation: {selectedLocation}
            </div>
          )}
        </div>

        <div className="mobile-data">
          {sortedCancellations.length === 0 ? (
            <div className="mobile-no-data">
              No class cancellations found.
            </div>
          ) : (
            sortedCancellations.map((c, i) => {
              const isFavorite = favorites.has(c.program_id);
              return (
                <div key={i} className={`mobile-card ${isFavorite ? 'favorite' : ''}`}>
                  <div className="mobile-card-header">
                    <span 
                      className={`mobile-star ${isFavorite ? 'favorited' : ''}`}
                      onClick={() => toggleFavorite(c.program_id)}
                    >
                      {isFavorite ? '★' : '☆'}
                    </span>
                    <div className="mobile-program-info">
                      <div 
                        className="mobile-program-name"
                        onClick={() => setSelectedProgram(c)}
                        data-tooltip="More information about this program"
                        style={{ cursor: 'pointer', color: '#0072ce', textDecoration: 'underline' }}
                      >
                        {c.program}
                      </div>
                      <div className="mobile-program-id" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 'bold' }}>ID: {c.program_id.split('.')[0]}</span>
                        <img 
                          src="/message-icon.svg"
                          alt="Send message"
                          className="message-icon custom-tooltip"
                          onTouchStart={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('📱 Mobile message icon touch start!', c.program);
                            setMessageProgram(c);
                            setShowMessageModal(true);
                            console.log('📱 showMessageModal set to true via touch');
                          }}
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('🖱️ Mobile message icon clicked!', c.program);
                            setMessageProgram(c);
                            setShowMessageModal(true);
                            console.log('📱 showMessageModal set to true via click');
                          }}
                          data-tooltip="Send a message regarding this program"
                          style={{
                            cursor: 'pointer',
                            width: '20px',
                            height: '20px',
                            transition: 'transform 0.2s ease'
                          }}
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="mobile-card-details">
                    <div className="mobile-detail-row">
                      <span className="mobile-label">Day:</span>
                      <span className="mobile-value">{c.sheet}</span>
                    </div>
                    <div className="mobile-detail-row">
                      <span className="mobile-label">Time:</span>
                      <span className="mobile-value">{c.time}</span>
                    </div>
                    <div className="mobile-detail-row">
                      <span className="mobile-label">Date Range:</span>
                      <span className="mobile-value">{c.date_range}</span>
                    </div>
                    <div className="mobile-detail-row">
                    <span className="mobile-label">Location:</span>
                    <span 
                      className="mobile-value"
                      onClick={() => {
                        setSelectedLocation(c.location);
                      }}
                      style={{ cursor: 'pointer', color: '#0072ce', textDecoration: 'underline' }}
                    >
                      {c.location}
                    </span>
                    </div>
                    <div className="mobile-detail-row">
                      <span className="mobile-label">Room:</span>
                      <span className="mobile-value">{c.class_room}</span>
                    </div>
                    <div className="mobile-detail-row">
                      <span className="mobile-label">Instructor:</span>
                      <span className="mobile-value">{c.instructor}</span>
                    </div>
                    <div className="mobile-detail-row">
                      <span className="mobile-label">Cancelled:</span>
                      <span className="mobile-value mobile-cancellation">
                        {c.class_cancellation && c.class_cancellation !== '' ? 
                          c.class_cancellation.split(';').map((date, index) => {
                            const trimmedDate = date.trim();
                            if (trimmedDate) {
                              try {
                                // Normalize date format: replace period with comma for better parsing
                                const normalizedDate = trimmedDate.replace(/\./g, ',');
                                const parsedDate = new Date(normalizedDate);
                                if (!isNaN(parsedDate.getTime())) {
                                  return (
                                    <div key={index}>
                                      {parsedDate.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })}
                                    </div>
                                  );
                                } else {
                                  // If parsing still fails, show the original text
                                  return (
                                    <div key={index}>
                                      {trimmedDate}
                                    </div>
                                  );
                                }
                              } catch (e) {
                                // If parsing fails, show the original text
                                return (
                                  <div key={index}>
                                    {trimmedDate}
                                  </div>
                                );
                              }
                            }
                            return null;
                          }).filter(Boolean) || c.class_cancellation : 'N/A'}
                      </span>
                    </div>
                    {c.note && c.note !== '' && (
                      <div className="mobile-detail-row">
                        <span className="mobile-label">Note:</span>
                        <span className="mobile-value">{c.note}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
        
        
        {/* PROGRAM DETAILS MODAL - Mobile */}
        {selectedProgram && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999999999,
            padding: '20px'
          }}
          onClick={() => {
            setSelectedProgram(null);
          }}
          >
            <div style={{
              background: 'white',
              padding: '30px',
              borderRadius: '12px',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
              maxWidth: '90vw',
              maxHeight: '80vh',
              border: '3px solid #0072ce',
              textAlign: 'center',
              position: 'relative',
              overflow: 'auto'
            }}
            onClick={(e) => {
              e.stopPropagation();
            }}
            >
              <h3 style={{ marginBottom: '20px', color: '#0072ce' }}>{selectedProgram.program}</h3>
              
              
              {/* Always show Description section */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ color: '#333', marginBottom: '10px' }}>Description:</h4>
                <p style={{ fontSize: '1rem', lineHeight: '1.6', textAlign: 'left' }}>
                  {selectedProgram.description && selectedProgram.description.trim() !== '' 
                    ? selectedProgram.description 
                    : 'No description available'}
                </p>
              </div>
              
              {/* Always show Fee section */}
              <div style={{ marginBottom: '30px' }}>
                <h4 style={{ color: '#333', marginBottom: '10px' }}>Fee:</h4>
                <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#0072ce' }}>
                  {selectedProgram.fee && selectedProgram.fee.trim() !== '' 
                    ? selectedProgram.fee 
                    : 'No fee information available'}
                </p>
              </div>
              
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedProgram(null);
                }}
                style={{
                  background: '#0072ce',
                  color: 'white',
                  border: 'none',
                  padding: '12px 30px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 'bold'
                }}
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* LOCATION MODAL - MOVED HERE TO MATCH WORKING MODAL */}
        {selectedLocation && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999999999,
            padding: '20px'
          }}
          onClick={() => {
            setSelectedLocation(null);
          }}
          >
            <div style={{
              background: 'white',
              padding: '30px',
              borderRadius: '12px',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
              maxWidth: '90vw',
              maxHeight: '80vh',
              border: '3px solid #0072ce',
              textAlign: 'center',
              position: 'relative',
              overflow: 'auto'
            }}
            onClick={(e) => {
              e.stopPropagation();
            }}
            >
              <h3 style={{ marginBottom: '20px', color: '#0072ce' }}>{selectedLocation}</h3>
              <p style={{ fontSize: '1.1rem', marginBottom: '30px', lineHeight: '1.6' }}>
                {getFullAddress(selectedLocation)}
              </p>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedLocation(null);
                }}
                style={{
                  background: '#0072ce',
                  color: 'white',
                  border: 'none',
                  padding: '12px 30px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 'bold'
                }}
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* QR Code Modal - Mobile */}
        {showQRCode && (
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
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '20px',
              maxWidth: '90vw',
              maxHeight: '90vh',
              overflow: 'auto',
              position: 'relative',
              border: '4px solid #0072ce',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)',
              textAlign: 'center'
            }}>
              <div style={{ marginBottom: '20px' }}>
                <h2 style={{ margin: '0 0 10px 0', color: '#0072ce' }}>Scan with your phone to open the app</h2>
                <button 
                  onClick={() => setShowQRCode(false)}
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    background: 'none',
                    border: 'none',
                    fontSize: '24px',
                    cursor: 'pointer',
                    color: '#666'
                  }}
                >
                  ×
                </button>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                {qrCodeDataURL ? (
                  <div style={{ position: 'relative', display: 'inline-block' }}>
                    <img 
                      src={qrCodeDataURL} 
                      alt="QR Code for app" 
                      style={{ 
                        width: '250px', 
                        height: '250px', 
                        border: '2px solid #ddd',
                        borderRadius: '8px'
                      }}
                    />
                    <div style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      background: 'white',
                      padding: '6px',
                      borderRadius: '6px',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)'
                    }}>
                      <img 
                        src={logo} 
                        alt="Company Logo" 
                        style={{ width: '25px', height: '25px', objectFit: 'contain' }}
                      />
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: '40px', color: '#666' }}>
                    <p>Generating QR code...</p>
                    <button 
                      onClick={generateQRCode}
                      style={{
                        background: '#0072ce',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '6px',
                        cursor: 'pointer'
                      }}
                    >
                      Retry
                    </button>
                  </div>
                )}
              </div>
              
              <div style={{ marginTop: '20px' }}>
                <button 
                  onClick={() => setShowQRCode(false)} 
                  style={{ 
                    background: '#0072ce', 
                    color: 'white',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Desktop view
  return (
    <div className="App">
      {/* Floating QR Code Button - Desktop Only */}
      {!isMobileView && showFloatingQR && (
        <div className="floating-qr-container">
          <button 
            className="floating-qr-button qr-code-button custom-tooltip"
            onClick={() => setShowQRCode(true)}
            data-tooltip="Open QR Code"
          >
            📱
          </button>
          <button 
            className="floating-qr-close custom-tooltip"
            onClick={() => setShowFloatingQR(false)}
            data-tooltip="Close QR Code"
          >
            ×
          </button>
        </div>
      )}

      <div className="sticky-header">
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
            onClick={() => setCurrentView('calendar')} 
            className="events-schedule-image-button custom-tooltip"
            data-tooltip="View Event Schedule"
          >
            <img src={require('./assets/event-schedule-banner.png')} alt="Event Schedule" className="events-schedule-image" />
          </button>
        </div>
        <h1>Program Schedule Update</h1>
        <div className="datetime-display">
            {currentDateTime.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })} {currentDateTime.toLocaleTimeString('en-CA', { timeZone: 'America/Toronto' })}
        </div>
        
      </header>
      </div>
      <div className="filters">
        <button 
          onClick={() => setIsMobileView(true)} 
          style={{ background: "#00b388", color: "white", fontSize: "0.75rem", padding: "0.3rem 0.6rem" }}
          className="custom-tooltip"
          data-tooltip="Switch to Mobile View"
        >
          📱 Mobile
        </button>
        <input
          name="program"
          placeholder="Program Name/ID"
          value={filters.program}
          onChange={handleInputChange}
        />
        <select name="day" value={filters.day} onChange={handleInputChange}>
          <option value="">All Days</option>
          <option>Monday</option>
          <option>Tuesday</option>
          <option>Wednesday</option>
          <option>Thursday</option>
          <option>Friday</option>
          <option>Saturday</option>
        </select>
          <select name="location" value={filters.location} onChange={handleInputChange}>
            <option value="">All Locations</option>
            {locations.map((location, index) => (
              <option key={index} value={location}>{location}</option>
            ))}
          </select>
        <select
          name="program_status"
          value={filters.program_status}
          onChange={handleInputChange}
        >
          <option value="">All Statuses</option>
          <option value="Cancelled">Cancelled</option>
          <option value="Active">Active</option>
          <option value="Additions">Additions</option>
        </select>
          <select
            name="view_type"
            value={filters.view_type}
            onChange={handleInputChange}
          >
            <option value="cancellations">Show Class Cancellations</option>
            <option value="all">Show All Programs</option>
        </select>
        <button onClick={handleRefresh} disabled={loading} className="custom-tooltip" data-tooltip="Refresh Data">
          {loading ? "Refreshing..." : "Refresh"}
        </button>
        <button 
          onClick={() => handleExport('excel')} 
          style={{ background: "#0072ce", color: "white" }}
          disabled={cancellations.length === 0}
          className="custom-tooltip"
          data-tooltip="Export to Excel"
        >
          📊 Excel
        </button>
        <button 
          onClick={() => handleExport('pdf')} 
          style={{ background: "#0072ce", color: "white" }}
          disabled={cancellations.length === 0}
          className="custom-tooltip"
          data-tooltip="Export to PDF"
        >
          📄 PDF
        </button>
        <button 
          onClick={() => setShowUserGuide(true)} 
          style={{ background: "#0072ce", color: "white" }}
          className="custom-tooltip"
          data-tooltip="View Help Guide"
        >
          📖 Help
        </button>
      </div>
      
      <div className="last-loaded">
        Last updated: {lastLoaded ? new Date(lastLoaded).toLocaleString('en-CA', { timeZone: 'America/Toronto' }) : "Never"}
      </div>
      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading program data...</p>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead className="sticky-thead">
            <tr>
              <th>☆</th>
              <th>Day</th>
              <th>Program</th>
              <th>Program ID</th>
              <th>Date Range</th>
              <th>Time</th>
              <th>Location</th>
              <th>Class Room</th>
              <th>Instructor</th>
              <th>Program Status</th>
              <th>Class Cancellation</th>
              <th>Additional Information</th>
              <th>Refund</th>
            </tr>
          </thead>
          <tbody>
            {sortedCancellations.length === 0 && (
              <tr>
                <td colSpan={13} style={{ textAlign: "center" }}>
                  No cancellations found.
                </td>
              </tr>
            )}
            {sortedCancellations.map((c, i) => {
              const isFavorite = favorites.has(c.program_id);
              return (
                <tr key={i} className={isFavorite ? 'favorite-row' : ''}>
                  <td>
                    <span 
                      className={`favorite-star custom-tooltip ${isFavorite ? 'favorited' : ''}`}
                      onClick={() => toggleFavorite(c.program_id)}
                      data-tooltip={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      {isFavorite ? '★' : '☆'}
                    </span>
                  </td>
                <td>{c.sheet}</td>
                <td
                  onClick={() => setSelectedProgram(c)}
                  data-tooltip="More information about this program"
                  style={{ cursor: 'pointer', color: '#0072ce', textDecoration: 'underline' }}
                >
                  {c.program}
                </td>
                <td style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 'bold' }}>{c.program_id.split('.')[0]}</span>
                    <img 
                      src="/message-icon.svg"
                      alt="Send message"
                      className="message-icon custom-tooltip"
                      onClick={() => {
                        setMessageProgram(c);
                        setShowMessageModal(true);
                      }}
                      data-tooltip="Send a message regarding this program"
                      style={{
                        cursor: 'pointer',
                        width: '20px',
                        height: '20px',
                        transition: 'transform 0.2s ease'
                      }}
                    />
                  </div>
                </td>
                <td>{c.date_range}</td>
                <td>{c.time}</td>
                <td 
                  onClick={() => {
                    setSelectedLocation(c.location);
                  }}
                  style={{ cursor: 'pointer', color: '#0072ce', textDecoration: 'underline' }}
                >
                  {c.location}
                </td>
                  <td>{c.class_room}</td>
                  <td>{c.instructor}</td>
                <td>{c.program_status}</td>
                  <td>{c.class_cancellation && c.class_cancellation !== '' ? 
                    c.class_cancellation.split(';').map((date, index) => {
                      const trimmedDate = date.trim();
                      if (trimmedDate) {
                        try {
                          // Normalize date format: replace period with comma for better parsing
                          const normalizedDate = trimmedDate.replace(/\./g, ',');
                          const parsedDate = new Date(normalizedDate);
                          if (!isNaN(parsedDate.getTime())) {
                            return (
                              <div key={index}>
                                {parsedDate.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })}
                              </div>
                            );
                          } else {
                            // If parsing still fails, show the original text
                            return (
                              <div key={index}>
                                {trimmedDate}
                              </div>
                            );
                          }
                        } catch (e) {
                          // If parsing fails, show the original text
                          return (
                            <div key={index}>
                              {trimmedDate}
                            </div>
                          );
                        }
                      }
                      return null;
                    }).filter(Boolean) || c.class_cancellation : ''}</td>
                  <td>{c.note && c.note !== '' ? c.note : ''}</td>
                <td>{c.program_status === "Cancelled" ? "" : c.withdrawal}</td>
              </tr>
            );
            })}
          </tbody>
        </table>
      </div>

      {/* User Guide Modal */}
      {showUserGuide && (
        <div className="modal-overlay" onClick={() => setShowUserGuide(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <header className="app-header">
              <img src={logo} alt="Company Logo" className="app-logo" />
              <h1>Program Schedule Update</h1>
              <div className="datetime-display">
                {currentDateTime.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })} {currentDateTime.toLocaleTimeString('en-CA', { timeZone: 'America/Toronto' })}
              </div>
            </header>
            <div className="user-guide-content">
              <h2>Program Schedule Update App – User Guide</h2>
              
              <p><strong>Welcome!</strong> This guide will help you use the Program Schedule Update App to quickly search, filter, and manage program schedules and cancellations. The app works on both desktop and mobile devices, and can be installed as a native app on your phone or tablet.</p>

              <h3>1. Getting Started</h3>
              <h4>Desktop vs Mobile View</h4>
              <ul>
                <li><strong>Desktop View:</strong> Full table with all filters and features</li>
                <li><strong>Mobile View:</strong> Automatically activates on phones/tablets, shows only class cancellations in a card format</li>
                <li><strong>Automatic Detection:</strong> The app automatically detects your device and switches to the appropriate view</li>
              </ul>

              <h4>Installing as a Mobile App</h4>
              <ul>
                <li><strong>iPhone/iPad:</strong> Tap "📲 Save App" → Look for Share button (□↑) at bottom of Safari → "Add to Home Screen"</li>
                <li><strong>Android:</strong> Chrome may prompt automatically, or use browser menu to "Add to Home Screen"</li>
                <li><strong>App Name:</strong> Will default to "Program" when installing</li>
                <li><strong>Benefits:</strong> Works like a native app, faster access, offline capabilities</li>
              </ul>

              <h3>2. Loading Data</h3>
              <ul>
                <li>When you open the app, please allow a few minutes for the data to load.</li>
                <li>If you previously left the app open, refresh the page to ensure the data is up to date.</li>
                <li>Data refreshes automatically every 5 minutes.</li>
              </ul>

              <h3>3. Searching for a Program</h3>
              <p>You can search for a program using:</p>
              <ul>
                <li><strong>Program Name</strong></li>
                <li><strong>Program ID</strong></li>
                <li><strong>Day & Location</strong></li>
              </ul>

              <h3>4. Understanding Program Statuses</h3>
              <p>cancellations may appear with one of these statuses:</p>
              <ul>
                <li><strong>Active</strong> – The program is currently running (default view).</li>
                <li><strong>Cancelled</strong> – The program has been fully cancelled.</li>
                <li><strong>Additions</strong> – New cancellations added after the session started (displayed as Active).</li>
              </ul>
              <p>💡 <strong>Tip:</strong> Use the Active filter to see all current cancellations.</p>

              <h3>5. Using the View Filter (Dropdown)</h3>
              <p>The app uses a dropdown filter to select which cancellations to display:</p>
              <ul>
                <li><strong>Show Class Cancellations</strong> – Displays only classes that have individual cancellations.</li>
                <li><strong>Show All Programs</strong> – Displays all scheduled programs, including Active, Cancelled, and Additions.</li>
              </ul>
              <p>💡 <strong>Tip:</strong> Choose the desired option from the dropdown to switch views. The data updates immediately.</p>

              <h3>6. Filtering Options (Desktop View)</h3>
              <ul>
                <li><strong>Program:</strong> Search by program name</li>
                <li><strong>Program ID:</strong> Search by unique ID</li>
                <li><strong>Day:</strong> Filter by weekday</li>
                <li><strong>Location:</strong> Filter by program location</li>
                <li><strong>Program Status:</strong> Filter by Active, Cancelled, or Additions</li>
              </ul>

              <h3>7. Favorites Feature (Star Pinning)</h3>
              <ul>
                <li><strong>Click the star (★/☆)</strong> in the leftmost column to pin a program to the top</li>
                <li><strong>Favorites persist</strong> – Your starred cancellations stay at the top even after closing and reopening the app</li>
                <li><strong>Per-device storage</strong> – Each device remembers its own favorites</li>
                <li><strong>Visual indicator</strong> – Filled star (★) = favorited, empty star (☆) = not favorited</li>
                <li><strong>Works everywhere</strong> – Both desktop and mobile views support favorites</li>
              </ul>

              <h3>8. Understanding the Data Columns</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f0f0f0' }}>
                    <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Column</th>
                    <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Star</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Click to pin program to top (persists across sessions)</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Day</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Day of the week</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program/class name</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program ID</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Unique identifier</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Date Range</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Start and end dates</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Time</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Scheduled time</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Location</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program venue</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class Room</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Specific room/facility</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Instructor</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Assigned instructor</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program Status</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Active / Cancelled / Additions</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class Cancellation</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Specific cancelled dates</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Additional Information</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Notes or details</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Refund</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Allowed (Yes/No, based on classes completed)</td></tr>
                </tbody>
              </table>

              <h3>9. Mobile View Features</h3>
              <ul>
                <li><strong>Card Layout:</strong> cancellations displayed as easy-to-read cards</li>
                <li><strong>Favorites Support:</strong> Star cancellations to pin them to the top</li>
                <li><strong>Class Cancellations Only:</strong> Mobile view focuses on cancelled classes</li>
                <li><strong>Touch-Friendly:</strong> Large buttons and easy navigation</li>
                <li><strong>Header Buttons:</strong> Desktop switch (🖥️), Refresh (🔄), and Save App (📲) buttons in header</li>
                <li><strong>Search Function:</strong> Search by program name or ID directly from mobile view</li>
                <li><strong>PWA Installation:</strong> Can be installed as a native app</li>
              </ul>

              <h3>10. Exporting Data (Desktop Only)</h3>
              <ul>
                <li><strong>Export to Excel</strong> – Download filtered results as an Excel file</li>
                <li><strong>Export to PDF</strong> – Download filtered results as a PDF file</li>
                <li>Both exports respect your current filters and include your favorites at the top</li>
              </ul>

              <h3>11. Refund Rules</h3>
              <ul>
                <li><strong>Yes</strong> – Refund allowed if fewer than 3 classes are completed</li>
                <li><strong>No</strong> – Refund not allowed if 3 or more classes are completed</li>
                <li>The calculation considers start date, current date, and cancellations.</li>
              </ul>

              <h3>12. Tips & Best Practices</h3>
              <ul>
                <li><strong>Use favorites</strong> to keep important cancellations at the top</li>
                <li><strong>Install on mobile</strong> for quick access to class cancellations</li>
                <li><strong>Automatic view switching</strong> - the app automatically chooses the best view for your device</li>
                <li><strong>Export data</strong> to share or print schedules</li>
                <li><strong>Refresh regularly</strong> to get the latest updates</li>
                <li>All times are shown in Kingston, Ontario timezone</li>
              </ul>

              <h3>13. Troubleshooting</h3>
              <ul>
                <li><strong>Data not loading:</strong> Try refreshing the page or using the Refresh button (🔄) in the header</li>
                <li><strong>Favorites disappeared:</strong> Check if you're on the same device/browser</li>
                <li><strong>Mobile view issues:</strong> Use the Desktop button (🖥️) in the mobile header to switch views</li>
                <li><strong>Installation problems:</strong> Use the Save App button (📲) and follow the instructions</li>
                <li><strong>Search not working:</strong> Make sure you're searching by program name or ID only</li>
              </ul>

              <h3>14. Support</h3>
              <p>For technical issues or questions, please contact your system administrator.</p>
            </div>
            <div className="modal-actions">
              <button 
                onClick={() => setShowUserGuide(false)} 
                style={{ background: "#0072ce", color: "white" }}
                className="custom-tooltip"
                data-tooltip="Close Help Guide"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}







      {/* Program Details Modal - Desktop */}
      {selectedProgram && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 9999999999,
          padding: '20px'
        }}
        onClick={() => {
          setSelectedProgram(null);
        }}
        >
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
            maxWidth: '90vw',
            maxHeight: '80vh',
            border: '3px solid #0072ce',
            textAlign: 'center',
            position: 'relative',
            overflow: 'auto'
          }}
          onClick={(e) => {
            e.stopPropagation();
          }}
          >
            <h3 style={{ marginBottom: '20px', color: '#0072ce' }}>{selectedProgram.program}</h3>
            
            
            {/* Always show Description section */}
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ color: '#333', marginBottom: '10px' }}>Description:</h4>
              <p style={{ fontSize: '1rem', lineHeight: '1.6', textAlign: 'left' }}>
                {selectedProgram.description && selectedProgram.description.trim() !== '' 
                  ? selectedProgram.description 
                  : 'No description available'}
              </p>
            </div>
            
            {/* Always show Fee section */}
            <div style={{ marginBottom: '30px' }}>
              <h4 style={{ color: '#333', marginBottom: '10px' }}>Fee:</h4>
              <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#0072ce' }}>
                {selectedProgram.fee && selectedProgram.fee.trim() !== '' 
                  ? selectedProgram.fee 
                  : 'No fee information available'}
              </p>
            </div>
            
            <button 
              onClick={(e) => {
                e.stopPropagation();
                setSelectedProgram(null);
              }}
              style={{
                background: '#0072ce',
                color: 'white',
                border: 'none',
                padding: '12px 30px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: 'bold'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Location Address Modal - Desktop */}
      {selectedLocation && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 9999999999,
          padding: '20px'
        }}
        onClick={() => {
          setSelectedLocation(null);
        }}
        >
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
            maxWidth: '90vw',
            maxHeight: '80vh',
            border: '3px solid #0072ce',
            textAlign: 'center',
            position: 'relative',
            overflow: 'auto'
          }}
          onClick={(e) => {
            e.stopPropagation();
          }}
          >
            <h3 style={{ marginBottom: '20px', color: '#0072ce' }}>{selectedLocation}</h3>
            <p style={{ fontSize: '1.1rem', marginBottom: '30px', lineHeight: '1.6' }}>
              {getFullAddress(selectedLocation)}
            </p>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                setSelectedLocation(null);
              }}
              style={{
                background: '#0072ce',
                color: 'white',
                border: 'none',
                padding: '12px 30px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: 'bold'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* QR Code Modal - Global for both mobile and desktop */}
      {showQRCode && (
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
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '20px',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            position: 'relative',
            border: '4px solid #0072ce',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)',
            textAlign: 'center'
          }}>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ margin: '0 0 10px 0', color: '#0072ce' }}>Scan with your phone to open the app</h2>
              <button 
                onClick={() => setShowQRCode(false)}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                ×
              </button>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              {qrCodeDataURL ? (
                <div style={{ position: 'relative', display: 'inline-block' }}>
                  <img 
                    src={qrCodeDataURL} 
                    alt="QR Code for app" 
                    style={{ 
                      width: '300px', 
                      height: '300px', 
                      border: '2px solid #ddd',
                      borderRadius: '8px'
                    }}
                  />
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: 'white',
                    padding: '8px',
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)'
                  }}>
                    <img 
                      src={logo} 
                      alt="Company Logo" 
                      style={{ width: '30px', height: '30px', objectFit: 'contain' }}
                    />
                  </div>
                </div>
              ) : (
                <div style={{ padding: '40px', color: '#666' }}>
                  <p>Generating QR code...</p>
                  <button 
                    onClick={generateQRCode}
                    style={{
                      background: '#0072ce',
                      color: 'white',
                      border: 'none',
                      padding: '10px 20px',
                      borderRadius: '6px',
                      cursor: 'pointer'
                    }}
                  >
                    Retry
                  </button>
                </div>
              )}
            </div>
            
            <div style={{ marginTop: '20px' }}>
              <button 
                onClick={() => setShowQRCode(false)} 
                style={{ 
                  background: '#0072ce', 
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Message Modal */}
      {showMessageModal && messageProgram && (
        <div 
          className="message-modal-overlay" 
          onClick={() => setShowMessageModal(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999999999,
            width: '100vw',
            height: '100vh',
            padding: '20px',
            boxSizing: 'border-box',
            overflow: 'hidden'
          }}
          onLoad={() => console.log('📱 Modal overlay loaded!')}
        >
          <div 
            className="message-modal-content" 
            onClick={e => e.stopPropagation()}
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '20px',
              width: '100%',
              maxWidth: '500px',
              maxHeight: '80vh',
              overflow: 'auto',
              position: 'relative',
              border: '3px solid #0072ce',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)',
              margin: '0'
            }}
          >
            <h3 style={{ color: '#0072ce', marginTop: 0 }}>Send Message</h3>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '10px', backgroundColor: '#e7f3ff', padding: '8px', borderRadius: '4px' }}>
              ✅ Modal is working! ✉️ (Mobile & Desktop) - {new Date().toLocaleTimeString()}
              <br/>
              📱 Mobile: {window.innerWidth < 768 ? 'YES' : 'NO'} | 📏 Width: {window.innerWidth}px
              <br/>
              🔧 Modal State: {showMessageModal ? 'OPEN' : 'CLOSED'}
              <br/>
              📱 Touch Device: {('ontouchstart' in window) ? 'YES' : 'NO'}
              <br/>
              🖱️ Click Type: {navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'}
            </div>
            <div style={{ marginBottom: '15px', fontSize: '14px', color: '#666' }}>
              <strong>Program:</strong> {messageProgram.program}<br/>
              <strong>ID:</strong> {messageProgram.program_id.split('.')[0]}<br/>
              <strong>Instructor:</strong> {messageProgram.instructor}
            </div>
            <textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Enter your message here..."
              rows={6}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                resize: 'vertical',
                marginBottom: '15px'
              }}
            />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <button
                onClick={() => {
                  console.log('🖱️ Cancel button clicked!');
                  setShowMessageModal(false);
                  setMessageText("");
                  setMessageProgram(null);
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
              >
                Cancel
              </button>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  console.log('🖱️ Send Message button clicked!');
                  console.log('📝 Message text:', messageText);
                  console.log('📋 Program:', messageProgram);
                  if (messageText.trim()) {
                    handleSendMessage(messageProgram, messageText);
                  } else {
                    alert('Please enter a message first!');
                  }
                }}
                disabled={!messageText.trim()}
                style={{
                  padding: '10px 20px',
                  backgroundColor: messageText.trim() ? '#0072ce' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: messageText.trim() ? 'pointer' : 'not-allowed',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
              >
                Send Message
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
