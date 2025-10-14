import os
import sqlite3
import uuid
from fastapi import FastAPI, Query, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import json
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import io
import pytz
import time
from dateutil import parser

# Use environment variable for port, default to 8000 (Render uses PORT env var)
PORT = int(os.environ.get("PORT", 8000))

# Database file path
DB_PATH = "class_cancellations.db"

# Set timezone to Kingston, Ontario
KINGSTON_TZ = pytz.timezone('America/Toronto')
utc = pytz.UTC

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

def import_excel_data(file_path_or_content):
    """Import data from Excel file into SQLite database"""
    try:
        # Handle both file path (string) and file content (bytes)
        if isinstance(file_path_or_content, str):
            # It's a file path, read directly
            excel_data = pd.read_excel(file_path_or_content, sheet_name=None)
        else:
            # It's file content (bytes), use BytesIO
            excel_data = pd.read_excel(io.BytesIO(file_path_or_content), sheet_name=None)
        
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
                
                # Normalize date format: replace periods with commas for better parsing
                if class_cancellation and class_cancellation != '':
                    class_cancellation = class_cancellation.replace('.', ',')
                
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
    
    if program and program_id and program == program_id:
        # Unified search: search for both program name and program ID with OR
        normalized_id = program_id.lstrip('0') or '0'
        query += " AND (program LIKE ? OR program_id LIKE ? OR program_id LIKE ?)"
        params.append(f"%{program}%")
        params.append(f"%{program_id}%")
        params.append(f"%{normalized_id}%")
    else:
        # Separate searches
        if program:
            query += " AND program LIKE ?"
            params.append(f"%{program}%")
        
        if program_id:
            # Handle both original and normalized program IDs
            # Try both the original ID and the ID with leading zeros stripped
            normalized_id = program_id.lstrip('0') or '0'
            query += " AND (program_id LIKE ? OR program_id LIKE ?)"
            params.append(f"%{program_id}%")
            params.append(f"%{normalized_id}%")
    
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

# In-memory storage for editable events (in production, this would be a database)
editable_events = {}

# Initialize known_events at module level
known_events = [
    # 2025 Canadian Holidays
    {
        'title': 'New Year\'s Day',
        'startDate': datetime(2025, 1, 1, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 1, 1, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'New Year\'s Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Good Friday',
        'startDate': datetime(2025, 4, 18, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 4, 18, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Good Friday - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Easter Monday',
        'startDate': datetime(2025, 4, 21, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 4, 21, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Easter Monday - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Victoria Day',
        'startDate': datetime(2025, 5, 19, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 5, 19, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Victoria Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Saint-Jean-Baptiste Day',
        'startDate': datetime(2025, 6, 24, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 6, 24, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Saint-Jean-Baptiste Day - Quebec holiday',
        'location': 'Quebec'
    },
    {
        'title': 'Canada Day',
        'startDate': datetime(2025, 7, 1, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 7, 1, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Canada Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Civic Holiday',
        'startDate': datetime(2025, 8, 4, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 8, 4, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Civic Holiday - Provincial holiday (excluding Quebec)',
        'location': 'Canada (excluding Quebec)'
    },
    {
        'title': 'Labour Day',
        'startDate': datetime(2025, 9, 1, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 9, 1, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Labour Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'National Day for Truth and Reconciliation',
        'startDate': datetime(2025, 9, 30, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 9, 30, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'National Day for Truth and Reconciliation - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Thanksgiving Day',
        'startDate': datetime(2025, 10, 13, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 10, 13, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Thanksgiving Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Christmas Day',
        'startDate': datetime(2025, 12, 25, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 12, 25, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Christmas Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Boxing Day',
        'startDate': datetime(2025, 12, 26, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2025, 12, 26, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Boxing Day - Federal holiday',
        'location': 'Canada'
    },
    
    # 2026 Canadian Holidays
    {
        'title': 'New Year\'s Day',
        'startDate': datetime(2026, 1, 1, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 1, 1, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'New Year\'s Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Family Day',
        'startDate': datetime(2026, 2, 16, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 2, 16, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Family Day - Provincial holiday',
        'location': 'Canada'
    },
    {
        'title': 'Good Friday',
        'startDate': datetime(2026, 4, 3, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 4, 3, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Good Friday - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Victoria Day',
        'startDate': datetime(2026, 5, 18, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 5, 18, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Victoria Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Canada Day',
        'startDate': datetime(2026, 7, 1, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 7, 1, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Canada Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Civic Holiday',
        'startDate': datetime(2026, 8, 3, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 8, 3, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Civic Holiday - Provincial holiday (Optional)',
        'location': 'Canada'
    },
    {
        'title': 'Labour Day',
        'startDate': datetime(2026, 9, 7, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 9, 7, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Labour Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Thanksgiving Day',
        'startDate': datetime(2026, 10, 12, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 10, 12, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Thanksgiving Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Christmas Day',
        'startDate': datetime(2026, 12, 25, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 12, 25, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Christmas Day - Federal holiday',
        'location': 'Canada'
    },
    {
        'title': 'Boxing Day',
        'startDate': datetime(2026, 12, 26, 9, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'endDate': datetime(2026, 12, 26, 17, 0, tzinfo=KINGSTON_TZ).astimezone(utc),
        'description': 'Boxing Day - Federal holiday',
        'location': 'Canada'
    }
]

# Analytics tracking
analytics_data = {
    'desktop_visits': 25,  # Sample data to show how reports look
    'mobile_visits': 18,   # Sample data to show how reports look
    'total_visits': 43,    # Sample data to show how reports look
    'last_reset': datetime.now().isoformat()
}

def track_visit(user_agent: str):
    """Track a visit and determine if it's desktop or mobile"""
    global analytics_data
    
    # Simple mobile detection based on user agent
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'tablet', 'blackberry', 'windows phone']
    is_mobile = any(keyword in user_agent.lower() for keyword in mobile_keywords)
    
    analytics_data['total_visits'] += 1
    if is_mobile:
        analytics_data['mobile_visits'] += 1
    else:
        analytics_data['desktop_visits'] += 1
    
    print(f"📊 Visit tracked: {'Mobile' if is_mobile else 'Desktop'} - Total: {analytics_data['total_visits']}")

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

@app.get("/api/events")
def get_events(request: Request):
    """Get all events (real + editable events) from Seniors Kingston"""
    print(f"🌐 Events API call received")
    
    # Track the visit
    user_agent = request.headers.get('user-agent', '')
    track_visit(user_agent)
    
    # Combine known events with Canadian holidays and editable events
    all_events = known_events + list(editable_events.values())
    
    return {
        "events": all_events,
        "last_loaded": datetime.now(KINGSTON_TZ).isoformat(),
        "count": len(all_events),
        "source": "known_events_fallback"
    }

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

@app.post("/api/refresh")
async def refresh_data():
    """Manual refresh endpoint - checks and re-imports Excel if needed, returns current data count"""
    try:
        # Force check and import Excel file
        check_and_import_excel()
        
        # Get current data count
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM programs")
        count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "message": "Data refreshed and Excel checked",
            "data_count": count,
            "timestamp": datetime.now(KINGSTON_TZ).isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to refresh: {str(e)}"}

@app.get("/analytics")
def analytics_web_interface():
    """Simple analytics report showing just the visit numbers"""
    global analytics_data
    
    desktop_percentage = (analytics_data['desktop_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    mobile_percentage = (analytics_data['mobile_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>App Visit Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 40px;
                background: #f8f9fa;
                color: #333;
            }}
            .report-card {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            h1 {{
                color: #0072ce;
                margin-bottom: 30px;
                font-size: 2.2rem;
                font-weight: 600;
            }}
            .visit-number {{
                font-size: 4.5rem;
                font-weight: bold;
                color: #0072ce;
                margin: 20px 0;
                text-shadow: 2px 2px 4px rgba(0, 114, 206, 0.1);
                line-height: 1;
            }}
            .visit-label {{
                font-size: 1.5rem;
                color: #333;
                margin-bottom: 30px;
                font-weight: 600;
            }}
            .breakdown {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 30px 0;
            }}
            .breakdown-item {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #0072ce;
            }}
            .breakdown-number {{
                font-size: 2.5rem;
                font-weight: bold;
                color: #0072ce;
                line-height: 1;
            }}
            .breakdown-label {{
                font-size: 1.1rem;
                color: #333;
                margin-top: 8px;
                font-weight: 500;
            }}
            .date-info {{
                color: #888;
                font-size: 0.9rem;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="report-card">
            <h1>📊 App Visit Report</h1>
            
            <div class="visit-number">{analytics_data['total_visits']}</div>
            <div class="visit-label">Total App Visits</div>
            
            <div class="breakdown">
                <div class="breakdown-item">
                    <div class="breakdown-number">{analytics_data['desktop_visits']}</div>
                    <div class="breakdown-label">Desktop Users</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-number">{analytics_data['mobile_visits']}</div>
                    <div class="breakdown-label">Mobile Users</div>
                </div>
            </div>
            
            <div class="date-info">
                Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

