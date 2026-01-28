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
  session?: string;
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
        errorCorrectionLevel: 'H', // High error correction to allow logo overlay
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
            // Calculate logo size (about 20% of QR code size - smaller for better scanning)
            const logoSize = qrSize * 0.2;
            const logoX = (qrSize - logoSize) / 2;
            const logoY = (qrSize - logoSize) / 2;
            
            // Draw white background square for logo (with padding)
            const padding = 4;
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
        logoImg.onerror = (err) => {
          console.error('Logo load error:', err);
          // If logo fails to load, use QR code without logo
          setQrCodeDataURL(qrDataURL);
          resolve(null);
        };
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
          errorCorrectionLevel: 'H',
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

    // Sort programs within each day: first by session number (2, 3, 4), then alphabetically by name within each session
    Object.keys(grouped).forEach(day => {
      grouped[day].sort((a, b) => {
        // First sort by session number (2, 3, 4)
        const sessionA = parseInt(a.session || '0') || 0;
        const sessionB = parseInt(b.session || '0') || 0;
        if (sessionA !== sessionB) {
          return sessionA - sessionB;
        }
        
        // If same session, sort by program name alphabetically
        const nameA = (a.program || '').toLowerCase();
        const nameB = (b.program || '').toLowerCase();
        return nameA.localeCompare(nameB);
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
      {/* Cover page must be first and isolated */}
      <style>{`
        /* Screen view - center the container */
        .print-container {
          margin: 0 auto !important;
        }
        
        /* Odd pages (1, 3, 5...) - binding on left, so left margin is larger */
        @page:right {
          size: letter portrait;
          margin: 10mm 5mm 10mm 20mm; /* top right bottom left - left margin 20mm for binding */
          @bottom-right {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 7px;
            color: #666;
            font-family: Arial, sans-serif;
            vertical-align: top;
          }
        }
        
        /* Even pages (2, 4, 6...) - binding on right, so right margin is larger */
        @page:left {
          size: letter portrait;
          margin: 10mm 20mm 10mm 5mm; /* top right bottom left - right margin 20mm for binding */
          @bottom-left {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 7px;
            color: #666;
            font-family: Arial, sans-serif;
            vertical-align: top;
          }
        }
        
        /* Cover page (page 1) - odd page, no page number */
        @page:first {
          size: letter portrait;
          margin: 10mm 5mm 10mm 20mm; /* same as odd pages - left margin 20mm */
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
          body > div {
            margin: 0 !important;
            padding: 0 !important;
            width: 8.5in !important;
            max-width: 8.5in !important;
          }
          
          .print-container {
            margin: 0 !important;
            padding: 0 !important;
            width: 8.5in !important;
            max-width: 8.5in !important;
          }
          
          /* Cover page must break out of container padding completely */
          .print-container > .cover-page-new:first-child {
            margin-left: -20px !important;
            margin-right: -20px !important;
            margin-top: -20px !important;
            width: calc(8.5in + 40px) !important;
            max-width: calc(8.5in + 40px) !important;
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
          
          /* New cover page - uses same margins as other pages */
          .cover-page-new {
            margin: 0;
            padding: 0;
            min-height: calc(11in - 10mm - 8mm); /* Full height minus top and bottom margins */
            width: 100%;
            page-break-after: always;
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
          }
          
          /* Content wrapper after cover page - ensure it's visible */
          .content-wrapper {
            display: block !important;
            padding: 20px !important;
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
          🖨️ Print the program guide
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

      {/* New Cover Page - uses same margins as other pages */}
      <div className="cover-page-new" style={{
        background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)',
        color: 'white',
        padding: '0'
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
                {/* Program Title with Session # */}
                <div style={{
                  fontSize: '16px',
                  fontWeight: 'bold',
                  color: '#2e7d32',
                  marginBottom: '10px',
                  borderBottom: '2px solid #e8f5e9',
                  paddingBottom: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span>{program.program || 'N/A'}</span>
                  {program.session && program.session.trim() !== '' && (
                    <span style={{
                      fontSize: '14px',
                      fontWeight: 'normal',
                      color: '#666',
                      marginLeft: 'auto'
                    }}>
                      Session {program.session}
                    </span>
                  )}
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

