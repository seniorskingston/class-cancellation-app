import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
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
  const [qrCodeDataURL, setQrCodeDataURL] = useState<string>('');

  useEffect(() => {
    fetchPrograms();
    generateQRCode();
  }, []);

  const generateQRCode = async () => {
    try {
      const appURL = 'https://class-cancellation-frontend.onrender.com/';
      const qrSize = 200;
      
      // Generate QR code as data URL first
      const qrDataURL = await QRCode.toDataURL(appURL, {
        width: qrSize,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      });
      
      // Create a new canvas to combine QR code and logo
      const combinedCanvas = document.createElement('canvas');
      const ctx = combinedCanvas.getContext('2d');
      if (!ctx) {
        throw new Error('Could not get canvas context');
      }
      
      // Set canvas size
      combinedCanvas.width = qrSize;
      combinedCanvas.height = qrSize;
      
      // Load QR code as image
      const qrImg = new Image();
      await new Promise((resolve, reject) => {
        qrImg.onload = resolve;
        qrImg.onerror = reject;
        qrImg.src = qrDataURL;
      });
      
      // Draw QR code on canvas
      ctx.drawImage(qrImg, 0, 0, qrSize, qrSize);
      
      // Load and draw logo in center
      const logoImg = new Image();
      
      await new Promise((resolve, reject) => {
        logoImg.onload = () => {
          try {
            // Calculate logo size (about 30% of QR code size)
            const logoSize = qrSize * 0.3;
            const logoX = (qrSize - logoSize) / 2;
            const logoY = (qrSize - logoSize) / 2;
            
            // Draw white background square for logo (with padding)
            const padding = 5;
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(logoX - padding, logoY - padding, logoSize + (padding * 2), logoSize + (padding * 2));
            
            // Draw logo
            ctx.drawImage(logoImg, logoX, logoY, logoSize, logoSize);
            
            // Convert to data URL
            const finalDataURL = combinedCanvas.toDataURL('image/png');
            setQrCodeDataURL(finalDataURL);
            resolve(null);
          } catch (err) {
            reject(err);
          }
        };
        logoImg.onerror = reject;
        logoImg.src = logo;
      });
    } catch (err) {
      console.error('Error generating QR code with logo:', err);
      // Fallback: generate QR code without logo
      try {
        const appURL = 'https://class-cancellation-frontend.onrender.com/';
        const qrDataURL = await QRCode.toDataURL(appURL, {
          width: 150,
          margin: 1,
          color: {
            dark: '#000000',
            light: '#FFFFFF'
          }
        });
        setQrCodeDataURL(qrDataURL);
      } catch (fallbackErr) {
        console.error('Fallback QR code generation failed:', fallbackErr);
      }
    }
  };

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/api/cancellations`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('ProgramListPrint - Received data:', data);
      
      // Handle both response formats: {data: [...]} or direct array
      let programsList = [];
      if (Array.isArray(data)) {
        programsList = data;
      } else if (data.data && Array.isArray(data.data)) {
        programsList = data.data;
      } else {
        console.error('Unexpected data format:', data);
        setError('No program data found in response');
        return;
      }
      
      console.log(`ProgramListPrint - Loaded ${programsList.length} programs`);
      setPrograms(programsList);
      
      if (programsList.length === 0) {
        setError('No programs found. Please make sure programs are uploaded in the Admin Panel.');
      }
    } catch (err) {
      console.error('Error fetching programs:', err);
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
        <p style={{ color: 'red', fontSize: '18px', marginBottom: '10px' }}>❌ Error: {error}</p>
        <p style={{ color: '#666', fontSize: '14px', marginBottom: '20px' }}>
          Please make sure:
          <br />1. Programs are uploaded in the Admin Panel
          <br />2. The backend API is running
          <br />3. Check browser console for more details
        </p>
        <button 
          onClick={fetchPrograms} 
          style={{ 
            marginRight: '10px',
            marginTop: '20px', 
            padding: '10px 20px',
            background: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          🔄 Try Again
        </button>
        <button 
          onClick={onBackToMain} 
          style={{ 
            marginTop: '20px', 
            padding: '10px 20px',
            background: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          ← Back to Main
        </button>
      </div>
    );
  }
  
  if (programs.length === 0 && !loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: '#ff9800', fontSize: '18px', marginBottom: '10px' }}>⚠️ No Programs Found</p>
        <p style={{ color: '#666', fontSize: '14px', marginBottom: '20px' }}>
          No programs are available. Please upload programs in the Admin Panel first.
        </p>
        <button 
          onClick={fetchPrograms} 
          style={{ 
            marginRight: '10px',
            marginTop: '20px', 
            padding: '10px 20px',
            background: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          🔄 Refresh
        </button>
        <button 
          onClick={onBackToMain} 
          style={{ 
            marginTop: '20px', 
            padding: '10px 20px',
            background: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          ← Back to Main
        </button>
      </div>
    );
  }

  const { grouped, allDays } = groupProgramsByDay(programs);

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', maxWidth: '8.5in', width: '8.5in', margin: '0 auto', padding: '20px', position: 'relative' }} className="print-container">
      <style>{`
        /* Screen view - center the container */
        .print-container {
          margin: 0 auto !important;
        }
        
        @page {
          size: letter portrait;
          margin: 10mm 5mm 8mm 20mm; /* top right bottom left */
          @bottom-right {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 9px;
            color: #666;
            font-family: Arial, sans-serif;
          }
        }
        
        @page:first {
          size: letter portrait;
          margin: 0 !important;
          padding: 0 !important;
          @bottom-right {
            content: "";
          }
        }
        
        @media print {
          * {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          
          html, body {
            margin: 0 !important;
            padding: 0 !important;
            width: 8.5in !important;
            height: auto !important;
            overflow: visible !important;
          }
          
          /* Main container - no margins in print to prevent white bars */
          body > div,
          .print-container {
            margin: 0 !important;
            padding: 0 !important;
            width: 8.5in !important;
            max-width: 8.5in !important;
            min-width: 8.5in !important;
          }
          
          /* Content wrapper - ensure it shows after cover page */
          .content-wrapper {
            display: block !important;
            padding: 20px !important;
            visibility: visible !important;
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
          
          /* Cover page styling - full letter size, no margins, no white space */
          .cover-page {
            margin: 0 !important;
            padding: 0 !important;
            height: 11in !important;
            width: 8.5in !important;
            min-width: 8.5in !important;
            max-width: 8.5in !important;
            min-height: 11in !important;
            max-height: 11in !important;
            page-break-after: always;
            box-sizing: border-box !important;
            position: relative !important;
            overflow: hidden !important;
            left: 0 !important;
            right: 0 !important;
            top: 0 !important;
            transform: none !important;
            border: none !important;
            outline: none !important;
          }
          
          /* Ensure cover page background extends to all edges */
          .cover-page::before,
          .cover-page::after {
            display: none !important;
          }
          
          /* Content wrapper after cover page - ensure it's visible */
          .content-wrapper {
            display: block !important;
            padding: 20px !important;
          }
          
          /* Content inside cover page - positioned within safe area for binding */
          .cover-page > div:first-of-type {
            position: absolute !important;
            top: 10mm !important;
            left: 20mm !important;
            right: 5mm !important;
            bottom: 8mm !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
          }
          
          /* Hide page header completely - no duplicate cover page */
          .page-header {
            display: none !important;
          }
          
          /* Remove all page numbers completely */
          .page-number-footer,
          .page-number::after,
          .page-number-footer::before,
          .page-number-footer::after {
            display: none !important;
            content: none !important;
          }
          
          /* Remove any page numbers from other elements */
          .program-card::after,
          .program-day-section::after,
          .day-header::after,
          .page-header::after {
            display: none !important;
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
        height: '11in',
        width: '8.5in',
        minWidth: '8.5in',
        maxWidth: '8.5in',
        minHeight: '11in',
        maxHeight: '11in',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)',
        margin: '0',
        padding: '0',
        position: 'relative',
        overflow: 'hidden',
        boxSizing: 'border-box',
        left: '0',
        right: '0',
        top: '0'
      }}>
        {/* Content - positioned within safe area (20mm left, 5mm right, 10mm top, 8mm bottom) */}
        <div style={{
          position: 'absolute',
          top: '10mm',
          left: '20mm',
          right: '5mm',
          bottom: '8mm',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          color: 'white',
          zIndex: 2
        }}>
          {/* Top text */}
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            letterSpacing: '1.5px',
            marginBottom: '25px',
            textTransform: 'uppercase'
          }}>
            SENIORS ASSOCIATION
          </div>
          
          {/* Main title with overlapping effect */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '30px',
            flexWrap: 'wrap'
          }}>
            <h1 style={{
              fontSize: '56px',
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
              padding: '0 20px',
              borderRadius: '6px',
              transform: 'rotate(-2deg)',
              boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
            }}>
              <h1 style={{
                fontSize: '56px',
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
            padding: '10px 30px',
            borderRadius: '6px',
            display: 'inline-block',
            marginTop: '15px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
          }}>
            <h2 style={{
              fontSize: '24px',
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

      {/* Content wrapper for pages after cover - with padding */}
      <div className="content-wrapper" style={{ padding: '20px' }}>
        {/* Page number footer - appears at bottom of each page (except cover) */}
        <div className="page-number-footer" style={{ display: 'none' }}>
          {/* Page number will be inserted by CSS counter */}
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
              marginBottom: '20px'
            }}
          >
            {/* Day Header */}
            <div style={{
              background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
              color: 'white',
              padding: '8px 15px',
              borderRadius: '6px 6px 0 0',
              fontSize: '18px',
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
                  padding: '12px 15px',
                  marginBottom: 0
                }}
              >
                {/* Program Title */}
                <div style={{
                  fontSize: '16px',
                  fontWeight: 'bold',
                  color: '#2e7d32',
                  marginBottom: '10px',
                  borderBottom: '2px solid #e8f5e9',
                  paddingBottom: '6px'
                }}>
                  {program.program || 'N/A'}
                </div>

                {/* Program Details Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '8px',
                  marginBottom: '10px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Program ID:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.program_id || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Date Range:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.date_range || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Time:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.time || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Location:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.location || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Class Room:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.class_room || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Instructor:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.instructor || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Fee:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.fee || 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 'bold', color: '#555', minWidth: '100px', fontSize: '11px' }}>
                      Program Status:
                    </span>
                    <span style={{ color: '#333', flex: 1, fontSize: '11px' }}>
                      {program.program_status || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Program Description */}
                {program.description && (
                  <div style={{
                    background: '#f9f9f9',
                    borderLeft: '3px solid #4caf50',
                    padding: '10px',
                    marginTop: '10px',
                    borderRadius: '4px'
                  }}>
                    <div style={{
                      fontWeight: 'bold',
                      color: '#2e7d32',
                      marginBottom: '6px',
                      fontSize: '12px'
                    }}>
                      Description:
                    </div>
                    <div style={{
                      color: '#555',
                      lineHeight: '1.5',
                      fontSize: '11px'
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
        marginTop: '20px',
        paddingTop: '15px',
        borderTop: '2px solid #ddd',
        color: '#666',
        fontSize: '10px',
        pageBreakInside: 'avoid'
      }}>
        <p style={{ marginBottom: '10px' }}>
          For more information, visit the Seniors Kingston website or the Program/Event App{' '}
          <a 
            href="https://class-cancellation-frontend.onrender.com/" 
            style={{ color: '#2e7d32', textDecoration: 'none' }}
          >
            https://class-cancellation-frontend.onrender.com/
          </a>
          {' '}or scan
        </p>
        {qrCodeDataURL ? (
          <div style={{ marginTop: '10px', marginBottom: '10px', textAlign: 'center' }}>
            <img 
              src={qrCodeDataURL} 
              alt="App QR Code" 
              style={{ 
                width: '120px', 
                height: '120px',
                border: '2px solid #ddd',
                borderRadius: '4px',
                padding: '5px',
                background: 'white',
                display: 'inline-block'
              }} 
            />
          </div>
        ) : (
          <div style={{ marginTop: '10px', marginBottom: '10px', textAlign: 'center', color: '#999', fontSize: '9px' }}>
            Loading QR code...
          </div>
        )}
        </div>
      </div>

    </div>
  );
};

export default ProgramListPrint;

