import os
import sqlite3
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import io
import pytz
import time

# Use environment variable for port, default to 8000 (Render uses PORT env var)
PORT = int(os.environ.get("PORT", 8000))

# Database file path
DB_PATH = "class_cancellations.db"

# Set timezone to Kingston, Ontario
KINGSTON_TZ = pytz.timezone('America/Toronto')

app = FastAPI(title="Program Schedule Update API")

# Allow CORS for frontend - specifically allow Render domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://class-cancellation-frontend.onrender.com",
        "https://class-cancellation-frontend.onrender.com/",
        "http://localhost:3000",  # For local development
        "https://localhost:3000"   # For local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.onrender\.com",
)

def calculate_withdrawal(date_range: str, class_cancellation: str) -> str:
    """
    Calculate withdrawal eligibility based on:
    - If 3 or more classes have finished: "No"
    - If less than 3 classes finished: "Yes"
    
    Class calculation considers:
    - Start date from date_range
    - Today's date
    - Cancelled classes between these dates
    """
    try:
        if not date_range or date_range.strip() == '':
            return "Unknown"
        
        # Parse the date range (assuming format like "Sep 9 - Dec 16, 2025")
        # Extract start date - handle multiple hyphens properly
        # For dates like "2025-09-09 - 2025-12-16", we need to find the last hyphen that separates the range
        if date_range.count('-') >= 2:
            # Handle ISO format dates with multiple hyphens
            # Find the last hyphen that separates the date range
            last_hyphen_index = date_range.rfind(' - ')
            if last_hyphen_index != -1:
                start_date_str = date_range[:last_hyphen_index].strip()
            else:
                # Fallback: split by " - " (space-hyphen-space)
                date_parts = date_range.split(' - ')
                if len(date_parts) < 2:
                    return "Unknown"
                start_date_str = date_parts[0].strip()
        else:
            # Simple case: single hyphen
            date_parts = date_range.split('-')
            if len(date_parts) < 2:
                return "Unknown"
            start_date_str = date_parts[0].strip()
        
        # Handle ISO format dates (e.g., "2025-09-09")
        start_date = None
        if '-' in start_date_str and len(start_date_str.split('-')) == 3:
            # This might be an ISO date, try to parse it directly
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                print(f"✅ Parsed ISO date: {start_date}")
            except ValueError:
                pass  # Continue with normal parsing
        
        # Try different date formats
        date_formats = [
            "%a %d/%m/%Y",    # "Wed 03/09/2025" (your Excel format)
            "%b %d, %Y",      # "Sep 9, 2025"
            "%B %d, %Y",      # "September 9, 2025"
            "%b %d %Y",       # "Sep 9 2025"
            "%B %d %Y",       # "September 9 2025"
            "%Y-%m-%d",       # "2025-09-09"
            "%m/%d/%Y",       # "09/09/2025"
            "%d/%m/%Y",       # "03/09/2025" (DD/MM/YYYY)
            "%b %d",          # "Sep 9" (without year)
            "%B %d",          # "September 9" (without year)
        ]
        
        print(f"🔍 Trying to parse start date: '{start_date_str}'")
        print(f"📅 Available formats: {date_formats}")
        
        for fmt in date_formats:
            try:
                if fmt in ["%b %d", "%B %d"]:
                    # For dates without year, add current year
                    test_date = f"{start_date_str} {datetime.now(KINGSTON_TZ).year}"
                    start_date = datetime.strptime(test_date, f"{fmt} %Y")
                    print(f"✅ Parsed with format '{fmt}': {start_date}")
                else:
                    start_date = datetime.strptime(start_date_str, fmt)
                    print(f"✅ Parsed with format '{fmt}': {start_date}")
                break
            except ValueError as e:
                print(f"❌ Format '{fmt}' failed: {e}")
                continue
        
        if not start_date:
            # Try to extract just the month and day if all else fails
            try:
                # Look for patterns like "Sep 9" or "September 9"
                import re
                month_day_match = re.search(r'([A-Za-z]+)\s+(\d+)', start_date_str)
                if month_day_match:
                    month_str = month_day_match.group(1)
                    day_str = month_day_match.group(2)
                    # Try to parse with current year
                    current_year = datetime.now(KINGSTON_TZ).year
                    start_date = datetime.strptime(f"{month_str} {day_str} {current_year}", "%b %d %Y")
                    print(f"✅ Parsed date using fallback: {start_date}")
            except Exception as e:
                print(f"❌ Fallback parsing failed: {e}")
                return "Unknown"
        
        # Get today's date in Kingston timezone
        today = datetime.now(KINGSTON_TZ).date()
        start_date = start_date.date()
        
        # Calculate actual class days between start date and today
        # For date ranges like "Wed 03/09/2025 - Fri 14/11/2025", classes are on Wednesdays and Fridays
        
        # Extract the days of the week from the date range
        # Handle all possible combinations like:
        # "Wed 03/09/2025 - Fri 14/11/2025" (Wed, Fri)
        # "Tue 05/09/2025 - Thu 14/11/2025" (Tue, Thu)
        # "Mon 02/09/2025 - Wed 13/11/2025" (Mon, Wed)
        # "Mon 01/09/2025 - Fri 15/11/2025" (Mon, Tue, Wed, Thu, Fri)
        
        day_abbreviations = []
        
        # Check for all possible day abbreviations in the date range
        if 'Mon' in date_range:
            day_abbreviations.append('Mon')
        if 'Tue' in date_range:
            day_abbreviations.append('Tue')
        if 'Wed' in date_range:
            day_abbreviations.append('Wed')
        if 'Thu' in date_range:
            day_abbreviations.append('Thu')
        if 'Fri' in date_range:
            day_abbreviations.append('Fri')
        if 'Sat' in date_range:
            day_abbreviations.append('Sat')
        if 'Sun' in date_range:
            day_abbreviations.append('Sun')
        
        # If no day abbreviations found, assume weekly classes
        if not day_abbreviations:
            day_abbreviations = ['Mon']  # Default to weekly
            print(f"⚠️ No day abbreviations found, assuming weekly classes")
        
        print(f"📅 Classes scheduled on: {', '.join(day_abbreviations)}")
        print(f"📊 Total scheduled days per week: {len(day_abbreviations)}")
        
        # Count actual class days between start and today
        total_classes = 0
        current_date = start_date
        class_days_found = []
        
        print(f"🔍 Counting classes from {start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
        
        while current_date <= today:
            # Check if this date is a scheduled class day
            day_name = current_date.strftime('%a')  # Gets 'Mon', 'Tue', 'Wed', etc.
            
            if day_name in day_abbreviations:
                # This is a scheduled class day
                total_classes += 1
                class_days_found.append(f"{current_date.strftime('%Y-%m-%d')} ({day_name})")
                print(f"✅ Class day: {current_date.strftime('%Y-%m-%d')} ({day_name})")
            
            current_date += timedelta(days=1)
        
        print(f"📋 All class days found: {', '.join(class_days_found)}")
        
        # Count cancelled classes
        cancelled_count = 0
        if class_cancellation and class_cancellation.strip() != '':
            # Split by semicolon and count each cancelled date
            cancelled_dates = [d.strip() for d in class_cancellation.split(';') if d.strip()]
            cancelled_count = len(cancelled_dates)
            print(f"🚫 Cancelled classes: {cancelled_count}")
        
        # Subtract cancelled classes from total
        total_classes = max(0, total_classes - cancelled_count)
        
        print(f"📊 Total classes that would have happened: {total_classes}")
        
        # Determine withdrawal eligibility
        if total_classes >= 3:
            return "No"  # Cannot withdraw after 3 classes
        else:
            return "Yes"  # Can still withdraw
            
    except Exception as e:
        print(f"❌ Error calculating withdrawal: {e}")
        print(f"🔍 Date range: '{date_range}'")
        print(f"🔍 Class cancellation: '{class_cancellation}'")
        import traceback
        print(f"📋 Full error traceback:")
        traceback.print_exc()
        return "Unknown"

def init_database():
    """Initialize SQLite database with tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create main table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet TEXT,
            program TEXT,
            program_id TEXT,
            date_range TEXT,
            time TEXT,
            location TEXT,
            class_room TEXT,
            instructor TEXT,
            program_status TEXT,
            class_cancellation TEXT,
            note TEXT,
            withdrawal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

def import_excel_data(file_content: bytes):
    """Import data from Excel file into SQLite database"""
    try:
        # Read ALL sheets from Excel file
        excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
        
        # Clear existing data
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM programs")
        
        total_records = 0
        
        # Process each sheet
        for sheet_name, df in excel_data.items():
            print(f"Processing sheet: {sheet_name}")
            print(f"Rows in {sheet_name}: {len(df)}")
            
            # Process each row in the sheet
            for _, row in df.iterrows():
                # Extract data with proper handling of NaN values
                def safe_str(value):
                    if pd.isna(value) or value == 'nan' or value == '':
                        return ""
                    return str(value).strip()
                
                program = safe_str(row.get('Event', row.get('event', '')))
                program_id = safe_str(row.get('Course ID', row.get('course_id', '')))
                date_range = safe_str(row.get('Date', row.get('date', '')))
                time = safe_str(row.get('Time', row.get('time', '')))
                location = safe_str(row.get('Location', row.get('location', '')))
                class_room = safe_str(row.get('Facility', row.get('facility', '')))
                instructor = safe_str(row.get('Instructor', row.get('instructor', '')))
                
                # Determine status based on Actions column
                actions = safe_str(row.get('Actions', row.get('actions', '')))
                class_cancellation = safe_str(row.get('Cancellation Date', row.get('cancellation_date', '')))
                
                # Program status: Actions TRUE = whole program cancelled, Actions FALSE = program active
                if actions.strip().upper() == 'TRUE':
                    program_status = "Cancelled"
                else:
                    program_status = "Active"
                
                # Note: class_cancellation field contains individual class cancellation dates
                # for active programs (when Actions = FALSE)
                
                note = safe_str(row.get('Note', row.get('note', '')))
                
                # Calculate withdrawal eligibility
                withdrawal = calculate_withdrawal(date_range, class_cancellation)
                
                # Insert into database with sheet name
                cursor.execute('''
                    INSERT INTO programs (sheet, program, program_id, date_range, time, location, 
                                       class_room, instructor, program_status, class_cancellation, note, withdrawal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sheet_name, program, program_id, date_range, time, location, 
                      class_room, instructor, program_status, class_cancellation, note, withdrawal))
                
                total_records += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Imported {total_records} records to database")
        return True
        
    except Exception as e:
        print(f"❌ Error importing Excel data: {e}")
        return False

def get_programs_from_db(
    program: Optional[str] = None,
    program_id: Optional[str] = None,
    date: Optional[str] = None,
    day: Optional[str] = None,
    location: Optional[str] = None,
    program_status: Optional[str] = None,
    has_cancellation: Optional[bool] = False
):
    """Get programs from SQLite database with filters"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM programs WHERE 1=1"
    params = []
    
    if program:
        query += " AND program LIKE ?"
        params.append(f"%{program}%")
    
    if program_id:
        query += " AND program_id LIKE ?"
        params.append(f"%{program_id}%")
    
    if day:
        query += " AND sheet = ?"
        params.append(day)
    
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    
    if program_status:
        query += " AND program_status = ?"
        params.append(program_status)
    
    if has_cancellation:
        query += " AND class_cancellation != '' AND class_cancellation IS NOT NULL"
    
    # Execute query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    programs = []
    for row in rows:
        programs.append({
            'sheet': row[1],
            'program': row[2],
            'program_id': row[3],
            'date_range': row[4],
            'time': row[5],
            'location': row[6],
            'class_room': row[7],
            'instructor': row[8],
            'program_status': row[9],
            'class_cancellation': row[10],
            'note': row[11],
            'withdrawal': row[12]
        })
    
    conn.close()
    return programs

# Initialize database on startup
init_database()

# Track Excel file modification time
excel_last_modified = None

def check_and_import_excel():
    """Check if Excel file has been modified and re-import if needed"""
    global excel_last_modified
    EXCEL_PATH = "Class Cancellation App.xlsx"
    
    if os.path.exists(EXCEL_PATH):
        current_modified = os.path.getmtime(EXCEL_PATH)
        
        if excel_last_modified is None or current_modified > excel_last_modified:
            print("📁 Excel file modified, auto-importing...")
            try:
                import_excel_data(EXCEL_PATH)
                excel_last_modified = current_modified
                print("✅ Excel file auto-imported successfully")
            except Exception as e:
                print(f"❌ Error auto-importing Excel file: {e}")
    else:
        print("⚠️ Excel file not found")

# Auto-import Excel file on startup if it exists
check_and_import_excel()

# Set up periodic check every 30 seconds
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_import_excel, 'interval', seconds=30)
scheduler.start()

@app.get("/api/test")
def test_connection():
    """Test endpoint to verify connection"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM programs")
    count = cursor.fetchone()[0]
    conn.close()
    
    return {
        "message": "Backend is working with SQLite!",
        "timestamp": datetime.now(KINGSTON_TZ).isoformat(),
        "data_count": count,
        "database": "SQLite"
    }

@app.get("/api/cancellations")
def get_cancellations(
    program: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    day: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    program_status: Optional[str] = Query(None),
    has_cancellation: Optional[bool] = Query(False),
):
    print(f"🌐 API call received from frontend")
    print(f"📊 Query params: {locals()}")
    
    # Get total count first for debugging
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM programs")
    total_count = cursor.fetchone()[0]
    print(f"📈 Total data available: {total_count} rows")
    
    # Check if we have any cancellations
    cursor.execute("SELECT COUNT(*) FROM programs WHERE class_cancellation != '' AND class_cancellation IS NOT NULL")
    cancellation_count = cursor.fetchone()[0]
    print(f"🚫 Cancellations found: {cancellation_count} rows")
    
    conn.close()
    
    programs = get_programs_from_db(
        program=program,
        program_id=program_id,
        date=date,
        day=day,
        location=location,
        program_status=program_status,
        has_cancellation=has_cancellation
    )
    
    print(f"📈 Returning {len(programs)} results")
    return {"data": programs, "last_loaded": datetime.now(KINGSTON_TZ).isoformat()}

@app.post("/api/refresh")
async def refresh_data():
    """Manual refresh endpoint - returns current data count"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM programs")
        count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "message": "Data refreshed successfully",
            "data_count": count,
            "timestamp": datetime.now(KINGSTON_TZ).isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to refresh: {str(e)}"}

@app.post("/api/import-excel")
async def import_excel(file: UploadFile = File(...)):
    """Import Excel file to update database"""
    if file.filename.endswith('.xlsx'):
        content = await file.read()
        success = import_excel_data(content)
        if success:
            return {"message": "Excel file imported successfully", "status": "success"}
        else:
            return {"message": "Error importing Excel file", "status": "error"}
    else:
        return {"message": "Please upload an Excel (.xlsx) file", "status": "error"}

@app.get("/api/export-excel")
def export_excel(
    program: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    day: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    program_status: Optional[str] = Query(None),
    has_cancellation: Optional[bool] = Query(False),
):
    """Export filtered data to Excel format"""
    # Get filtered data
    programs = get_programs_from_db(
        program=program,
        program_id=program_id,
        date=date,
        day=day,
        location=location,
        program_status=program_status,
        has_cancellation=has_cancellation
    )
    
    # Convert to DataFrame
    df = pd.DataFrame(programs)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Programs', index=False)
    
    output.seek(0)
    
    # Return file as response
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=class_cancellations_{datetime.now(KINGSTON_TZ).strftime('%Y%m%d')}.xlsx"}
    )

@app.get("/api/export-pdf")
def export_pdf(
    program: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    day: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    program_status: Optional[str] = Query(None),
    has_cancellation: Optional[bool] = Query(False),
):
    """Export filtered data to PDF format"""
    try:
        # Get filtered data
        programs = get_programs_from_db(
            program=program,
            program_id=program_id,
            date=date,
            day=day,
            location=location,
            program_status=program_status,
            has_cancellation=has_cancellation
        )
        
        # Create PDF using reportlab
        from reportlab.lib.pagesizes import letter, landscape, A4, A3
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        # Create PDF in memory - use A4 landscape with minimal margins for maximum space
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4), 
                               topMargin=0.25*inch, bottomMargin=0.25*inch,
                               leftMargin=0.2*inch, rightMargin=0.2*inch)
        
        # Get page dimensions for dynamic sizing
        page_width, page_height = landscape(A4)
        margin = 0.2 * inch  # Minimal margins for maximum content space
        available_width = page_width - (2 * margin)
        
        # Prepare table data with very short headers to save space
        headers = ['Day', 'Program', 'ID', 'Date', 'Time', 'Loc', 'Room', 'Instructor', 'Status', 'Cancel', 'Info', 'Withdraw']
        table_data = [headers]
        
        for prog in programs:
            # Show more content by using longer truncation limits
            def truncate_text(text, max_length=35):
                if not text:
                    return ''
                text = str(text).strip()
                if len(text) <= max_length:
                    return text
                return text[:max_length-3] + '...'
            
            table_data.append([
                truncate_text(prog['sheet'], 10),  # Day
                truncate_text(prog['program'], 50),  # Program (most important - show more)
                truncate_text(prog['program_id'], 15),  # Program ID
                truncate_text(prog['date_range'], 25),  # Date Range
                truncate_text(prog['time'], 15),  # Time
                truncate_text(prog['location'], 20),  # Location
                truncate_text(prog['class_room'], 15),  # Class Room
                truncate_text(prog['instructor'], 25),  # Instructor
                truncate_text(prog['program_status'], 12),  # Status
                truncate_text(prog['class_cancellation'], 20),  # Cancellation
                truncate_text(prog['note'], 30),  # Additional Info
                truncate_text(prog['withdrawal'], 8)  # Withdrawal
            ])
        
        # Calculate column widths to fit exactly on page - optimized for content visibility
        # Total width must not exceed available_width
        col_widths = [
            available_width * 0.06,   # Day (6%)
            available_width * 0.25,   # Program (25% - most important, needs more space)
            available_width * 0.08,   # ID (8%)
            available_width * 0.12,   # Date (12% - date ranges can be long)
            available_width * 0.08,   # Time (8%)
            available_width * 0.10,   # Location (10%)
            available_width * 0.08,   # Room (8%)
            available_width * 0.13,   # Instructor (13% - names can be long)
            available_width * 0.07,   # Status (7%)
            available_width * 0.10,   # Cancel (10% - cancellation dates)
            available_width * 0.15,   # Info (15% - notes can be long)
            available_width * 0.06    # Withdraw (6%)
        ]
        
        # Verify total width doesn't exceed available space
        total_width = sum(col_widths)
        if total_width > available_width:
            # Scale down proportionally if needed
            scale_factor = available_width / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        # Create table with exact column widths
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header styling - readable fonts and padding
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0072ce')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),  # Slightly larger header font
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            
            # Data row styling - readable fonts and minimal padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 6),  # Slightly larger data font
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Grid and borders - thinner lines
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#0072ce')),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Minimal padding to save space
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 1), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
            
            # Word wrapping and text handling
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        # Build PDF
        doc.build([table])
        output.seek(0)
        
        # Return file as response
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=class_cancellations_{datetime.now(KINGSTON_TZ).strftime('%Y%m%d')}.pdf"}
        )
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return {"error": "Failed to create PDF"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
