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
  program_status: string;
  class_cancellation: string;
  note: string;
  classes_finished: number;
  withdrawal: string;
};

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api"; // Use environment variable for deployment

function App() {
  const [cancellations, setCancellations] = useState<Cancellation[]>([]);
  const [filters, setFilters] = useState({
    program: "",
    program_id: "",
    day: "",
    date: "",
    program_status: "",
  });
  const [lastLoaded, setLastLoaded] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [showingCancellationsOnly, setShowingCancellationsOnly] = useState(true);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());

  // Update date and time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchCancellations = async (hasCancellation = true) => {
    setLoading(true);
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
    if (hasCancellation) params.append("has_cancellation", "true");
    const res = await fetch(`${API_URL}/cancellations?${params.toString()}`);
    const data = await res.json();
    setCancellations(data.data);
    setLastLoaded(data.last_loaded);
    setLoading(false);
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
    await fetch(`${API_URL}/refresh`, { method: "POST" });
    await fetchCancellations(showingCancellationsOnly);
    setLoading(false);
  };

  const handleShowAll = () => {
    setShowingCancellationsOnly(false);
  };

  const handleShowCancellations = () => {
    setShowingCancellationsOnly(true);
  };

  return (
    <div className="App">
      <header className="app-header">
        <img src={logo} alt="Company Logo" className="app-logo" />
        <h1>Program Schedule Update</h1>
        <div className="datetime-display">
          {currentDateTime.toLocaleDateString()} {currentDateTime.toLocaleTimeString()}
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
            Show Only Cancellations
          </button>
        )}
      </div>
      <div className="last-loaded">
        Last updated: {lastLoaded ? new Date(lastLoaded).toLocaleString() : "Never"}
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
              <th>Program Status</th>
              <th>Class Cancellation</th>
              <th>Note</th>
              <th>Classes Finished</th>
              <th>Withdrawal</th>
            </tr>
          </thead>
          <tbody>
            {cancellations.length === 0 && (
              <tr>
                <td colSpan={11} style={{ textAlign: "center" }}>
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
                <td>{c.program_status}</td>
                <td>{c.class_cancellation}</td>
                <td>{c.note}</td>
                <td>{c.program_status === "Cancelled" ? "" : c.classes_finished}</td>
                <td>{c.program_status === "Cancelled" ? "" : c.withdrawal}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
