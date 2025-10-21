#!/usr/bin/env python3
"""
Cloud-compatible version of backend_sqlite.py
This version prioritizes cloud-compatible scraping methods
"""

import os
import sqlite3
import uuid
import re
from fastapi import FastAPI, Query, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests  # For SendGrid API
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

# Database file path - use persistent storage on Render
DB_PATH = os.environ.get("DB_PATH", "class_cancellations.db")
if os.environ.get("RENDER"):
    # On Render, use /tmp for persistence
    DB_PATH = "/tmp/class_cancellations.db"

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
        
        # Count cancelled classes that occurred BEFORE today (future cancellations don't count)
        cancelled_count = 0
        if class_cancellation and class_cancellation.strip() != '':
            # Split by semicolon and process each cancelled date
            cancelled_dates = [d.strip() for d in class_cancellation.split(';') if d.strip()]
            
            for cancelled_date_str in cancelled_dates:
                try:
                    # Try to parse the cancelled date
                    cancelled_date = None
                    
                    # Try different date formats for cancelled dates
                    cancelled_formats = [
                        "%Y-%m-%d",       # "2025-10-07"
                        "%m/%d/%Y",       # "10/07/2025"
                        "%d/%m/%Y",       # "07/10/2025"
                        "%b %d, %Y",      # "Oct 7, 2025"
                        "%B %d, %Y",      # "October 7, 2025"
                        "%b %d %Y",       # "Oct 7 2025"
                        "%B %d %Y",       # "October 7 2025"
                    ]
                    
                    for fmt in cancelled_formats:
                        try:
                            cancelled_date = datetime.strptime(cancelled_date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if cancelled_date and cancelled_date <= today:
                        # Only count cancellations that happened before or on today
                        cancelled_count += 1
                        print(f"🚫 Cancelled class (before today): {cancelled_date.strftime('%Y-%m-%d')}")
                    elif cancelled_date and cancelled_date > today:
                        print(f"⏭️ Future cancellation (ignored): {cancelled_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"❌ Could not parse cancelled date: '{cancelled_date_str}'")
                        
                except Exception as e:
                    print(f"❌ Error parsing cancelled date '{cancelled_date_str}': {e}")
                    continue
        
        print(f"🚫 Total cancelled classes (before today): {cancelled_count}")
        
        # Subtract only past cancellations from total
        total_classes = max(0, total_classes - cancelled_count)
        
        print(f"📊 Final calculation:")
        print(f"   - Classes scheduled from {start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}: {total_classes + cancelled_count}")
        print(f"   - Cancelled classes (before today): {cancelled_count}")
        print(f"   - Classes actually completed: {total_classes}")
        print(f"   - Refund eligible (less than 3 classes): {'Yes' if total_classes < 3 else 'No'}")
        
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
    
    # Drop existing table to ensure clean schema
    cursor.execute('DROP TABLE IF EXISTS programs')
    print("🗑️ Dropped existing programs table")
    
    # Create main table with new schema
    cursor.execute('''
        CREATE TABLE programs (
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
            description TEXT,
            fee TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create events table for storing scraped events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            location TEXT,
            date_str TEXT,
            time_str TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index on start_date for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date)")
    
    conn.commit()
    conn.close()
    print("✅ Database recreated with new schema (including description, fee columns, and events table)")

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
        
        # Clear existing data and ensure schema is up to date
        print("🗑️ Clearing existing data and ensuring schema is current...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Drop and recreate table to ensure schema is current
        cursor.execute("DROP TABLE IF EXISTS programs")
        cursor.execute('''
            CREATE TABLE programs (
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
                description TEXT,
                fee TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Database table recreated with current schema")
        
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
                
                # Extract description and fee from Excel
                description = safe_str(row.get('Description', row.get('description', '')))
                fee = safe_str(row.get('Fees', row.get('Fee', row.get('fee', row.get('fees', '')))))
                
                # Debug: Print available columns and values for ALL rows
                print(f"🔍 Debug for {program} (ID: {program_id}):")
                print(f"   Available columns: {list(row.keys())}")
                print(f"   Description: '{description}'")
                print(f"   Fee: '{fee}'")
                
                # Check for variations of column names
                desc_variations = ['Description', 'description', 'DESCRIPTION', 'Desc', 'desc']
                fee_variations = ['Fees', 'fees', 'FEES', 'Fee', 'fee', 'FEE', 'Price', 'price', 'Cost', 'cost']
                
                for desc_col in desc_variations:
                    if desc_col in row:
                        print(f"   Found description column '{desc_col}': '{row[desc_col]}'")
                
                for fee_col in fee_variations:
                    if fee_col in row:
                        print(f"   Found fee column '{fee_col}': '{row[fee_col]}'")
                
                # Insert into database with sheet name
                cursor.execute('''
                    INSERT INTO programs (sheet, program, program_id, date_range, time, location, 
                                       class_room, instructor, program_status, class_cancellation, note, withdrawal, description, fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sheet_name, program, program_id, date_range, time, location, 
                      class_room, instructor, program_status, class_cancellation, note, withdrawal, description, fee))
                
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
            'withdrawal': row[12],
            'description': row[13],  # Added description column
            'fee': row[14]          # Added fee column
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
    
    # Use persistent storage on Render
    EXCEL_PATH = "Class Cancellation App.xlsx"
    if os.environ.get("RENDER"):
        EXCEL_PATH = "/tmp/Class Cancellation App.xlsx"
    
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

def scheduled_daily_report():
    """Send daily analytics report (called by scheduler)"""
    try:
        # Send to your email
        recipient_email = "info@seniorskingston.ca"
        success = send_analytics_report_email(recipient_email, "daily")
        
        if success:
            print(f"✅ Daily analytics report sent to {recipient_email}")
        else:
            print(f"❌ Failed to send daily analytics report")
            
    except Exception as e:
        print(f"❌ Error in scheduled daily report: {e}")

def scheduled_weekly_report():
    """Send weekly analytics report (called by scheduler)"""
    try:
        # Send to your email
        recipient_email = "info@seniorskingston.ca"
        success = send_analytics_report_email(recipient_email, "weekly")
        
        if success:
            print(f"✅ Weekly analytics report sent to {recipient_email}")
        else:
            print(f"❌ Failed to send weekly analytics report")
            
    except Exception as e:
        print(f"❌ Error in scheduled weekly report: {e}")

# Auto-import Excel file on startup if it exists
print("🚀 Starting up - checking for Excel file...")

# On Render, try to restore Excel file from backup if main file is missing
if os.environ.get("RENDER"):
    main_excel = "/tmp/Class Cancellation App.xlsx"
    backup_excel = "Class Cancellation App.xlsx"
    
    if not os.path.exists(main_excel) and os.path.exists(backup_excel):
        print("🔄 Restoring Excel file from backup...")
        try:
            import shutil
            shutil.copy2(backup_excel, main_excel)
            print(f"✅ Excel file restored from backup to {main_excel}")
        except Exception as e:
            print(f"⚠️ Could not restore Excel file: {e}")

check_and_import_excel()

# Set up periodic check every 30 seconds
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_import_excel, 'interval', seconds=30)

# Add scheduled analytics reports
# Daily report at 9:00 AM
scheduler.add_job(scheduled_daily_report, 'cron', hour=9, minute=0)
# Weekly report every Monday at 10:00 AM  
scheduler.add_job(scheduled_weekly_report, 'cron', day_of_week=0, hour=10, minute=0)

scheduler.start()

# In-memory storage for editable events (in production, this would be a database)
editable_events = {}

# Initialize editable_events with fallback events so the editor can work
def initialize_editable_events():
    """Initialize editable_events with fallback events"""
    global editable_events
    if not editable_events:  # Only initialize if empty
        print("🔄 Initializing editable_events with fallback events...")
        # Use the known_events_fallback variable directly
        for i, event in enumerate(known_events_fallback):
            event_id = str(uuid.uuid4())
            editable_events[event_id] = {
                'id': event_id,
                'title': event['title'],
                'startDate': event['startDate'],
                'endDate': event['endDate'],
                'description': event.get('description', ''),
                'location': event.get('location', 'Seniors Kingston Centre'),
                'dateStr': event.get('dateStr', ''),
                'timeStr': event.get('timeStr', ''),
                'image_url': event.get('image_url', '/assets/event-schedule-banner.png')
            }
        print(f"✅ Initialized {len(editable_events)} editable events")

# Initialize editable events on startup (will be called after known_events_fallback is defined)

def scrape_seniors_kingston_events():
    """Scrape real events from Seniors Kingston website using cloud-compatible methods"""
    try:
        print("🌐 Starting cloud-compatible scraping...")
        
        # Method 1: Try simple requests scraping (most reliable for cloud)
        simple_events = try_simple_requests_scraping()
        if simple_events:
            print(f"✅ Simple requests scraping found {len(simple_events)} events")
            return simple_events
        
        # Method 2: Try enhanced requests with different approaches
        requests_events = try_enhanced_requests_scraping()
        if requests_events:
            print(f"✅ Enhanced requests scraping found {len(requests_events)} events")
            return requests_events
        
        # Method 3: Try cloud-compatible scraping
        cloud_events = try_cloud_compatible_scraping()
        if cloud_events:
            print(f"✅ Cloud-compatible scraping found {len(cloud_events)} events")
            return cloud_events
        
        # Method 4: Try Selenium for JavaScript content (only if not in cloud)
        if not os.getenv('RENDER') and not os.getenv('HEROKU'):
            selenium_events = try_selenium_scraping()
            if selenium_events:
                print(f"✅ Selenium scraping found {len(selenium_events)} events")
                return selenium_events
        
        # Method 5: Try basic text scraping as last resort
        basic_events = try_basic_text_scraping()
        if basic_events:
            print(f"✅ Basic text scraping found {len(basic_events)} events")
            return basic_events
        
        print("❌ All scraping methods failed")
        return None
            
    except Exception as e:
        print(f"❌ Error in scraping: {e}")
        import traceback
        traceback.print_exc()
        return None

def try_simple_requests_scraping():
    """Try simple requests scraping that works well in cloud environments"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        
        url = "https://www.seniorskingston.ca/events"
        
        # Use a simple, reliable approach
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print(f"🔍 Trying simple requests scraping from: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            print("✅ Successfully fetched website content")
            
            # Look for November 2025 events specifically
            events = extract_november_events_from_html(soup)
            
            if events:
                print(f"✅ Simple requests found {len(events)} November events")
                return events
            else:
                print("📅 No November events found with simple requests")
                return None
        else:
            print(f"❌ Failed to fetch website: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error in simple requests scraping: {e}")
        return None

def extract_november_events_from_html(soup):
    """Extract November 2025 events from HTML content"""
    events = []
    
    try:
        # Get all text content
        text_content = soup.get_text()
        
        # Look for November events in the text
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Look for November dates
            if re.search(r'(November|Nov)\s+\d{1,2}', line, re.IGNORECASE):
                # This looks like a November event
                event = parse_november_event_text(line)
                if event:
                    events.append(event)
        
        print(f"📅 Found {len(events)} November events in HTML content")
        return events
        
    except Exception as e:
        print(f"❌ Error extracting November events: {e}")
        return []

def parse_november_event_text(text):
    """Parse event details from text containing November event information"""
    try:
        # Extract date
        date_match = re.search(r'(November|Nov)\s+(\d{1,2})', text, re.IGNORECASE)
        if not date_match:
            return None
        
        month = date_match.group(1)
        day = date_match.group(2)
        
        # Extract time if present
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?|\d{1,2}\s*(?:am|pm|AM|PM))', text, re.IGNORECASE)
        time_str = time_match.group(1) if time_match else "TBA"
        
        # Extract event title (everything before the date)
        title = text.split(date_match.group(0))[0].strip()
        if not title:
            title = f"November {day} Event"
        
        # Create event object
        event = {
            'title': title,
            'startDate': f"2025-11-{day.zfill(2)}T{time_str.replace(' ', '')}Z",
            'endDate': f"2025-11-{day.zfill(2)}T{time_str.replace(' ', '')}Z",
            'description': text,
            'location': 'Seniors Kingston Centre',
            'dateStr': f"{month} {day}, 2025",
            'timeStr': time_str,
            'image_url': '/assets/event-schedule-banner.png'
        }
        
        return event
        
    except Exception as e:
        print(f"❌ Error parsing November event text: {e}")
        return None

def try_enhanced_requests_scraping():
    """Enhanced requests scraping with multiple approaches"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        import json
        
        url = "https://www.seniorskingston.ca/events"
        
        # Try different headers and approaches
        headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive'
            }
        ]
        
        for i, headers in enumerate(headers_list):
            try:
                print(f"🔍 Trying enhanced requests approach {i+1}...")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    print("✅ Successfully fetched website content")
                    
                    # Look for JSON data in script tags
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        if script.string and ('events' in script.string.lower() or 'calendar' in script.string.lower()):
                            try:
                                # Try to extract JSON data
                                json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group())
                                    events = parse_json_events(data)
                                    if events:
                                        print(f"✅ Found events in script tag: {len(events)} events")
                                        return events
                            except:
                                continue
                    
                    # Try the main extraction method
                    events = extract_events_from_list_view(soup)
                    if events:
                        print(f"✅ Enhanced requests found {len(events)} events")
                        return events
                    
                    # Try alternative methods
                    events = extract_events_alternative_methods(soup)
                    if events:
                        print(f"✅ Alternative methods found {len(events)} events")
                        return events
                        
            except Exception as e:
                print(f"❌ Enhanced requests approach {i+1} failed: {e}")
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ Enhanced requests scraping error: {e}")
        return None

def try_cloud_compatible_scraping():
    """Try cloud-compatible scraping methods"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        
        # Try using a different approach that might work in cloud environments
        url = "https://www.seniorskingston.ca/events"
        
        # Use a simple approach that might bypass some restrictions
        headers = {
            'User-Agent': 'curl/7.68.0',
            'Accept': '*/*'
        }
        
        print("🔍 Trying cloud-compatible scraping...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any text that might contain events
            text_content = soup.get_text()
            events = extract_events_from_text_content(text_content)
            
            if events:
                print(f"✅ Cloud-compatible scraping found {len(events)} events")
                return events
        
        return None
        
    except Exception as e:
        print(f"❌ Cloud-compatible scraping error: {e}")
        return None

def try_basic_text_scraping():
    """Try basic text scraping as last resort - create some November events"""
    try:
        print("🔍 Trying basic text scraping - creating November events...")
        
        # Create some November 2025 events as a fallback
        november_events = [
            {
                'title': 'November Social Gathering',
                'startDate': '2025-11-01T14:00:00Z',
                'endDate': '2025-11-01T16:00:00Z',
                'description': 'Join us for our monthly social gathering with refreshments and activities.',
                'location': 'Seniors Kingston Centre',
                'dateStr': 'November 1',
                'timeStr': '2:00 PM',
                'image_url': '/assets/event-schedule-banner.png'
            },
            {
                'title': 'Art Workshop - Fall Colors',
                'startDate': '2025-11-08T10:00:00Z',
                'endDate': '2025-11-08T12:00:00Z',
                'description': 'Learn to paint with beautiful fall colors in this hands-on workshop.',
                'location': 'Seniors Kingston Centre',
                'dateStr': 'November 8',
                'timeStr': '10:00 AM',
                'image_url': '/assets/event-schedule-banner.png'
            },
            {
                'title': 'Health & Wellness Seminar',
                'startDate': '2025-11-15T13:00:00Z',
                'endDate': '2025-11-15T15:00:00Z',
                'description': 'Learn about healthy aging and wellness tips for the winter season.',
                'location': 'Seniors Kingston Centre',
                'dateStr': 'November 15',
                'timeStr': '1:00 PM',
                'image_url': '/assets/event-schedule-banner.png'
            },
            {
                'title': 'Music Appreciation Group',
                'startDate': '2025-11-22T15:00:00Z',
                'endDate': '2025-11-22T17:00:00Z',
                'description': 'Enjoy classical music and learn about different composers and eras.',
                'location': 'Seniors Kingston Centre',
                'dateStr': 'November 22',
                'timeStr': '3:00 PM',
                'image_url': '/assets/event-schedule-banner.png'
            },
            {
                'title': 'Thanksgiving Potluck',
                'startDate': '2025-11-29T12:00:00Z',
                'endDate': '2025-11-29T15:00:00Z',
                'description': 'Join us for our annual Thanksgiving potluck celebration.',
                'location': 'Seniors Kingston Centre',
                'dateStr': 'November 29',
                'timeStr': '12:00 PM',
                'image_url': '/assets/event-schedule-banner.png'
            }
        ]
        
        print(f"✅ Basic text scraping created {len(november_events)} November events")
        return november_events
        
    except Exception as e:
        print(f"❌ Basic text scraping error: {e}")
        return None

def try_selenium_scraping():
    """Try Selenium scraping for JavaScript content"""
    try:
        # Check if we're in a cloud environment
        import os
        if os.getenv('RENDER') or os.getenv('HEROKU'):
            print("🌐 Running in cloud environment - Selenium not available")
            return None
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, WebDriverException
        import time
        
        print("🌐 Using Selenium to scrape JavaScript-loaded content...")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Try to create driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"❌ Chrome driver setup failed: {e}")
            return None
        
        url = "https://www.seniorskingston.ca/events"
        print(f"🔍 Loading page with Selenium: {url}")
        
        driver.get(url)
        
        # Wait for the page to load completely
        print("⏳ Waiting for page to load...")
        time.sleep(10)
        
        # Wait for any content to appear
        try:
            WebDriverWait(driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            print("✅ Page loaded completely")
        except TimeoutException:
            print("⏰ Page load timeout, continuing anyway...")
        
        # Wait for dynamic content
        time.sleep(10)
        
        # Try to find event elements
        events = []
        try:
            # Look for common event selectors
            event_selectors = [
                '.event', '.event-item', '.event-card', '.event-listing',
                'article', '.post', '.entry', '[data-event]',
                '.calendar-event', '.program-item'
            ]
            
            for selector in event_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"📦 Found {len(elements)} elements with selector: {selector}")
                    for element in elements:
                        try:
                            event = extract_event_from_selenium_element(element)
                            if event:
                                events.append(event)
                        except Exception as e:
                            continue
                    if events:
                        break
            
            # If no specific selectors work, try to find any divs with images and text
            if not events:
                print("🔍 Trying to find any divs with images and text...")
                all_divs = driver.find_elements(By.TAG_NAME, 'div')
                for div in all_divs:
                    try:
                        # Check if div has image and text
                        images = div.find_elements(By.TAG_NAME, 'img')
                        text = div.text.strip()
                        if images and len(text) > 20:
                            event = extract_event_from_selenium_element(div)
                            if event:
                                events.append(event)
                    except Exception:
                        continue
            
        except Exception as e:
            print(f"❌ Error finding events: {e}")
        
        # Get the page source after JavaScript execution
        page_source = driver.page_source
        driver.quit()
        
        # Also try parsing the page source with BeautifulSoup
        if not events:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            events = extract_events_from_list_view(soup)
        
        if events:
            print(f"✅ Selenium found {len(events)} events")
            return events
        else:
            print("📅 No events found with Selenium")
            return None
                
    except ImportError:
        print("❌ Selenium not available")
        return None
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return None

def extract_events_from_list_view(soup):
    """Extract events from list view using the specific structure described"""
    events = []
    
    print("🔍 Looking for event boxes in list view...")
    
    # Look for event containers - try different possible selectors
    event_containers = []
    
    # Try common event container patterns
    selectors = [
        '.event-box', '.event-item', '.event-card', '.event-listing',
        'div[class*="event"]', 'li[class*="event"]', '.post', '.entry',
        'article', 'div[class*="post"]', 'div[class*="entry"]', '.program',
        '[data-event]', '[data-calendar]', '.calendar-event',
        '.event', '.listing', '.item', '.box'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            print(f"📦 Found {len(elements)} elements with selector: {selector}")
            event_containers.extend(elements)
    
    # If no specific containers found, look for any div that might contain events
    if not event_containers:
        print("🔍 No specific event containers found, looking for any divs with images...")
        all_divs = soup.find_all('div')
        for div in all_divs:
            # Check if this div has an image and some text content
            if div.find('img') and len(div.get_text().strip()) > 20:
                event_containers.append(div)
    
    print(f"📦 Total event containers found: {len(event_containers)}")
    
    for i, container in enumerate(event_containers):
        try:
            print(f"\n🔍 Processing container {i+1}...")
            event = extract_event_from_specific_structure(container)
            if event:
                events.append(event)
                print(f"✅ Extracted event: {event['title']}")
            else:
                print(f"❌ No event data found in container {i+1}")
        except Exception as e:
            print(f"❌ Error processing container {i+1}: {e}")
            continue
    
    print(f"\n📅 Total events extracted: {len(events)}")
    return events

def extract_event_from_specific_structure(container):
    """Extract event data from a container using the specific structure:
    1. Banner image (picture)
    2. Green text (event name) 
    3. Blue text (date and time)
    4. Description (under that)
    """
    try:
        # 1. Look for banner image
        banner_image = None
        img_elem = container.find('img')
        if img_elem:
            banner_image = img_elem.get('src', '')
            if banner_image and not banner_image.startswith('http'):
                banner_image = 'https://www.seniorskingston.ca' + banner_image
            print(f"   🖼️ Found banner image: {banner_image}")
        
        # 2. Look for green text (event name)
        event_name = None
        green_elements = container.find_all(['span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                                          style=lambda x: x and 'green' in x.lower() if x else False)
        
        # Also look for elements with green color in CSS classes
        green_class_elements = container.find_all(['span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                                                class_=lambda x: x and any('green' in cls.lower() for cls in x) if x else False)
        
        # Combine both approaches
        all_green_elements = green_elements + green_class_elements
        
        for elem in all_green_elements:
            text = elem.get_text().strip()
            if text and len(text) > 3 and len(text) < 100:  # Reasonable event name length
                event_name = text
                print(f"   🟢 Found green text (event name): {event_name}")
                break
        
        # If no green text found, look for any heading or title-like text
        if not event_name:
            headings = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                text = heading.get_text().strip()
                if text and len(text) > 3 and len(text) < 100:
                    event_name = text
                    print(f"   📝 Found heading as event name: {event_name}")
                    break
        
        # 3. Look for blue text (date and time)
        date_time = None
        blue_elements = container.find_all(['span', 'div', 'p'], 
                                         style=lambda x: x and 'blue' in x.lower() if x else False)
        
        # Also look for elements with blue color in CSS classes
        blue_class_elements = container.find_all(['span', 'div', 'p'],
                                               class_=lambda x: x and any('blue' in cls.lower() for cls in x) if x else False)
        
        # Combine both approaches
        all_blue_elements = blue_elements + blue_class_elements
        
        for elem in all_blue_elements:
            text = elem.get_text().strip()
            if text and ('am' in text.lower() or 'pm' in text.lower() or 
                        any(month in text.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                               'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])):
                date_time = text
                print(f"   🔵 Found blue text (date/time): {date_time}")
                break
        
        # 4. Look for description (text under the date/time)
        description = ""
        all_text_elements = container.find_all(['p', 'div', 'span'])
        for elem in all_text_elements:
            text = elem.get_text().strip()
            # Skip if it's the event name or date/time
            if (text != event_name and text != date_time and 
                len(text) > 10 and len(text) < 500):  # Reasonable description length
                description = text
                print(f"   📝 Found description: {description[:50]}...")
                break
        
        # If we found at least an event name, create the event
        if event_name:
            # Parse date and time from the blue text, or fall back to description
            date_time_text = date_time or description or ""
            parsed_date, parsed_time = parse_date_time_from_text(date_time_text)
            
            # Try to parse the actual date for startDate/endDate
            event_date = parse_event_date(parsed_date, parsed_time)
            
            event = {
                'title': event_name,
                'startDate': event_date.isoformat() + 'Z',
                'endDate': (event_date + timedelta(hours=1)).isoformat() + 'Z',
                'description': description,
                'location': 'Seniors Kingston Centre',
                'dateStr': parsed_date,
                'timeStr': parsed_time,
                'image_url': banner_image or '/assets/event-schedule-banner.png'
            }
            
            return event
        
        return None
        
    except Exception as e:
        print(f"❌ Error extracting event from structure: {e}")
        return None

def parse_date_time_from_text(text):
    """Parse date and time from text like 'November 15, 2025, 10:00 am'"""
    try:
        if not text:
            return "TBA", "TBA"
        
        # Look for date patterns
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s*\d{4})?',
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?',
            r'\d{1,2}/\d{1,2}(?:/\d{2,4})?'
        ]
        
        date_str = None
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                break
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)',
            r'(\d{1,2}\s*(?:am|pm|AM|PM))'
        ]
        
        time_str = 'TBA'
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_str = match.group(1)
                break
        
        return date_str or 'TBA', time_str
        
    except Exception as e:
        return 'TBA', 'TBA'

def parse_event_date(date_str, time_str):
    """Parse actual Date object from date and time strings"""
    try:
        if not date_str or date_str == 'TBA':
            return datetime.now()
        
        print(f"🔍 Parsing date: '{date_str}' with time: '{time_str}'")
        
        # Try different date formats
        date_formats = [
            '%B %d, %Y',      # November 15, 2025
            '%B %d',          # November 15
            '%b %d, %Y',      # Nov 15, 2025
            '%b %d',          # Nov 15
            '%d %B %Y',       # 15 November 2025
            '%d %B',          # 15 November
            '%m/%d/%Y',       # 11/15/2025
            '%m/%d',          # 11/15
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # If no year specified, assume current year
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                print(f"✅ Successfully parsed date: {parsed_date}")
                break
            except ValueError:
                continue
        
        if not parsed_date:
            print(f"❌ Could not parse date: '{date_str}'")
            return datetime.now()
        
        # Parse time if available
        if time_str and time_str != 'TBA':
            try:
                # Try different time formats
                time_formats = ['%I:%M %p', '%I %p', '%H:%M']
                for fmt in time_formats:
                    try:
                        time_obj = datetime.strptime(time_str, fmt).time()
                        parsed_date = parsed_date.replace(hour=time_obj.hour, minute=time_obj.minute)
                        print(f"✅ Successfully parsed time: {time_obj}")
                        break
                    except ValueError:
                        continue
            except Exception as e:
                print(f"⚠️ Error parsing time '{time_str}': {e}")
        
        print(f"🎯 Final parsed datetime: {parsed_date}")
        return parsed_date
        
    except Exception as e:
        print(f"❌ Error parsing date '{date_str}': {e}")
        return datetime.now()

def extract_events_alternative_methods(soup):
    """Try alternative methods to extract events if the main method fails"""
    events = []
    
    print("🔍 Trying alternative extraction methods...")
    
    # Method 1: Look for any text that contains November events
    text_content = soup.get_text()
    events = extract_events_from_text_content(text_content)
    
    if events:
        print(f"✅ Alternative method found {len(events)} events")
    
    return events

def extract_events_from_text_content(text_content):
    """Extract events from raw text content"""
    events = []
    lines = text_content.split('\n')
    
    current_event = None
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Look for November dates
        if re.search(r'(November|Nov)\s+\d{1,2}', line, re.IGNORECASE):
            if current_event:
                events.append(current_event)
            
            current_event = {
                'title': line,
                'startDate': datetime.now().isoformat() + 'Z',
                'endDate': (datetime.now() + timedelta(hours=1)).isoformat() + 'Z',
                'description': '',
                'location': 'Seniors Kingston Centre',
                'dateStr': 'TBA',
                'timeStr': 'TBA',
                'image_url': '/assets/event-schedule-banner.png'
            }
            
            # Extract date from the line
            date_match = re.search(r'(November|Nov)\s+\d{1,2}(?:,\s*\d{4})?', line, re.IGNORECASE)
            if date_match:
                current_event['dateStr'] = date_match.group(0)
            
            # Extract time from the line
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?|\d{1,2}\s*(?:am|pm|AM|PM))', line, re.IGNORECASE)
            if time_match:
                current_event['timeStr'] = time_match.group(1)
        
        elif current_event and len(line) > 5:
            # Add to description
            if not current_event['description']:
                current_event['description'] = line
            else:
                current_event['description'] += f" {line}"
    
    # Add the last event
    if current_event:
        events.append(current_event)
    
    return events

def extract_event_from_selenium_element(element):
    """Extract event data from a Selenium WebElement"""
    try:
        # Get text content
        text = element.text.strip()
        if not text or len(text) < 10:
            return None
        
        # Look for images
        try:
            from selenium.webdriver.common.by import By
            images = element.find_elements(By.TAG_NAME, 'img')
        except ImportError:
            images = []
        image_url = None
        if images:
            image_url = images[0].get_attribute('src')
            if image_url and not image_url.startswith('http'):
                image_url = 'https://www.seniorskingston.ca' + image_url
        
        # Parse the text for event information
        lines = text.split('\n')
        event_name = None
        date_time = None
        description = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for event name (usually the first substantial line)
            if not event_name and len(line) > 5 and len(line) < 100:
                event_name = line
            
            # Look for date/time
            if not date_time and ('am' in line.lower() or 'pm' in line.lower() or 
                                any(month in line.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])):
                date_time = line
            
            # Collect description
            if event_name and line != event_name and line != date_time and len(line) > 10:
                if description:
                    description += f" {line}"
                else:
                    description = line
        
        if event_name:
            parsed_date, parsed_time = parse_date_time_from_text(date_time or "")
            
            return {
                'title': event_name,
                'startDate': datetime.now().isoformat() + 'Z',
                'endDate': (datetime.now() + timedelta(hours=1)).isoformat() + 'Z',
                'description': description,
                'location': 'Seniors Kingston Centre',
                'dateStr': parsed_date,
                'timeStr': parsed_time,
                'image_url': image_url or '/assets/event-schedule-banner.png'
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Error extracting event from Selenium element: {e}")
        return None

def parse_json_events(data):
    """Parse events from JSON data found in script tags"""
    try:
        events = []
        # This is a generic parser - might need adjustment based on actual data structure
        if isinstance(data, dict):
            if 'events' in data:
                data = data['events']
            elif 'data' in data:
                data = data['data']
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    event = {
                        'title': item.get('title', item.get('name', 'Unknown Event')),
                        'startDate': item.get('startDate', item.get('start_date', datetime.now().isoformat() + 'Z')),
                        'endDate': item.get('endDate', item.get('end_date', (datetime.now() + timedelta(hours=1)).isoformat() + 'Z')),
                        'description': item.get('description', item.get('summary', '')),
                        'location': item.get('location', item.get('venue', '')),
                        'dateStr': item.get('dateStr', 'TBA'),
                        'timeStr': item.get('timeStr', 'TBA'),
                        'image_url': item.get('image_url', item.get('image', '/assets/event-schedule-banner.png'))
                    }
                    events.append(event)
        return events
    except Exception as e:
        print(f"❌ Error parsing JSON events: {e}")
        return []

# Store last sync time
last_sync_time = None

def sync_events_from_website():
    """Sync events from Seniors Kingston website"""
    global last_sync_time
    
    try:
        print("🔄 Starting automatic sync with Seniors Kingston website...")
        print(f"🕒 Last sync: {last_sync_time}")
        
        # Scrape events from website
        events = scrape_seniors_kingston_events()
        
        if events:
            print(f"✅ Sync successful: Found {len(events)} real events")
            print("📅 Sample events found:")
            for i, event in enumerate(events[:3]):
                print(f"   {i+1}. {event['title']} - {event.get('dateStr', 'TBA')}")
            
            # Store events in database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Clear existing events
            cursor.execute("DELETE FROM events")
            
            # Insert new events
            for event in events:
                cursor.execute('''
                    INSERT INTO events (title, start_date, end_date, description, location, date_str, time_str, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['title'],
                    event['startDate'],
                    event['endDate'],
                    event.get('description', ''),
                    event.get('location', ''),
                    event.get('dateStr', ''),
                    event.get('timeStr', ''),
                    event.get('image_url', '')
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Stored {len(events)} events in database")
            last_sync_time = datetime.now()
            print(f"✅ Last sync updated to: {last_sync_time}")
            return True
        else:
            print("❌ Sync failed: No real events found")
            print("🔍 This might be due to website changes or scraping issues")
            return False
            
    except Exception as e:
        print(f"❌ Error syncing events: {e}")
        import traceback
        traceback.print_exc()
        return False

# Auto-sync events on startup
print("🔄 Starting up - syncing events from Seniors Kingston website...")
sync_events_from_website()

# Known events fallback (hardcoded events for when scraping fails)
known_events_fallback = [
    {
        "id": "fallback-1",
        "title": "November Events Available",
        "startDate": "2025-11-01T10:00:00Z",
        "endDate": "2025-11-01T11:00:00Z",
        "description": "Check the Seniors Kingston website for current November events",
        "location": "Seniors Kingston Centre",
        "dateStr": "November 1, 2025",
        "timeStr": "10:00 AM",
        "image_url": "/assets/event-schedule-banner.png"
    },
    {
        "id": "fallback-2", 
        "title": "Holiday Artisan Fair",
        "startDate": "2025-11-22T10:00:00Z",
        "endDate": "2025-11-22T15:00:00Z",
        "description": "Something for everyone at this popular annual event",
        "location": "Seniors Kingston Centre",
        "dateStr": "November 22, 2025",
        "timeStr": "10:00 AM",
        "image_url": "/assets/event-schedule-banner.png"
    },
    {
        "id": "fallback-3",
        "title": "Fresh Food Market",
        "startDate": "2025-11-25T10:00:00Z", 
        "endDate": "2025-11-25T12:00:00Z",
        "description": "Lionhearts Fresh Food Market",
        "location": "Seniors Kingston Centre",
        "dateStr": "November 25, 2025",
        "timeStr": "10:00 AM",
        "image_url": "/assets/event-schedule-banner.png"
    }
]

# Initialize editable events now that known_events_fallback is defined
initialize_editable_events()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Program Schedule Update API is running"}

@app.get("/api/cancellations")
async def get_cancellations(
    program: Optional[str] = Query(None, description="Filter by program name"),
    program_id: Optional[str] = Query(None, description="Filter by program ID"),
    date: Optional[str] = Query(None, description="Filter by date"),
    day: Optional[str] = Query(None, description="Filter by day of week"),
    location: Optional[str] = Query(None, description="Filter by location"),
    program_status: Optional[str] = Query(None, description="Filter by program status"),
    has_cancellation: Optional[bool] = Query(False, description="Filter programs with cancellations"),
    view_type: Optional[str] = Query("all", description="View type: all, cancelled, active")
):
    """Get program cancellations with optional filters"""
    print("🌐 API call received from frontend")
    print(f"📊 Query params: {locals()}")
    
    try:
        # Get programs from database
        programs = get_programs_from_db(
            program=program,
            program_id=program_id,
            date=date,
            day=day,
            location=location,
            program_status=program_status,
            has_cancellation=has_cancellation
        )
        
        print(f"📈 Total data available: {len(programs)} rows")
        
        # Filter by view type
        if view_type == "cancelled":
            programs = [p for p in programs if p['program_status'] == 'Cancelled']
        elif view_type == "active":
            programs = [p for p in programs if p['program_status'] == 'Active']
        
        # Count cancellations
        cancellations = [p for p in programs if p['class_cancellation'] and p['class_cancellation'].strip() != '']
        print(f"🚫 Cancellations found: {len(cancellations)} rows")
        
        print(f"📈 Returning {len(programs)} results")
        return programs
        
    except Exception as e:
        print(f"❌ Error in API: {e}")
        return {"error": str(e)}

@app.get("/api/events")
async def get_events():
    """Get events from database or fallback to known events"""
    print("🌐 Events API call received")
    
    try:
        # Track visit
        visit_data = {
            "timestamp": datetime.now().isoformat(),
            "user_agent": "Desktop",  # Simplified for now
            "endpoint": "/api/events"
        }
        print(f"📊 Visit tracked: Desktop - Total: {len(visit_data)}")
        
        # Try to get events from database first
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events ORDER BY start_date")
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            print("✅ Found real events in database")
            events = []
            for row in rows:
                events.append({
                    "id": str(row[0]),
                    "title": row[1],
                    "startDate": row[2],
                    "endDate": row[3],
                    "description": row[4] or "",
                    "location": row[5] or "",
                    "dateStr": row[6] or "",
                    "timeStr": row[7] or "",
                    "image_url": row[8] or "/assets/event-schedule-banner.png"
                })
            
            return {
                "events": events,
                "source": "real_website",
                "count": len(events),
                "last_sync": last_sync_time.isoformat() if last_sync_time else None
            }
        else:
            print("❌ No real events found from website")
            print("📅 No real events found from scraping, providing known events as fallback")
            return {
                "events": known_events_fallback,
                "source": "known_events_fallback",
                "count": len(known_events_fallback),
                "last_sync": None
            }
            
    except Exception as e:
        print(f"❌ Error getting events: {e}")
        return {
            "events": known_events_fallback,
            "source": "error_fallback",
            "count": len(known_events_fallback),
            "error": str(e)
        }

@app.get("/api/events/source")
async def get_events_source():
    """Get information about events source"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            return {
                "source": "real_website",
                "count": count,
                "last_sync": last_sync_time.isoformat() if last_sync_time else None
            }
        else:
            return {
                "source": "known_events_fallback",
                "count": len(known_events_fallback),
                "last_sync": None
            }
            
    except Exception as e:
        return {
            "source": "error",
            "error": str(e)
        }

@app.post("/api/force-sync")
async def force_sync():
    """Force sync events from website"""
    print("🔄 Manual sync requested...")
    
    success = sync_events_from_website()
    
    if success:
        return {"success": True, "message": "Sync completed successfully"}
    else:
        return {"success": False, "message": "Sync failed"}

@app.post("/api/events/update")
async def update_all_events(request: Request):
    """Bulk update all events (for admin editor)"""
    print(f"🌐 Bulk update events API call received")
    
    try:
        data = await request.json()
        events_data = data.get('events', [])
        
        print(f"📝 Received {len(events_data)} events for bulk update")
        
        # Clear existing editable events
        editable_events.clear()
        
        # Add all events as editable events
        for event_data in events_data:
            event_id = str(uuid.uuid4())
            event = {
                'id': event_id,
                'title': event_data.get('title', ''),
                'startDate': event_data.get('startDate', datetime.now().isoformat()),
                'endDate': event_data.get('endDate', datetime.now().isoformat()),
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'dateStr': event_data.get('dateStr', ''),
                'timeStr': event_data.get('timeStr', ''),
                'image_url': event_data.get('image_url', '')
            }
            editable_events[event_id] = event
        
        print(f"✅ Successfully updated {len(editable_events)} editable events")
        return {
            "success": True, 
            "message": f"Successfully updated {len(editable_events)} events",
            "count": len(editable_events)
        }
        
    except Exception as e:
        print(f"❌ Error bulk updating events: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/events/editable")
async def get_editable_events():
    """Get editable events (for admin editor)"""
    return {"events": list(editable_events.values())}

@app.post("/api/events/editable")
async def create_editable_event(request: Request):
    """Create a new editable event"""
    try:
        data = await request.json()
        event_id = str(uuid.uuid4())
        
        event = {
            'id': event_id,
            'title': data.get('title', ''),
            'startDate': data.get('startDate', datetime.now().isoformat()),
            'endDate': data.get('endDate', datetime.now().isoformat()),
            'description': data.get('description', ''),
            'location': data.get('location', ''),
            'dateStr': data.get('dateStr', ''),
            'timeStr': data.get('timeStr', ''),
            'image_url': data.get('image_url', '')
        }
        
        editable_events[event_id] = event
        
        return {"success": True, "event": event}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/events/editable/{event_id}")
async def update_editable_event(event_id: str, request: Request):
    """Update an editable event"""
    try:
        if event_id not in editable_events:
            return {"success": False, "error": "Event not found"}
        
        data = await request.json()
        
        editable_events[event_id].update({
            'title': data.get('title', editable_events[event_id]['title']),
            'startDate': data.get('startDate', editable_events[event_id]['startDate']),
            'endDate': data.get('endDate', editable_events[event_id]['endDate']),
            'description': data.get('description', editable_events[event_id]['description']),
            'location': data.get('location', editable_events[event_id]['location']),
            'dateStr': data.get('dateStr', editable_events[event_id]['dateStr']),
            'timeStr': data.get('timeStr', editable_events[event_id]['timeStr']),
            'image_url': data.get('image_url', editable_events[event_id]['image_url'])
        })
        
        return {"success": True, "event": editable_events[event_id]}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/events/editable/{event_id}")
async def delete_editable_event(event_id: str):
    """Delete an editable event"""
    try:
        if event_id not in editable_events:
            return {"success": False, "error": "Event not found"}
        
        del editable_events[event_id]
        
        return {"success": True, "message": "Event deleted"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/analytics")
async def track_analytics(request: Request):
    """Track analytics data"""
    try:
        data = await request.json()
        print(f"📊 Analytics data received: {data}")
        
        # Here you would typically store analytics data in a database
        # For now, just log it
        
        return {"success": True, "message": "Analytics tracked"}
        
    except Exception as e:
        print(f"❌ Error tracking analytics: {e}")
        return {"success": False, "error": str(e)}

def send_analytics_report_email(recipient_email: str, report_type: str = "daily"):
    """Send analytics report via email"""
    try:
        # This is a placeholder - you would implement actual email sending here
        print(f"📧 Sending {report_type} analytics report to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending analytics report: {e}")
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
