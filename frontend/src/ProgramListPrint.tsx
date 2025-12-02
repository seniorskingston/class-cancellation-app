import React, { useEffect, useState } from 'react';
import logo from './logo.png';

interface Program {
  sheet: string;
  program: string;
  program_id: string;
  date_range: string;
  time: string;
  location: string;
  class_room: string;
  instructor: string;
  program_status: string;
  description: string;
  fee: string;
}

interface ProgramListPrintProps {
  onBackToMain: () => void;
}

const API_URL = "https://class-cancellation-backend.onrender.com";

const ProgramListPrint: React.FC<ProgramListPrintProps> = ({ onBackToMain }) => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPrograms();
  }, []);

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/cancellations`);
      const data = await response.json();
      
      if (data.data && Array.isArray(data.data)) {
        setPrograms(data.data);
      } else {
        setError('No program data found');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load programs');
    } finally {
      setLoading(false);
    }
  };

  // Helper function to parse time string to comparable number (minutes from midnight)
  const parseTimeToMinutes = (timeStr: string): number => {
    if (!timeStr) return 9999; // Put empty times at the end
    
    const time = timeStr.trim().toUpperCase();
    
    // Try to match patterns like "9:00 AM", "1:00 PM", "9 AM", "13:00"
    const patterns = [
      /(\d{1,2}):(\d{2})\s*(AM|PM)?/,
      /(\d{1,2})\s*(AM|PM)/,
      /(\d{1,2}):(\d{2})/
    ];
    
    for (const pattern of patterns) {
      const match = time.match(pattern);
      if (match) {
        let hour = parseInt(match[1]);
        const minute = match[2] ? parseInt(match[2]) : 0;
        const period = match[3] || '';
        
        // Convert to 24-hour format
        if (period === 'PM' && hour !== 12) {
          hour += 12;
        } else if (period === 'AM' && hour === 12) {
          hour = 0;
        }
        
        return hour * 60 + minute;
      }
    }
    
    return 9999; // Default to end if can't parse
  };

  // Group programs by day and sort alphabetically, then by time
  const groupProgramsByDay = (programs: Program[]) => {
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const grouped: { [key: string]: Program[] } = {};

    programs.forEach(program => {
      const day = program.sheet || 'Unknown';
      if (!grouped[day]) {
        grouped[day] = [];
      }
      grouped[day].push(program);
    });

    // Sort programs within each day: first alphabetically by name, then by time
    Object.keys(grouped).forEach(day => {
      grouped[day].sort((a, b) => {
        // First sort by program name alphabetically
        const nameA = (a.program || '').toLowerCase();
        const nameB = (b.program || '').toLowerCase();
        const nameCompare = nameA.localeCompare(nameB);
        
        if (nameCompare !== 0) {
          return nameCompare;
        }
        
        // If same name, sort by time (morning to night)
        const timeA = parseTimeToMinutes(a.time || '');
        const timeB = parseTimeToMinutes(b.time || '');
        return timeA - timeB;
      });
    });

    // Sort days according to dayOrder
    const sortedDays = dayOrder.filter(day => grouped[day]);
    const otherDays = Object.keys(grouped).filter(day => !dayOrder.includes(day));
    const allDays = [...sortedDays, ...otherDays];

    return { grouped, allDays };
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>Loading programs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <button onClick={onBackToMain} style={{ marginTop: '20px', padding: '10px 20px' }}>
          Back to Main
        </button>
      </div>
    );
  }

  const { grouped, allDays } = groupProgramsByDay(programs);

  return (
    <div className="page-number" style={{ fontFamily: 'Arial, sans-serif', maxWidth: '8.5in', margin: '0 auto', padding: '20px' }}>
      <style>{`
        @page {
          size: letter;
          margin: 0.75in;
        }
        
        @page:first {
          margin: 0;
        }
        
        @media print {
          * {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          
          body {
            margin: 0;
            padding: 0;
          }
          .no-print {
            display: none !important;
          }
          .page-break {
            page-break-before: always;
          }
          .program-day-section {
            page-break-inside: avoid;
          }
          .program-card {
            page-break-inside: avoid;
            break-inside: avoid;
          }
          
          /* Cover page styling */
          .cover-page {
            margin: 0 !important;
            padding: 60px 40px !important;
            page-break-after: always;
          }
          
          /* Cover page forces page break, so header will be on page 2 */
          .cover-page {
            page-break-after: always;
          }
          
          /* Page number using CSS counter - skip first page */
          body {
            counter-reset: page;
          }
          
          .page-number::after {
            counter-increment: page;
            content: "Page " counter(page);
            position: fixed;
            bottom: 0.5in;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 10px;
            color: #666;
            font-family: Arial, sans-serif;
          }
          
          /* Don't show page number on cover page */
          .cover-page::after {
            content: none !important;
          }
        }
      `}</style>

      {/* Header with buttons - hidden when printing */}
      <div className="no-print" style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button
          onClick={onBackToMain}
          style={{
            background: '#6c757d',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ← Back to Main
        </button>
        <button
          onClick={handlePrint}
          style={{
            background: '#4caf50',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          🖨️ Print Program List
        </button>
        <button
          onClick={fetchPrograms}
          style={{
            background: '#2196f3',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          🔄 Refresh
        </button>
        <span style={{ marginLeft: '20px', color: '#666' }}>
          Total Programs: {programs.length}
        </span>
      </div>

      {/* Cover Page - First Page Only */}
      <div className="cover-page" style={{
        minHeight: '11in',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)',
        margin: '-20px -20px 40px -20px',
        padding: '60px 40px',
        pageBreakAfter: 'always',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Decorative elements */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '120px',
          background: '#8bc34a',
          zIndex: 1
        }}></div>
        
        {/* Content */}
        <div style={{
          position: 'relative',
          zIndex: 2,
          textAlign: 'center',
          color: 'white',
          width: '100%',
          maxWidth: '7in'
        }}>
          {/* Top text */}
          <div style={{
            fontSize: '18px',
            fontWeight: 'bold',
            letterSpacing: '2px',
            marginBottom: '20px',
            textTransform: 'uppercase'
          }}>
            SENIORS ASSOCIATION
          </div>
          
          {/* Main title with overlapping effect */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '30px',
            flexWrap: 'wrap'
          }}>
            <h1 style={{
              fontSize: '72px',
              fontWeight: 'bold',
              margin: 0,
              color: 'white',
              textShadow: '2px 2px 4px rgba(0,0,0,0.2)',
              lineHeight: '1'
            }}>
              PROGRAM
            </h1>
            <div style={{
              position: 'relative',
              background: '#8bc34a',
              padding: '0 30px',
              borderRadius: '8px',
              transform: 'rotate(-2deg)',
              boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
            }}>
              <h1 style={{
                fontSize: '72px',
                fontWeight: 'bold',
                margin: 0,
                color: '#1565c0',
                lineHeight: '1'
              }}>
                GUIDE
              </h1>
            </div>
          </div>
          
          {/* Subtitle on green stripe */}
          <div style={{
            background: '#8bc34a',
            padding: '15px 40px',
            borderRadius: '8px',
            display: 'inline-block',
            marginTop: '20px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
          }}>
            <h2 style={{
              fontSize: '32px',
              fontWeight: 'bold',
              margin: 0,
              color: 'white',
              textTransform: 'uppercase',
              letterSpacing: '1px'
            }}>
              WINTER 2025
            </h2>
          </div>
        </div>
      </div>

      {/* Document Header - For subsequent pages */}
      <div className="page-header" style={{
        display: 'flex', // Show on screen, will be on page 2 when printing
        alignItems: 'center',
        justifyContent: 'center',
        gap: '20px',
        marginBottom: '20px',
        borderBottom: '3px solid #2e7d32',
        paddingBottom: '15px'
      }}>
        <img 
          src={logo} 
          alt="Company Logo" 
          style={{ 
            height: '60px', 
            width: 'auto',
            objectFit: 'contain'
          }} 
        />
        <div style={{ textAlign: 'center', flex: 1 }}>
          <h1 style={{ color: '#2e7d32', margin: 0, fontSize: '28px', fontWeight: 'bold' }}>
            Program Guide Winter 2025, Session 2
          </h1>
          <p style={{ color: '#666', margin: '8px 0 0 0', fontSize: '16px', fontWeight: '500' }}>
            December, 2025
          </p>
        </div>
        <div style={{ width: '60px' }}></div> {/* Spacer for centering */}
      </div>

      {/* Programs by Day */}
      {allDays.map((day, dayIndex) => {
        const dayPrograms = grouped[day];
        if (!dayPrograms || dayPrograms.length === 0) return null;

        return (
          <div
            key={day}
            className="program-day-section"
            style={{
              marginBottom: '30px'
            }}
          >
            {/* Day Header */}
            <div style={{
              background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
              color: 'white',
              padding: '12px 20px',
              borderRadius: '8px 8px 0 0',
              fontSize: '20px',
              fontWeight: 'bold',
              marginBottom: 0
            }}>
              {day}
            </div>

            {/* Programs for this day */}
            {dayPrograms.map((program, programIndex) => (
              <div
                key={`${program.program_id}-${programIndex}`}
                className="program-card"
                style={{
                  background: 'white',
                  border: '1px solid #ddd',
                  borderTop: 'none',
                  padding: '15px 20px',
                  marginBottom: 0
                }}
              >
                {/* Program Title */}
                <div style={{
                  fontSize: '18px',
                  fontWeight: 'bold',
                  color: '#2e7d32',
                  marginBottom: '12px',
                  borderBottom: '2px solid #e8f5e9',
                  paddingBottom: '8px'
                }}>
                  {program.program || 'N/A'}
                </div>

                {/* Program Details Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  marginBottom: '15px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Program ID:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.program_id || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Date Range:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.date_range || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Time:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.time || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Location:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.location || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Class Room:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.class_room || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Instructor:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.instructor || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Fee:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.fee || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '120px', fontSize: '13px' }}>
                      Program Status:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '13px' }}>
                      {program.program_status || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Program Description */}
                {program.description && (
                  <div style={{
                    background: '#f9f9f9',
                    borderLeft: '4px solid #4caf50',
                    padding: '12px',
                    marginTop: '15px',
                    borderRadius: '4px'
                  }}>
                    <div style={{
                      fontWeight: 'bold',
                      color: '#2e7d32',
                      marginBottom: '8px',
                      fontSize: '14px'
                    }}>
                      Description:
                    </div>
                    <div style={{
                      color: '#555',
                      lineHeight: '1.6',
                      fontSize: '13px'
                    }}>
                      {program.description}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      })}

      {/* Footer - only on last page */}
      <div style={{
        textAlign: 'center',
        marginTop: '30px',
        paddingTop: '20px',
        borderTop: '2px solid #ddd',
        color: '#666',
        fontSize: '12px',
        pageBreakInside: 'avoid'
      }}>
        <p>For more information, visit our website or contact the Seniors Association Kingston</p>
        <p>This document was generated automatically from the program database</p>
      </div>

    </div>
  );
};

export default ProgramListPrint;

