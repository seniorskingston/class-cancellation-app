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
              
              <p><strong>Welcome!</strong> This guide will help you use the Program Schedule Update App to quickly search, filter, and manage program schedules and cancellations.</p>

              <h3>1. Loading Data</h3>
              <ul>
                <li>When you open the app, please allow a few minutes for the data to load.</li>
                <li>If you previously left the app open, refresh the page to ensure the data is up to date.</li>
              </ul>

              <h3>2. Searching for a Program</h3>
              <p>You can search for a program using:</p>
              <ul>
                <li><strong>Program Name</strong></li>
                <li><strong>Program ID</strong></li>
                <li><strong>Day & Location</strong></li>
              </ul>

              <h3>3. Understanding Program Statuses</h3>
              <p>Programs may appear with one of these statuses:</p>
              <ul>
                <li><strong>Active</strong> – The program is currently running (default view).</li>
                <li><strong>Cancelled</strong> – The program has been fully cancelled.</li>
                <li><strong>Additions</strong> – New programs added after the session started (displayed as Active).</li>
              </ul>
              <p>💡 <strong>Tip:</strong> Use the Active filter to see all current programs.</p>

              <h3>4. Using the View Filter (Dropdown)</h3>
              <p>The app now uses a dropdown filter to select which programs to display:</p>
              <ul>
                <li><strong>Show All Programs</strong> – Displays all scheduled programs, including Active, Cancelled, and Additions.</li>
                <li><strong>Show Class Cancellations</strong> – Displays only classes that have individual cancellations.</li>
              </ul>
              <p>💡 <strong>Tip:</strong> Choose the desired option from the dropdown to switch views. The data updates immediately.</p>

              <h3>5. Filtering by Location</h3>
              <ul>
                <li>To filter programs by location, make sure the View Filter is set to Show All Programs.</li>
                <li>Then select your preferred location from the location filter list.</li>
              </ul>

              <h3>6. Main Features</h3>
              <h4>Viewing Data</h4>
              <ul>
                <li>By default, the app opens in Show Class Cancellations mode.</li>
                <li>Switch to Show All Programs to see the full schedule.</li>
              </ul>

              <h4>Filtering Options</h4>
              <ul>
                <li><strong>Program:</strong> Search by program name</li>
                <li><strong>Program ID:</strong> Search by unique ID</li>
                <li><strong>Day:</strong> Filter by weekday</li>
                <li><strong>Location:</strong> Filter by program location</li>
                <li><strong>Program Status:</strong> Filter by Active, Cancelled, or Additions</li>
              </ul>

              <h4>Refreshing Data</h4>
              <ul>
                <li>Data refreshes automatically every 5 minutes.</li>
                <li>To update manually, click Refresh in the app.</li>
                <li>You can also refresh your browser (circle arrow at the top).</li>
              </ul>

              <h4>Exporting Data</h4>
              <ul>
                <li><strong>Export to Excel</strong> – Download filtered results as an Excel file</li>
                <li><strong>Export to PDF</strong> – Download filtered results as a PDF file</li>
                <li>Both exports respect your current filters.</li>
              </ul>

              <h3>7. Understanding the Data Columns</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f0f0f0' }}>
                    <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Column</th>
                    <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
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
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Withdrawal</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Allowed (Yes/No, based on classes completed)</td></tr>
                  <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Star</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Click the star to "pin" a program at the top of your list</td></tr>
                </tbody>
              </table>

              <h3>8. Withdrawal Rules</h3>
              <ul>
                <li><strong>Yes</strong> – Withdrawal allowed if fewer than 3 classes are completed</li>
                <li><strong>No</strong> – Withdrawal not allowed if 3 or more classes are completed</li>
                <li>The calculation considers start date, current date, and cancellations.</li>
              </ul>

              <h3>9. Tips</h3>
              <ul>
                <li>Use filters to quickly find the programs you need.</li>
                <li>Export data to share or print schedules.</li>
                <li>The app auto-updates when new data is uploaded.</li>
                <li>All times are shown in Kingston, Ontario timezone.</li>
              </ul>

              <h3>10. Support</h3>
              <p>For technical issues or questions, please contact your system administrator.</p>
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