import React, { useEffect, useState } from "react";
import "./App.css";
import logo from "./logo.png";

type Cancellation = {
  sheet: string;
  program: string;
  program_id: string;
  date_range: string;
  time: string;
  location: string;
  class_room: string;  // New: Class Room from Facility
  instructor: string;  // New: Instructor
  program_status: string;
  class_cancellation: string;
  note: string;
  withdrawal: string;
  is_favorite?: boolean;  // New: Favorite status
};

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

function App() {
  console.log("API_URL:", API_URL);
  const [cancellations, setCancellations] = useState<Cancellation[]>([]);
  const [filters, setFilters] = useState({
    program: "",
    program_id: "",
    day: "",
    location: "",
    program_status: "",
    view_type: "cancellations", // New: "cancellations" or "all"
  });
  const [lastLoaded, setLastLoaded] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [locations, setLocations] = useState<string[]>([]);
  const [showUserGuide, setShowUserGuide] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  // Update date and time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchCancellations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      if (filters.view_type === "cancellations") params.append("has_cancellation", "true");
      
      const url = `${API_URL}/cancellations?${params.toString()}`;
      console.log("Fetching from:", url);
      
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      console.log("Received data:", data);
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
    const interval = setInterval(() => fetchCancellations(), 5 * 60 * 1000); // 5 min
    return () => clearInterval(interval);
    // eslint-disable-next-line
  }, [filters]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/refresh`, { method: "POST" });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      await fetchCancellations();
    } catch (error) {
      console.error("Error refreshing:", error);
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
      console.log('Current favorites:', Array.from(newFavorites));
      return newFavorites;
    });
  };

  // Sort cancellations with favorites at the top
  const sortedCancellations = [...cancellations].sort((a, b) => {
    const aIsFavorite = favorites.has(a.program_id);
    const bIsFavorite = favorites.has(b.program_id);
    
    if (aIsFavorite && !bIsFavorite) return -1;
    if (!aIsFavorite && bIsFavorite) return 1;
    return 0;
  });

  // Debug logging
  console.log('Favorites state:', Array.from(favorites));
  console.log('Sorted cancellations count:', sortedCancellations.length);

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

  return (
    <div className="App">
      <div className="sticky-header">
        <header className="app-header">
          <img src={logo} alt="Company Logo" className="app-logo" />
          <h1>Program Schedule Update</h1>
          <div className="datetime-display">
            {currentDateTime.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })} {currentDateTime.toLocaleTimeString('en-CA', { timeZone: 'America/Toronto' })}
          </div>
        </header>
        <div className="filters">
          <input
            name="program"
            placeholder="Program"
            value={filters.program}
            onChange={handleInputChange}
          />
          <input
            name="program_id"
            placeholder="Program ID"
            value={filters.program_id}
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
          <button onClick={handleRefresh} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
          <div style={{ marginLeft: "auto", display: "flex", gap: "10px" }}>
            <button 
              onClick={() => handleExport('excel')} 
              style={{ background: "#0072ce", color: "white" }}
              disabled={cancellations.length === 0}
            >
              📊 Export to Excel
            </button>
            <button 
              onClick={() => handleExport('pdf')} 
              style={{ background: "#0072ce", color: "white" }}
              disabled={cancellations.length === 0}
            >
              📄 Export to PDF
            </button>
            <button 
              onClick={() => setShowUserGuide(true)} 
              style={{ background: "#0072ce", color: "white" }}
            >
              📖 User Guide
            </button>
          </div>
        </div>
        <div className="last-loaded">
          Last updated: {lastLoaded ? new Date(lastLoaded).toLocaleString('en-CA', { timeZone: 'America/Toronto' }) : "Never"}
        </div>
      </div>
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
              <th>Withdrawal</th>
            </tr>
          </thead>
          <tbody>
            {sortedCancellations.length === 0 && (
              <tr>
                <td colSpan={13} style={{ textAlign: "center" }}>
                  No programs found.
                </td>
              </tr>
            )}
            {sortedCancellations.map((c, i) => {
              const isFavorite = favorites.has(c.program_id);
              return (
                <tr key={i} className={isFavorite ? 'favorite-row' : ''}>
                  <td>
                    <span 
                      className={`favorite-star ${isFavorite ? 'favorited' : ''}`}
                      onClick={() => toggleFavorite(c.program_id)}
                      title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      {isFavorite ? '★' : '☆'}
                    </span>
                  </td>
                  <td>{c.sheet}</td>
                  <td>{c.program}</td>
                  <td>{c.program_id}</td>
                  <td>{c.date_range}</td>
                  <td>{c.time}</td>
                  <td>{c.location}</td>
                  <td>{c.class_room}</td>
                  <td>{c.instructor}</td>
                  <td>{c.program_status}</td>
                  <td>{c.class_cancellation && c.class_cancellation !== '' ? 
                    c.class_cancellation.split(';').map((date, index) => {
                      const trimmedDate = date.trim();
                      if (trimmedDate) {
                        try {
                          const parsedDate = new Date(trimmedDate);
                          if (!isNaN(parsedDate.getTime())) {
                            return (
                              <div key={index}>
                                {parsedDate.toLocaleDateString('en-CA', { timeZone: 'America/Toronto' })}
                              </div>
                            );
                          }
                        } catch (e) {
                          // If parsing fails, show the original text
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
              
              <p><strong>Welcome!</strong> This guide will help you navigate the Program Schedule Update App efficiently, allowing you to view, filter, and manage program schedules and class cancellations.</p>

              <h3>1. Loading Data</h3>
              <ul>
                <li>When you open the app, please allow a few minutes for all program data to load completely.</li>
                <li>Data automatically refreshes every 5 minutes.</li>
              </ul>

              <h3>2. Searching for a Program</h3>
              <p>You can quickly find programs using any of the following search options:</p>
              <ul>
                <li><strong>Program Name</strong> – Search by the name of the program/class.</li>
                <li><strong>Program ID</strong> – Enter the unique identifier for a program.</li>
                <li><strong>Date and Location</strong> – Filter programs by a specific date and location.</li>
              </ul>

              <h3>3. Understanding Program Statuses</h3>
              <p>Programs in the schedule may have one of the following statuses:</p>
              <ul>
                <li><strong>Active</strong> – Program is currently running (most common).</li>
                <li><strong>Cancelled</strong> – Program has been fully cancelled.</li>
                <li><strong>Additions</strong> – Programs added after the session started (these also appear as Active).</li>
              </ul>
              <p><em>Tip: Selecting Active displays all programs currently on schedule.</em></p>

              <h3>4. Using Filters</h3>
              <h4>Click Filters</h4>
              <ul>
                <li><strong>Show Class Cancellations</strong> – Displays only classes with individual cancellations.</li>
                <li><strong>Show All Programs</strong> – Displays all programs, including those without cancellations.</li>
              </ul>

              <h4>Location Filter</h4>
              <ul>
                <li>Ensure the filter is set to Show All Programs (the button will display "Show Class Cancellations").</li>
                <li>Select your preferred location from the list to view programs only at that location.</li>
              </ul>

              <h4>Additional Filters</h4>
              <p>You can refine your view using multiple filter options:</p>
              <ul>
                <li><strong>Day:</strong> Filter by the day of the week (Monday, Tuesday, etc.).</li>
                <li><strong>Date:</strong> Filter by a specific date.</li>
                <li><strong>Program Status:</strong> Active, Cancelled, or Additions.</li>
              </ul>

              <h3>5. Viewing Data</h3>
              <p>The app displays the following program information:</p>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f0f0f0' }}>
                    <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Field</th>
                    <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Day</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Day of the week the class runs</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Name of the program/class</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program ID</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Unique identifier for the program</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Date Range</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program start and end dates</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Time</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class time</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Location</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Venue or facility</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class Room</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Specific room/facility</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Instructor</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Name of instructor</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program Status</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Active, Cancelled, or Additions</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class Cancellation</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Specific dates of individual cancellations</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Additional Information</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Extra notes about the program</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Withdrawal</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Indicates if withdrawal is allowed (Yes/No)</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>⭐</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Click to favorite/unfavorite programs</td></tr>
                </tbody>
              </table>

              <h3>6. Favorite System</h3>
              <ul>
                <li><strong>Star Column:</strong> Click the ⭐ in the rightmost column to favorite/unfavorite programs.</li>
                <li><strong>Pinned Favorites:</strong> Favorited programs automatically appear at the top of the list.</li>
                <li><strong>Visual Highlighting:</strong> Favorite rows have a green background and left border.</li>
                <li><strong>Persistent:</strong> Favorites are remembered during your session.</li>
              </ul>

              <h3>7. Withdrawal Logic</h3>
              <ul>
                <li><strong>Yes:</strong> Fewer than 3 classes completed; withdrawal allowed.</li>
                <li><strong>No:</strong> 3 or more classes completed; withdrawal not allowed.</li>
                <li><strong>Calculation:</strong> Considers class start date, current date, and any cancelled classes.</li>
              </ul>

              <h3>8. Refreshing Data</h3>
              <ul>
                <li>Click <strong>Refresh</strong> to manually update program data.</li>
                <li>Automatic updates occur every 5 minutes.</li>
              </ul>

              <h3>9. Exporting Data</h3>
              <ul>
                <li><strong>Excel Export:</strong> Downloads filtered data as an Excel file.</li>
                <li><strong>PDF Export:</strong> Downloads filtered data as a PDF file.</li>
                <li><em>Note: Exports only include currently displayed data, respecting all applied filters.</em></li>
              </ul>

              <h3>10. Tips for Using the App</h3>
              <ul>
                <li>Use filters to quickly narrow down the data you need.</li>
                <li>Export data to share or print relevant information.</li>
                <li>All times are displayed in Kingston, Ontario timezone.</li>
                <li>The app updates automatically whenever new data is uploaded.</li>
                <li>Use the favorite system to keep important programs at the top.</li>
              </ul>

              <h3>11. Support</h3>
              <p>For technical assistance or questions, contact your system administrator.</p>
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowUserGuide(false)} style={{ background: "#0072ce", color: "white" }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;