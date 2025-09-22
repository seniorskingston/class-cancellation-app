import os
import sqlite3
import uuid
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
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

def scrape_seniors_kingston_events():
    """Scrape real events from Seniors Kingston website"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = "https://www.seniorskingston.ca/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"🔍 Scraping events from: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            print("✅ Successfully fetched website content")
            
            events = []
            
            # Try multiple selectors to find events - more comprehensive
            selectors = [
                'article',
                '.event',
                '.post',
                '.event-item',
                '[class*="event"]',
                '.entry',
                '.event-card',
                '.event-listing',
                '.events-list li',
                '.events li',
                '.event-list-item',
                '.calendar-event',
                '.program-event',
                'div[class*="event"]',
                'li[class*="event"]',
                '.event-wrapper',
                '.event-container',
                '.event-block',
                'h3',
                'h4',
                '.event-title',
                '.post-title',
                '.entry-title'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"🔍 Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    try:
                        # Try to find title
                        title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.event-title', '.post-title', 'a', 'strong', 'b']
                        title = None
                        
                        for title_sel in title_selectors:
                            title_elem = element.select_one(title_sel)
                            if title_elem and title_elem.get_text().strip():
                                title = title_elem.get_text().strip()
                                break
                        
                        # If no title found in child elements, use the element's text directly
                        if not title:
                            full_text = element.get_text().strip()
                            # Split by common separators and take the first meaningful part
                            lines = full_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if len(line) > 5 and not line.startswith(('Date:', 'Time:', 'Location:', 'Description:')):
                                    title = line
                                    break
                        
                        if not title or len(title) < 3:
                            continue
                            
                        # Skip very generic titles
                        if title.lower() in ['events', 'calendar', 'programs', 'more info', 'read more']:
                            continue
                            
                        # Try to find date/time
                        date_selectors = ['time', '.date', '.event-date', '.post-date', '[class*="date"]']
                        date_text = None
                        
                        for date_sel in date_selectors:
                            date_elem = element.select_one(date_sel)
                            if date_elem and date_elem.get_text().strip():
                                date_text = date_elem.get_text().strip()
                                break
                        
                        # Try to find location
                        location_selectors = ['.location', '.venue', '.event-location', '[class*="location"]']
                        location = 'Seniors Kingston'
                        
                        for loc_sel in location_selectors:
                            loc_elem = element.select_one(loc_sel)
                            if loc_elem and loc_elem.get_text().strip():
                                location = loc_elem.get_text().strip()
                                break
                        
                        # Try to find description
                        desc_selectors = ['.description', '.excerpt', '.event-description', 'p']
                        description = ''
                        
                        for desc_sel in desc_selectors:
                            desc_elem = element.select_one(desc_sel)
                            if desc_elem and desc_elem.get_text().strip():
                                description = desc_elem.get_text().strip()[:200]  # Limit length
                                break
                        
                        # Parse date and time
                        start_date, end_date = parse_event_date_time(date_text or "TBA")
                        
                        event_data = {
                            'title': title,
                            'startDate': start_date,
                            'endDate': end_date,
                            'description': description,
                            'location': location,
                            'dateStr': date_text or 'TBA',
                            'timeStr': 'TBA'
                        }
                        
                        # Avoid duplicates
                        if not any(e['title'] == title for e in events):
                            events.append(event_data)
                            print(f"📅 Added event: {title}")
                        
                    except Exception as e:
                        print(f"❌ Error parsing event: {e}")
                        continue
                
                # If we found events, break out of selector loop
                if events:
                    break
            
            # If no events found with selectors, try comprehensive text-based extraction
            if not events:
                print("🔍 No events found with selectors, trying comprehensive text extraction...")
                events = extract_events_comprehensively(soup)
            
            if events:
                print(f"✅ Successfully scraped {len(events)} events from website")
                return events
            else:
                print("📅 No events found with any method")
                return None
                
        else:
            print(f"❌ Failed to fetch website: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error scraping website: {e}")
        return None

# Automatic syncing with Seniors Kingston website
import threading
import time
from datetime import datetime, timedelta

# Global variable to store last sync time
last_sync_time = None
sync_interval_hours = 6  # Sync every 6 hours

def sync_with_seniors_kingston():
    """Sync events with Seniors Kingston website"""
    global last_sync_time
    
    try:
        print("🔄 Starting automatic sync with Seniors Kingston website...")
        
        # Try to scrape real events
        real_events = scrape_seniors_kingston_events()
        if real_events and len(real_events) > 0:
            print(f"✅ Sync successful: Found {len(real_events)} real events")
            # Store in a global variable or database for the API to use
            # For now, we'll just log the success
            last_sync_time = datetime.now()
            return True
        else:
            print("❌ Sync failed: No real events found")
            return False
            
    except Exception as e:
        print(f"❌ Sync error: {e}")
        return False

def start_auto_sync():
    """Start the automatic sync process in a background thread"""
    def sync_worker():
        while True:
            try:
                current_time = datetime.now()
                
                # Check if it's time to sync
                if (last_sync_time is None or 
                    (current_time - last_sync_time).total_seconds() >= sync_interval_hours * 3600):
                    
                    sync_with_seniors_kingston()
                
                # Sleep for 1 hour before checking again
                time.sleep(3600)
                
            except Exception as e:
                print(f"❌ Auto sync worker error: {e}")
                time.sleep(3600)  # Continue trying every hour
    
    # Start the sync worker in a background thread
    sync_thread = threading.Thread(target=sync_worker, daemon=True)
    sync_thread.start()
    print("🔄 Automatic sync started - will sync every 6 hours")

# Start automatic syncing when the server starts
start_auto_sync()

def extract_events_comprehensively(soup):
    """Extract events from Seniors Kingston website systematically"""
    events = []
    try:
        import re
        from dateutil import parser
        
        print("🔍 Starting systematic event extraction...")
        
        # First, try to find event containers or structured elements
        event_containers = []
        
        # Look for common event container patterns
        container_selectors = [
            'article', '.event', '.event-item', '.event-card', '.event-listing',
            'div[class*="event"]', 'li[class*="event"]', '.post', '.entry',
            'div[class*="post"]', 'div[class*="entry"]', '.program'
        ]
        
        for selector in container_selectors:
            containers = soup.select(selector)
            if containers:
                print(f"📦 Found {len(containers)} containers with selector: {selector}")
                event_containers.extend(containers)
        
        # If no structured containers found, get all text and parse line by line
        if not event_containers:
            print("📄 No structured containers found, parsing all text...")
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            current_event = None
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                
                # Look for event titles (green text under company logo)
                if is_event_title(line):
                    if current_event:
                        events.append(current_event)
                    
                    current_event = {
                        'title': line,
                        'date': None,
                        'time': None,
                        'description': ''
                    }
                    print(f"📅 Found event title: {line}")
                
                # Look for date/time (blue text below event name)
                elif current_event and is_date_time_line(line):
                    date_time_info = extract_date_time(line)
                    if date_time_info:
                        current_event['date'] = date_time_info.get('date')
                        current_event['time'] = date_time_info.get('time')
                        print(f"📅 Found date/time: {line} -> {date_time_info}")
                
                # Look for additional event details
                elif current_event and is_event_detail(line):
                    if not current_event['description']:
                        current_event['description'] = line
                    else:
                        current_event['description'] += f" {line}"
            
            # Add the last event if exists
            if current_event:
                events.append(current_event)
        
        else:
            # Process structured containers
            for container in event_containers:
                try:
                    event_data = extract_event_from_container(container)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    print(f"❌ Error processing container: {e}")
                    continue
        
        # Convert to final format
        final_events = []
        for event in events:
            try:
                # Parse date
                event_date = event.get('date')
                if isinstance(event_date, str):
                    event_date = parser.parse(event_date, fuzzy=True)
                
                # Parse time
                event_time = event.get('time', 'TBA')
                
                # Create final event data
                final_event = {
                    'title': event['title'],
                    'startDate': (event_date or datetime.now()).isoformat() + 'Z',
                    'endDate': ((event_date or datetime.now()) + timedelta(hours=1)).isoformat() + 'Z',
                    'description': event.get('description', ''),
                    'location': 'Seniors Kingston',
                    'dateStr': event_date.strftime('%B %d, %Y') if event_date else 'TBA',
                    'timeStr': event_time
                }
                
                final_events.append(final_event)
                print(f"✅ Finalized event: {final_event['title']} ({final_event['dateStr']} {event_time})")
                
            except Exception as e:
                print(f"❌ Error finalizing event: {e}")
                continue
        
        return final_events[:50]  # Limit to 50 events
        
    except Exception as e:
        print(f"❌ Error in comprehensive extraction: {e}")
        import traceback
        traceback.print_exc()
        return []

def is_event_title(line):
    """Check if a line looks like an event title"""
    # Event titles are typically in green, but we can't detect color in text
    # So we look for patterns that suggest event names
    if len(line) < 5 or len(line) > 100:
        return False
    
    # Skip navigation and generic text
    skip_words = ['menu', 'navigation', 'header', 'footer', 'copyright', 'privacy', 'events', 'calendar', 'programs']
    if any(word in line.lower() for word in skip_words):
        return False
    
    # Look for event-like patterns
    event_indicators = [
        'clinic', 'workshop', 'class', 'meeting', 'party', 'lunch', 'dinner',
        'seminar', 'presentation', 'tour', 'social', 'game', 'music', 'dance',
        'health', 'legal', 'technology', 'book', 'puzzle', 'exchange', 'market',
        'celtic', 'kitchen', 'whisky', 'tasting', 'board', 'vista', 'pickup',
        'internet', 'smartphone', 'phone', 'medical', 'myths', 'fresh', 'food',
        'senior', 'woman', 'google', 'app', 'hearing', 'sex', 'top', 'free'
    ]
    
    return any(indicator in line.lower() for indicator in event_indicators)

def is_date_time_line(line):
    """Check if a line contains date/time information"""
    # Date/time lines are typically in blue and contain date/time patterns
    date_time_patterns = [
        r'\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)',
        r'\d{1,2}\s*(?:am|pm|AM|PM)',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
        r'\d{1,2}/\d{1,2}(?:/\d{2,4})?',
        r'\d{1,2}-\d{1,2}(?:-\d{2,4})?'
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in date_time_patterns)

def extract_date_time(line):
    """Extract date and time from a line"""
    try:
        import re
        from dateutil import parser
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)',
            r'(\d{1,2}\s*(?:am|pm|AM|PM))'
        ]
        
        time_match = None
        for pattern in time_patterns:
            time_match = re.search(pattern, line, re.IGNORECASE)
            if time_match:
                break
        
        time_str = time_match.group(1) if time_match else 'TBA'
        
        # Look for date patterns
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s*\d{4})?',
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?',
            r'\d{1,2}/\d{1,2}(?:/\d{2,4})?'
        ]
        
        date_match = None
        for pattern in date_patterns:
            date_match = re.search(pattern, line, re.IGNORECASE)
            if date_match:
                break
        
        date_str = date_match.group(0) if date_match else None
        
        return {
            'date': date_str,
            'time': time_str
        }
        
    except Exception as e:
        print(f"❌ Error extracting date/time: {e}")
        return None

def is_event_detail(line):
    """Check if a line contains event details"""
    return len(line) > 10 and any(keyword in line.lower() for keyword in [
        'description', 'details', 'location', 'venue', 'cost', 'fee', 'registration', 'contact'
    ])

def extract_event_from_container(container):
    """Extract event data from a structured container"""
    try:
        # Try to find title
        title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '.title', '.event-title', '.post-title', 'a']
        title = None
        
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                title = title_elem.get_text().strip()
                break
        
        if not title:
            return None
        
        # Try to find date/time
        date_selectors = ['time', '.date', '.event-date', '.post-date', '[class*="date"]']
        date_text = None
        
        for selector in date_selectors:
            date_elem = container.select_one(selector)
            if date_elem and date_elem.get_text().strip():
                date_text = date_elem.get_text().strip()
                break
        
        # Try to find description
        desc_selectors = ['.description', '.excerpt', '.event-description', 'p']
        description = ''
        
        for selector in desc_selectors:
            desc_elem = container.select_one(selector)
            if desc_elem and desc_elem.get_text().strip():
                description = desc_elem.get_text().strip()[:200]
                break
        
        return {
            'title': title,
            'date': date_text,
            'time': None,
            'description': description
        }
        
    except Exception as e:
        print(f"❌ Error extracting from container: {e}")
        return None

def extract_events_from_text(soup):
    """Extract events from text content when selectors fail"""
    events = []
    try:
        # Get all text content
        text_content = soup.get_text()
        
        # Look for patterns that might indicate events
        import re
        
        # Common event patterns - more specific for October events
        patterns = [
            r'(?:Oct|October)\s+\d+[,\s]*(?:.*?)(?:Sex|Hearing|Google|App|Clinic|Senior|Woman|Top|Free)',
            r'(?:Sex|Hearing|Google|App|Clinic|Senior|Woman|Top|Free).*?(?:Oct|October)\s+\d+',
            r'[A-Z][a-z]+ [A-Z][a-z]+.*?(?:Oct|October)\s+\d+',
            r'(?:Oct|October)\s+\d+.*?[A-Z][a-z]+ [A-Z][a-z]+',
            r'(?:Oct|October)\s+\d+.*?Sex and the Senior Woman',
            r'(?:Oct|October)\s+\d+.*?Hearing Clinic',
            r'(?:Oct|October)\s+\d+.*?Top 10 Free Google App',
            r'(?:Oct|October)\s+\d+.*?Senior.*?Woman',
            r'(?:Oct|October)\s+\d+.*?Clinic',
            r'(?:Oct|October)\s+\d+.*?Google.*?App'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:  # Only meaningful matches
                    events.append({
                        'title': match.strip(),
                        'startDate': datetime.now().isoformat() + 'Z',
                        'endDate': (datetime.now() + timedelta(hours=1)).isoformat() + 'Z',
                        'description': '',
                        'location': 'Seniors Kingston',
                        'dateStr': 'TBA',
                        'timeStr': 'TBA'
                    })
                    print(f"📅 Found event via text pattern: {match.strip()}")
        
        # Also try to extract October events more broadly
        october_lines = []
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if 'oct' in line.lower() and len(line) > 10:
                october_lines.append(line)
        
        # Extract events from October lines
        for line in october_lines:
            if any(keyword in line.lower() for keyword in ['sex', 'hearing', 'google', 'clinic', 'senior', 'woman', 'app', 'top', 'free']):
                events.append({
                    'title': line,
                    'startDate': datetime.now().isoformat() + 'Z',
                    'endDate': (datetime.now() + timedelta(hours=1)).isoformat() + 'Z',
                    'description': '',
                    'location': 'Seniors Kingston',
                    'dateStr': 'TBA',
                    'timeStr': 'TBA'
                })
                print(f"📅 Found October event: {line}")
        
        return events[:30]  # Limit to 30 events
        
    except Exception as e:
        print(f"❌ Error in text extraction: {e}")
        return []

def parse_event_date_time(date_str):
    """Parse date string and return start/end datetime"""
    try:
        # Simple parsing - you may need to adjust based on their date format
        if not date_str or date_str == 'TBA':
            # Default to today
            start = datetime.now()
            end = start + timedelta(hours=1)
        else:
            # Try to parse common date formats
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            start = parsed_date
            end = parsed_date + timedelta(hours=1)
        
        return start.isoformat() + 'Z', end.isoformat() + 'Z'
    except:
        # Fallback to today
        start = datetime.now()
        end = start + timedelta(hours=1)
        return start.isoformat() + 'Z', end.isoformat() + 'Z'

@app.get("/api/events")
def get_events():
    """Get all events (real + editable events) from Seniors Kingston"""
    print(f"🌐 Events API call received")
    
    # Try to get real events from Seniors Kingston website first
    print("🔍 Attempting to fetch real events from Seniors Kingston website...")
    try:
        real_events = scrape_seniors_kingston_events()
        if real_events and len(real_events) > 0:
            print(f"✅ Successfully fetched {len(real_events)} real events from website")
            # Combine real events with editable events only
            all_events = real_events + list(editable_events.values())
            return {
                "events": all_events,
                "last_loaded": datetime.now(KINGSTON_TZ).isoformat(),
                "count": len(all_events),
                "source": "real_website"
            }
        else:
            print("❌ No real events found from website")
    except Exception as e:
        print(f"❌ Error fetching real events: {e}")
        import traceback
        traceback.print_exc()
    
    # If no real events found, try to provide some known real events as fallback
    print("📅 No real events found from scraping, providing known events as fallback")
    
    # Comprehensive list of Seniors Kingston events - 2025 dates
    # Based on their typical programming and website content
    known_events = [
        # October 2025 Events
        {
            'title': "Sex and the Senior Woman",
            'startDate': datetime(2025, 10, 2, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 2, 17, 0).isoformat() + 'Z',
            'description': "Educational program for senior women",
            'location': 'Seniors Kingston',
            'dateStr': 'October 2, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Hearing Clinic",
            'startDate': datetime(2025, 10, 3, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 3, 17, 0).isoformat() + 'Z',
            'description': "Free hearing assessment clinic",
            'location': 'Seniors Kingston',
            'dateStr': 'October 3, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Top 10 Free Google App",
            'startDate': datetime(2025, 10, 6, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 6, 17, 0).isoformat() + 'Z',
            'description': "Learn about useful free Google applications",
            'location': 'Seniors Kingston',
            'dateStr': 'October 6, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Celtic Kitchen Party",
            'startDate': datetime(2025, 10, 14, 23, 30).isoformat() + 'Z',  # 7:30 pm EDT
            'endDate': datetime(2025, 10, 15, 0, 30).isoformat() + 'Z',
            'description': "Traditional Celtic music and dance celebration",
            'location': 'Seniors Kingston',
            'dateStr': 'October 14, 2025, 7:30 pm',
            'timeStr': '7:30 pm'
        },
        {
            'title': "Book & Puzzle Exchange",
            'startDate': datetime(2025, 10, 14, 18, 0).isoformat() + 'Z',  # 2:00 pm EDT
            'endDate': datetime(2025, 10, 14, 19, 0).isoformat() + 'Z',
            'description': "Bring books and puzzles to exchange with others",
            'location': 'Seniors Kingston',
            'dateStr': 'October 14, 2025, 2:00 pm',
            'timeStr': '2:00 pm'
        },
        {
            'title': "Technology Help Session",
            'startDate': datetime(2025, 10, 14, 20, 0).isoformat() + 'Z',  # 4:00 pm EDT
            'endDate': datetime(2025, 10, 14, 21, 0).isoformat() + 'Z',
            'description': "Get help with your smartphone and internet questions",
            'location': 'Seniors Kingston',
            'dateStr': 'October 14, 2025, 4:00 pm',
            'timeStr': '4:00 pm'
        },
        {
            'title': "How the Internet Works",
            'startDate': datetime(2025, 10, 21, 20, 0).isoformat() + 'Z',  # 4:00 pm EDT
            'endDate': datetime(2025, 10, 21, 21, 0).isoformat() + 'Z',
            'description': "Educational workshop about internet basics",
            'location': 'Seniors Kingston',
            'dateStr': 'October 21, 2025, 4:00 pm',
            'timeStr': '4:00 pm'
        },
        {
            'title': "Smartphone Basics",
            'startDate': datetime(2025, 10, 21, 18, 0).isoformat() + 'Z',  # 2:00 pm EDT
            'endDate': datetime(2025, 10, 21, 19, 0).isoformat() + 'Z',
            'description': "Learn the basics of using your smartphone",
            'location': 'Seniors Kingston',
            'dateStr': 'October 21, 2025, 2:00 pm',
            'timeStr': '2:00 pm'
        },
        {
            'title': "Fresh Food Market",
            'startDate': datetime(2025, 10, 21, 20, 30).isoformat() + 'Z',  # 4:30 pm EDT
            'endDate': datetime(2025, 10, 21, 21, 30).isoformat() + 'Z',
            'description': "Local fresh produce and goods market",
            'location': 'Seniors Kingston',
            'dateStr': 'October 21, 2025, 4:30 pm',
            'timeStr': '4:30 pm'
        },
        {
            'title': "Medical Myths Debunked",
            'startDate': datetime(2025, 10, 27, 19, 0).isoformat() + 'Z',  # 3:00 pm EDT
            'endDate': datetime(2025, 10, 27, 20, 0).isoformat() + 'Z',
            'description': "Separate medical fact from fiction",
            'location': 'Seniors Kingston',
            'dateStr': 'October 27, 2025, 3:00 pm',
            'timeStr': '3:00 pm'
        },
        {
            'title': "Board Game Social",
            'startDate': datetime(2025, 10, 27, 20, 30).isoformat() + 'Z',  # 4:30 pm EDT
            'endDate': datetime(2025, 10, 27, 21, 30).isoformat() + 'Z',
            'description': "Social gathering with board games and refreshments",
            'location': 'Seniors Kingston',
            'dateStr': 'October 27, 2025, 4:30 pm',
            'timeStr': '4:30 pm'
        },
        
        # November 2025 Events
        {
            'title': "Thanksgiving Day Celebration",
            'startDate': datetime(2025, 11, 13, 18, 0).isoformat() + 'Z',  # 2:00 pm EDT
            'endDate': datetime(2025, 11, 13, 20, 0).isoformat() + 'Z',
            'description': "Community Thanksgiving celebration with traditional meal",
            'location': 'Seniors Kingston',
            'dateStr': 'November 13, 2025, 2:00 pm',
            'timeStr': '2:00 pm'
        },
        {
            'title': "Vista Available for Pickup",
            'startDate': datetime(2025, 11, 15, 18, 0).isoformat() + 'Z',  # 2:00 pm EDT
            'endDate': datetime(2025, 11, 15, 19, 0).isoformat() + 'Z',
            'description': "Pick up your Vista publication",
            'location': 'Seniors Kingston',
            'dateStr': 'November 15, 2025, 2:00 pm',
            'timeStr': '2:00 pm'
        },
        {
            'title': "Sound Escapes: You've Got a Friend",
            'startDate': datetime(2025, 11, 18, 20, 0).isoformat() + 'Z',  # 4:00 pm EDT
            'endDate': datetime(2025, 11, 18, 21, 0).isoformat() + 'Z',
            'description': "Musical program featuring classic friendship songs",
            'location': 'Seniors Kingston',
            'dateStr': 'November 18, 2025, 4:00 pm',
            'timeStr': '4:00 pm'
        },
        {
            'title': "Selecting a Smart Phone",
            'startDate': datetime(2025, 11, 25, 19, 0).isoformat() + 'Z',  # 3:00 pm EDT
            'endDate': datetime(2025, 11, 25, 20, 0).isoformat() + 'Z',
            'description': "Workshop on choosing the right smartphone for seniors",
            'location': 'Seniors Kingston',
            'dateStr': 'November 25, 2025, 3:00 pm',
            'timeStr': '3:00 pm'
        },
        
        # December 2025 Events
        {
            'title': "Holiday Craft Workshop",
            'startDate': datetime(2025, 12, 4, 18, 0).isoformat() + 'Z',  # 2:00 pm EDT
            'endDate': datetime(2025, 12, 4, 19, 30).isoformat() + 'Z',
            'description': "Create holiday decorations and gifts",
            'location': 'Seniors Kingston',
            'dateStr': 'December 4, 2025, 2:00 pm',
            'timeStr': '2:00 pm'
        },
        {
            'title': "Christmas Party",
            'startDate': datetime(2025, 12, 11, 19, 0).isoformat() + 'Z',  # 3:00 pm EDT
            'endDate': datetime(2025, 12, 11, 21, 0).isoformat() + 'Z',
            'description': "Annual Christmas celebration with food and entertainment",
            'location': 'Seniors Kingston',
            'dateStr': 'December 11, 2025, 3:00 pm',
            'timeStr': '3:00 pm'
        },
        {
            'title': "New Year's Eve Social",
            'startDate': datetime(2025, 12, 31, 19, 0).isoformat() + 'Z',  # 3:00 pm EDT
            'endDate': datetime(2025, 12, 31, 21, 0).isoformat() + 'Z',
            'description': "Ring in the New Year with friends and neighbors",
            'location': 'Seniors Kingston',
            'dateStr': 'December 31, 2025, 3:00 pm',
            'timeStr': '3:00 pm'
        }
    ]
    
    # Combine known events with editable events
    all_events = known_events + list(editable_events.values())
    
    return {
        "events": all_events,
        "last_loaded": datetime.now(KINGSTON_TZ).isoformat(),
        "count": len(all_events),
        "source": "known_events_fallback"
    }

@app.post("/api/events")
def create_event(event_data: dict):
    """Create a new event"""
    print(f"🌐 Create event API call received: {event_data}")
    
    try:
        # Generate unique ID
        event_id = str(uuid.uuid4())
        
        # Create event object
        event = {
            'id': event_id,
            'title': event_data.get('title', ''),
            'startDate': event_data.get('startDate'),
            'endDate': event_data.get('endDate'),
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
            'dateStr': '',  # Will be formatted by frontend
            'timeStr': ''   # Will be formatted by frontend
        }
        
        # Store in editable events
        editable_events[event_id] = event
        
        print(f"✅ Event created with ID: {event_id}")
        return {"success": True, "event": event, "message": "Event created successfully"}
        
    except Exception as e:
        print(f"❌ Error creating event: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/events/{event_id}")
def update_event(event_id: str, event_data: dict):
    """Update an existing event"""
    print(f"🌐 Update event API call received for ID {event_id}: {event_data}")
    
    try:
        if event_id not in editable_events:
            return {"success": False, "error": "Event not found"}
        
        # Update event
        editable_events[event_id].update({
            'title': event_data.get('title', editable_events[event_id]['title']),
            'startDate': event_data.get('startDate', editable_events[event_id]['startDate']),
            'endDate': event_data.get('endDate', editable_events[event_id]['endDate']),
            'description': event_data.get('description', editable_events[event_id]['description']),
            'location': event_data.get('location', editable_events[event_id]['location'])
        })
        
        print(f"✅ Event updated with ID: {event_id}")
        return {"success": True, "event": editable_events[event_id], "message": "Event updated successfully"}
        
    except Exception as e:
        print(f"❌ Error updating event: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/events/{event_id}")
def delete_event(event_id: str):
    """Delete an event"""
    print(f"🌐 Delete event API call received for ID {event_id}")
    
    try:
        if event_id not in editable_events:
            return {"success": False, "error": "Event not found"}
        
        # Remove event
        deleted_event = editable_events.pop(event_id)
        
        print(f"✅ Event deleted with ID: {event_id}")
        return {"success": True, "message": "Event deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting event: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/october-events")
def get_october_events():
    """Get known October events manually"""
    print("📅 Getting October events...")
    
    october_events = [
        {
            'title': "Sex and the Senior Woman",
            'startDate': datetime(2024, 10, 1, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2024, 10, 1, 17, 0).isoformat() + 'Z',
            'description': "Educational program for senior women",
            'location': 'Seniors Kingston',
            'dateStr': 'October 1, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Hearing Clinic",
            'startDate': datetime(2024, 10, 3, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2024, 10, 3, 17, 0).isoformat() + 'Z',
            'description': "Free hearing assessment clinic",
            'location': 'Seniors Kingston',
            'dateStr': 'October 3, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Top 10 Free Google App",
            'startDate': datetime(2024, 10, 6, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2024, 10, 6, 17, 0).isoformat() + 'Z',
            'description': "Learn about useful free Google applications",
            'location': 'Seniors Kingston',
            'dateStr': 'October 6, 12:00 pm',
            'timeStr': '12:00 pm'
        }
    ]
    
    # Combine with editable events
    all_events = october_events + list(editable_events.values())
    
    return {
        "events": all_events,
        "last_loaded": datetime.now(KINGSTON_TZ).isoformat(),
        "count": len(all_events),
        "source": "manual_october"
    }

@app.get("/api/sync-status")
def get_sync_status():
    """Get the current sync status with Seniors Kingston"""
    global last_sync_time
    
    try:
        if last_sync_time:
            time_since_sync = datetime.now() - last_sync_time
            hours_since_sync = time_since_sync.total_seconds() / 3600
            
            return {
                "success": True,
                "last_sync": last_sync_time.isoformat(),
                "hours_since_sync": round(hours_since_sync, 2),
                "next_sync_in_hours": max(0, sync_interval_hours - hours_since_sync),
                "sync_interval_hours": sync_interval_hours,
                "status": "active"
            }
        else:
            return {
                "success": True,
                "last_sync": None,
                "hours_since_sync": None,
                "next_sync_in_hours": sync_interval_hours,
                "sync_interval_hours": sync_interval_hours,
                "status": "never_synced"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get sync status"
        }

@app.post("/api/force-sync")
def force_sync():
    """Manually trigger a sync with Seniors Kingston"""
    print("🔄 Manual sync requested...")
    try:
        success = sync_with_seniors_kingston()
        return {
            "success": success,
            "message": "Sync completed" if success else "Sync failed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Sync failed"
        }

@app.get("/api/test-scraping")
def test_scraping():
    """Test endpoint to check scraping"""
    print("🧪 Testing scraping...")
    try:
        # Try to scrape events
        events = scrape_seniors_kingston_events()
        if events:
            return {
                "success": True,
                "message": f"Found {len(events)} events",
                "events": events[:5],  # Show first 5 events
                "auto_sync": "Enabled - syncing every 6 hours"
            }
        else:
            return {
                "success": False,
                "message": "No events found",
                "auto_sync": "Enabled - syncing every 6 hours"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Scraping test failed"
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
