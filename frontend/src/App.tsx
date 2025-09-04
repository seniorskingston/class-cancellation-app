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
};

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

function App() {
  const [cancellations, setCancellations] = useState<Cancellation[]>([]);
  const [filters, setFilters] = useState({
    program: "",
    program_id: "",
    day: "",
    date: "",
    location: "",
    program_status: "",
  });
  const [lastLoaded, setLastLoaded] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [showingCancellationsOnly, setShowingCancellationsOnly] = useState(true);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [locations, setLocations] = useState<string[]>([]);
  const [showUserGuide, setShowUserGuide] = useState(false);

  // Update date and time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchCancellations = async (hasCancellation = true) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      if (hasCancellation) params.append("has_cancellation", "true");
      
      const res = await fetch(`${API_URL}/cancellations?${params.toString()}`);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
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
    fetchCancellations(showingCancellationsOnly);
    const interval = setInterval(() => fetchCancellations(showingCancellationsOnly), 5 * 60 * 1000); // 5 min
    return () => clearInterval(interval);
    // eslint-disable-next-line
  }, [filters, showingCancellationsOnly]);

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
      await fetchCancellations(showingCancellationsOnly);
    } catch (error) {
      console.error("Error refreshing:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleShowAll = () => {
    setShowingCancellationsOnly(false);
  };

  const handleShowCancellations = () => {
    setShowingCancellationsOnly(true);
  };

  const handleExport = async (format: 'excel' | 'pdf') => {
    try {
      setLoading(true);
      
      // Build query parameters based on current filters
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      if (showingCancellationsOnly) params.append("has_cancellation", "true");
      
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
        <input
          name="date"
          type="date"
          value={filters.date}
          onChange={handleInputChange}
        />
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
        <button onClick={handleRefresh} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
        {showingCancellationsOnly ? (
          <button onClick={handleShowAll} style={{ background: "#00b388" }}>
            Show All Programs
          </button>
        ) : (
          <button onClick={handleShowCancellations} style={{ background: "#0072ce" }}>
            Show Class Cancellations
          </button>
        )}
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
      <div className="table-container">
        <table>
          <thead>
            <tr>
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
            {cancellations.length === 0 && (
              <tr>
                <td colSpan={12} style={{ textAlign: "center" }}>
                  No programs found.
                </td>
              </tr>
            )}
            {cancellations.map((c, i) => (
              <tr key={i}>
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
            ))}
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
              <h2>USER GUIDE</h2>
              
              <h3>OVERVIEW</h3>
              <p>This app helps you view and manage class cancellations and program schedules. You can filter, search, and export data as needed.</p>

              <h3>MAIN FEATURES</h3>

              <h4>1. VIEWING DATA</h4>
              <ul>
                <li>The app shows all programs by default</li>
                <li>Click "Show Class Cancellations" to see only classes with individual cancellations</li>
                <li>Click "Show All Programs" to see all programs again</li>
              </ul>

              <h4>2. FILTERING</h4>
              <ul>
                <li><strong>Program:</strong> Search by program name</li>
                <li><strong>Program ID:</strong> Search by specific program ID</li>
                <li><strong>Day:</strong> Filter by day of the week (Monday, Tuesday, etc.)</li>
                <li><strong>Date:</strong> Filter by specific date</li>
                <li><strong>Location:</strong> Filter by location</li>
                <li><strong>Program Status:</strong> Filter by status (Active, Cancelled, Additions)</li>
              </ul>

              <h4>3. REFRESHING DATA</h4>
              <ul>
                <li>Click "Refresh" to update the data from the database</li>
                <li>Data automatically refreshes every 5 minutes</li>
              </ul>

              <h4>4. EXPORTING DATA</h4>
              <ul>
                <li><strong>Export to Excel:</strong> Download filtered data as Excel file</li>
                <li><strong>Export to PDF:</strong> Download filtered data as PDF file</li>
                <li>Both exports include only the data currently displayed (respects filters)</li>
              </ul>

              <h4>5. UNDERSTANDING THE DATA</h4>
              <ul>
                <li><strong>Day:</strong> Day of the week the class runs</li>
                <li><strong>Program:</strong> Name of the program/class</li>
                <li><strong>Program ID:</strong> Unique identifier for the program</li>
                <li><strong>Date Range:</strong> When the program runs (start and end dates)</li>
                <li><strong>Time:</strong> Class time</li>
                <li><strong>Location:</strong> Where the class is held</li>
                <li><strong>Class Room:</strong> Specific room/facility</li>
                <li><strong>Instructor:</strong> Who teaches the class</li>
                <li><strong>Program Status:</strong> Active, Cancelled, or Additions</li>
                <li><strong>Class Cancellation:</strong> Specific dates when individual classes are cancelled</li>
                <li><strong>Additional Information:</strong> Extra notes about the program</li>
                <li><strong>Withdrawal:</strong> Whether withdrawal is allowed (Yes/No based on classes completed)</li>
              </ul>

              <h4>6. WITHDRAWAL LOGIC</h4>
              <ul>
                <li><strong>"Yes":</strong> Less than 3 classes have been completed, withdrawal is allowed</li>
                <li><strong>"No":</strong> 3 or more classes have been completed, withdrawal is not allowed</li>
                <li>Calculation considers class start date, current date, and any cancelled classes</li>
              </ul>

              <h3>TIPS</h3>
              <ul>
                <li>Use filters to narrow down the data you need</li>
                <li>Export data when you need to share or print information</li>
                <li>The app automatically updates when new data is uploaded</li>
                <li>All times are displayed in Kingston, Ontario timezone</li>
              </ul>

              <p><em>For technical support or questions, contact your system administrator.</em></p>
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
