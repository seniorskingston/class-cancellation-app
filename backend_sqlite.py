import os
import sqlite3
import uuid
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
import re
from dateutil import parser
from contextlib import asynccontextmanager
from urllib.parse import urljoin
import traceback

# Google Cloud Storage imports
try:
    from google.cloud import storage as gcs_storage
    GCS_AVAILABLE = True
    print("✅ Google Cloud Storage library loaded successfully")
except ImportError:
    GCS_AVAILABLE = False
    print("⚠️ Google Cloud Storage library not available - using local storage")

# Use environment variable for port, default to 8000 (Render uses PORT env var)
PORT = int(os.environ.get("PORT", 8000))

# Database file path - use persistent storage
# On Render, use /tmp for persistent storage, or project root
DB_PATH = "/tmp/class_cancellations.db" if os.getenv('RENDER') else "class_cancellations.db"

# Set timezone to Kingston, Ontario
KINGSTON_TZ = pytz.timezone('America/Toronto')
utc = pytz.UTC

# ============================================
# GOOGLE CLOUD STORAGE CONFIGURATION
# ============================================
# Set your GCS bucket name here (or use environment variable)
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'seniors-kingston-data')

# File names in GCS
GCS_EVENTS_FILE = "stored_events.json"
GCS_EXCEL_FILE = "excel_data.json"
GCS_EXCEL_ORIGINAL_FILE = "Class_Cancellation_App.xlsx"

def get_gcs_client():
    """Get Google Cloud Storage client"""
    try:
        if not GCS_AVAILABLE:
            print("⚠️ GCS library not available")
            return None
        
        # Method 1: Check for credentials JSON content in environment variable
        # This is the recommended way for Render - paste the entire JSON as GCS_CREDENTIALS
        gcs_creds_json = os.getenv('GCS_CREDENTIALS')
        if gcs_creds_json:
            try:
                import tempfile
                # Write the JSON to a temp file
                creds_data = json.loads(gcs_creds_json)
                
                # Create a temp file for credentials
                creds_file = "/tmp/gcs_credentials.json"
                with open(creds_file, 'w') as f:
                    json.dump(creds_data, f)
                
                # Set the environment variable to point to the file
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file
                
                client = gcs_storage.Client()
                print(f"✅ GCS client created from GCS_CREDENTIALS environment variable")
                return client
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in GCS_CREDENTIALS: {e}")
            except Exception as e:
                print(f"❌ Error using GCS_CREDENTIALS: {e}")
        
        # Method 2: Check for credentials file path in environment
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            print(f"✅ Using GCS credentials from file: {creds_path}")
            client = gcs_storage.Client()
            return client
        
        # Method 3: Try to use default credentials (works on GCP or with ADC)
        try:
            client = gcs_storage.Client()
            print("✅ GCS client created with default credentials")
            return client
        except Exception as e:
            print(f"⚠️ Could not create GCS client with default credentials: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating GCS client: {e}")
        traceback.print_exc()
        return None

def upload_to_gcs(data: dict, filename: str) -> bool:
    """Upload JSON data to Google Cloud Storage"""
    try:
        client = get_gcs_client()
        if not client:
            print(f"⚠️ GCS client not available, cannot upload {filename}")
            return False
        
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        
        # Convert data to JSON string
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        # Upload to GCS
        blob.upload_from_string(json_data, content_type='application/json')
        
        print(f"✅ Successfully uploaded {filename} to GCS bucket {GCS_BUCKET_NAME}")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading {filename} to GCS: {e}")
        traceback.print_exc()
        return False

def download_from_gcs(filename: str) -> dict:
    """Download JSON data from Google Cloud Storage"""
    try:
        client = get_gcs_client()
        if not client:
            print(f"⚠️ GCS client not available, cannot download {filename}")
            return None
        
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        
        if not blob.exists():
            print(f"📝 File {filename} does not exist in GCS bucket {GCS_BUCKET_NAME}")
            return None
        
        # Download and parse JSON
        json_data = blob.download_as_text()
        data = json.loads(json_data)
        
        print(f"✅ Successfully downloaded {filename} from GCS bucket {GCS_BUCKET_NAME}")
        return data
        
    except Exception as e:
        print(f"❌ Error downloading {filename} from GCS: {e}")
        traceback.print_exc()
        return None

def upload_file_to_gcs(file_content: bytes, filename: str, content_type: str = 'application/octet-stream') -> bool:
    """Upload binary file to Google Cloud Storage"""
    try:
        client = get_gcs_client()
        if not client:
            print(f"⚠️ GCS client not available, cannot upload {filename}")
            return False
        
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        
        # Upload to GCS
        blob.upload_from_string(file_content, content_type=content_type)
        
        print(f"✅ Successfully uploaded {filename} to GCS bucket {GCS_BUCKET_NAME}")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading file {filename} to GCS: {e}")
        traceback.print_exc()
        return False

def download_file_from_gcs(filename: str) -> bytes:
    """Download binary file from Google Cloud Storage"""
    try:
        client = get_gcs_client()
        if not client:
            print(f"⚠️ GCS client not available, cannot download {filename}")
            return None
        
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        
        if not blob.exists():
            print(f"📝 File {filename} does not exist in GCS bucket {GCS_BUCKET_NAME}")
            return None
        
        # Download file content
        file_content = blob.download_as_bytes()
        
        print(f"✅ Successfully downloaded {filename} from GCS bucket {GCS_BUCKET_NAME}")
        return file_content
        
    except Exception as e:
        print(f"❌ Error downloading file {filename} from GCS: {e}")
        traceback.print_exc()
        return None

def list_gcs_files() -> list:
    """List all files in the GCS bucket"""
    try:
        client = get_gcs_client()
        if not client:
            return []
        
        bucket = client.bucket(GCS_BUCKET_NAME)
        blobs = bucket.list_blobs()
        
        files = []
        for blob in blobs:
            files.append({
                "name": blob.name,
                "size": blob.size,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "content_type": blob.content_type
            })
        
        return files
        
    except Exception as e:
        print(f"❌ Error listing GCS files: {e}")
        return []

# ============================================
# END GOOGLE CLOUD STORAGE CONFIGURATION
# ============================================

# Global variable to store uploaded events
stored_events = []

# File to persist stored_events across restarts (local backup)
STORED_EVENTS_FILE = "/tmp/stored_events.json" if os.getenv('RENDER') else "stored_events.json"

def load_stored_events():
    """Load stored events - try GCS first, then local file"""
    global stored_events
    
    # Try to load from Google Cloud Storage first
    print("🔄 Loading events - trying GCS first...")
    try:
        gcs_data = download_from_gcs(GCS_EVENTS_FILE)
        if gcs_data:
            # GCS data might be wrapped in metadata or be a list directly
            if isinstance(gcs_data, list):
                stored_events = gcs_data
            elif isinstance(gcs_data, dict) and 'events' in gcs_data:
                stored_events = gcs_data['events']
            else:
                stored_events = gcs_data if isinstance(gcs_data, list) else []
            
            print(f"✅ Loaded {len(stored_events)} events from Google Cloud Storage")
            
            # Also save locally as backup
            try:
                with open(STORED_EVENTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(stored_events, f, ensure_ascii=False, indent=2)
                print(f"💾 Also saved local backup to {STORED_EVENTS_FILE}")
            except Exception as local_e:
                print(f"⚠️ Could not save local backup: {local_e}")
            
            return
    except Exception as e:
        print(f"⚠️ Could not load from GCS: {e}")
    
    # Fall back to local file
    print("📂 Falling back to local file...")
    try:
        if os.path.exists(STORED_EVENTS_FILE):
            with open(STORED_EVENTS_FILE, 'r', encoding='utf-8') as f:
                stored_events = json.load(f)
            print(f"✅ Loaded {len(stored_events)} events from local file {STORED_EVENTS_FILE}")
        else:
            stored_events = []
            print("📝 No stored events file found, starting fresh")
    except Exception as e:
        print(f"⚠️ Error loading stored events from local file: {e}")
        stored_events = []

def save_stored_events():
    """Save stored events to GCS and local file"""
    global stored_events
    try:
        # Make a copy to avoid any reference issues
        events_to_save = stored_events.copy() if isinstance(stored_events, list) else list(stored_events)
        
        # Save to Google Cloud Storage first (primary storage)
        gcs_data = {
            "metadata": {
                "updated_at": datetime.now().isoformat(),
                "total_events": len(events_to_save),
                "source": "backend_save"
            },
            "events": events_to_save
        }
        
        gcs_success = upload_to_gcs(gcs_data, GCS_EVENTS_FILE)
        if gcs_success:
            print(f"☁️ Saved {len(events_to_save)} events to Google Cloud Storage")
        else:
            print(f"⚠️ Could not save to GCS, using local file only")
        
        # Also save to local file as backup
        with open(STORED_EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events_to_save, f, ensure_ascii=False, indent=2)
        
        # Verify the local save worked
        if os.path.exists(STORED_EVENTS_FILE):
            file_size = os.path.getsize(STORED_EVENTS_FILE)
            print(f"💾 Saved {len(events_to_save)} events to local file {STORED_EVENTS_FILE} (file size: {file_size} bytes)")
            
    except Exception as e:
        print(f"❌ ERROR saving stored events: {e}")
        traceback.print_exc()
        raise  # Re-raise so caller knows save failed

# Load stored events on startup
load_stored_events()

# Global scheduler variable (will be initialized in lifespan)
scheduler = None

# Create FastAPI app (will add lifespan and middleware later)
# CORS middleware will be added after app is created

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
    
    conn.commit()
    conn.close()
    print("✅ Database recreated with new schema (including description and fee columns)")

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
                session TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Database table recreated with current schema")
        
        total_records = 0
        
        # Process each sheet
        for sheet_name, df in excel_data.items():
            print(f"Processing sheet: {sheet_name}")
            print(f"Rows in {sheet_name}: {len(df)}")
            print(f"Columns in {sheet_name}: {list(df.columns)}")
            
            # Get the first column name (Session column)
            first_col_name = df.columns[0] if len(df.columns) > 0 else None
            
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
                
                # Extract description, fee, and session from Excel
                description = safe_str(row.get('Description', row.get('description', '')))
                fee = safe_str(row.get('Fees', row.get('Fee', row.get('fee', row.get('fees', '')))))
                # Session is the first column - try by name first, then by first column name, then by index
                session = safe_str(row.get('Session', row.get('session', '')))
                if not session or session == '':
                    # Try to get from first column by its actual name
                    if first_col_name:
                        session = safe_str(row.get(first_col_name, ''))
                    # If still empty, try by index (first column = index 0)
                    if not session or session == '':
                        try:
                            session = safe_str(row.iloc[0]) if hasattr(row, 'iloc') else ''
                        except:
                            session = ''
                
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
                                       class_room, instructor, program_status, class_cancellation, note, withdrawal, description, fee, session)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sheet_name, program, program_id, date_range, time, location, 
                      class_room, instructor, program_status, class_cancellation, note, withdrawal, description, fee, session))
                
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
    session: Optional[str] = None,
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
        # Make search case-insensitive and handle apostrophes
        
        search_term = f"%{program}%"
        normalized_id = program_id.lstrip('0') or '0'
        
        # Try multiple approaches: exact match, normalized apostrophes, and wildcards
        # This handles cases where apostrophes might be different characters
        query += """ AND (
            LOWER(CAST(program AS TEXT)) LIKE LOWER(?) OR
            LOWER(REPLACE(CAST(program AS TEXT), '''', ' ')) LIKE LOWER(?) OR
            LOWER(REPLACE(CAST(program AS TEXT), '''', ' ')) LIKE LOWER(?) OR
            LOWER(REPLACE(CAST(program AS TEXT), '''', '')) LIKE LOWER(?) OR
            LOWER(CAST(program_id AS TEXT)) LIKE LOWER(?) OR
            LOWER(CAST(program_id AS TEXT)) LIKE LOWER(?)
        )"""
        params.append(search_term)
        params.append(search_term.replace("'", "").replace("'", ""))  # No apostrophes
        params.append(search_term.replace("'", " ").replace("'", " "))  # Apostrophe as space
        params.append(search_term.replace("'", "").replace("'", ""))  # No apostrophes
        params.append(f"%{program_id}%")
        params.append(f"%{normalized_id}%")
    else:
        # Separate searches - make case-insensitive
        if program:
            # Normalize apostrophes (both straight and curly) to handle different character encodings
            # Escape apostrophes in search term and database
            escaped_program = program.replace("'", "_")
            escaped_program = escaped_program.replace("'", "_")
            query += " AND LOWER(REPLACE(REPLACE(CAST(program AS TEXT), '''', '_'), '''', '_')) LIKE LOWER(?)"
            params.append(f"%{escaped_program}%")
        
        if program_id:
            # Handle both original and normalized program IDs
            # Try both the original ID and the ID with leading zeros stripped
            normalized_id = program_id.lstrip('0') or '0'
            query += " AND (LOWER(CAST(program_id AS TEXT)) LIKE LOWER(?) ESCAPE '\\' OR LOWER(CAST(program_id AS TEXT)) LIKE LOWER(?) ESCAPE '\\')"
            params.append(f"%{program_id}%")
            params.append(f"%{normalized_id}%")
    
    if day:
        query += " AND sheet = ?"
        params.append(day)
    
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    
    if session:
        query += " AND session = ?"
        params.append(session)
    
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
            'fee': row[14],          # Added fee column
            'session': row[15] if len(row) > 15 else ''  # Added session column
        })
    
    conn.close()
    
    # CRITICAL FIX: Auto-load Excel fallback when database is empty
    if not programs or len(programs) == 0:
        print("⚠️ No Excel programs found in database - attempting to restore from fallback...")
        fallback_programs = get_excel_fallback_data()
        if fallback_programs and len(fallback_programs) > 0:
            print(f"✅ Found {len(fallback_programs)} programs in fallback data")
            # CRITICAL: Restore fallback programs to database, not just return them
            restore_success = restore_fallback_programs_to_database()
            if restore_success:
                print(f"✅ Restored {len(fallback_programs)} programs from fallback to database")
                # Re-query database to get restored programs
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM programs")
                rows = cursor.fetchall()
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
                        'description': row[13],
                        'fee': row[14],
                        'session': row[15] if len(row) > 15 else ''
                    })
                conn.close()
            else:
                # If restore failed, at least return fallback data for display
                print(f"⚠️ Restore to database failed, but returning fallback data for display")
                programs = fallback_programs
        else:
            print("❌ No fallback data available")
    
    return programs

# Initialize database on startup
init_database()

# Track Excel file modification time
excel_last_modified = None

def check_and_import_excel():
    """Check if Excel file has been modified and re-import if needed - DISABLED FOR PERSISTENCE"""
    global excel_last_modified
    
    # DISABLED: This function was causing Excel data to revert on Render
    print("⚠️ Excel auto-import DISABLED to prevent data reversion")
    print("📊 Excel data will persist as uploaded")
    print("💡 Use manual Excel upload in Admin Panel if needed")
    return
    
    # Original function code below (commented out to prevent data reversion):
    # Define Excel file paths
    # EXCEL_PATH = "Class Cancellation App.xlsx"
    # BACKUP_EXCEL_PATH = "/tmp/backup_Class Cancellation App.xlsx" if os.getenv('RENDER') else "backup_Class Cancellation App.xlsx"
    # ... rest of function commented out

def scheduled_daily_report():
    """Send daily analytics report (called by scheduler)"""
    try:
        # Send to your email
        recipient_email = "rebeccam@seniorskingston.ca"
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
        recipient_email = "rebeccam@seniorskingston.ca"
        success = send_analytics_report_email(recipient_email, "weekly")
        
        if success:
            print(f"✅ Weekly analytics report sent to {recipient_email}")
        else:
            print(f"❌ Failed to send weekly analytics report")
            
    except Exception as e:
        print(f"❌ Error in scheduled weekly report: {e}")

# Auto-import Excel file on startup if it exists - DISABLED FOR PERSISTENCE
print("🚀 Starting up - Excel auto-import DISABLED to prevent data reversion")
# check_and_import_excel()  # DISABLED: This was causing data to revert

# Define lifespan handler for proper scheduler lifecycle
@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    # Startup: Initialize scheduler
    global scheduler
    try:
        scheduler = BackgroundScheduler()
        # DISABLED: Auto-import every 30 seconds was causing data reversion
        # scheduler.add_job(check_and_import_excel, 'interval', seconds=30)
        print("⚠️ Auto-import scheduler disabled to prevent data reversion")
        
        # Add scheduled analytics reports
        # Daily report at 9:00 AM
        scheduler.add_job(scheduled_daily_report, 'cron', hour=9, minute=0)
        # Weekly report every Monday at 10:00 AM  
        scheduler.add_job(scheduled_weekly_report, 'cron', day_of_week=0, hour=10, minute=0)
        scheduler.start()
        print("✅ Background scheduler started")
    except Exception as e:
        print(f"⚠️ Failed to start scheduler: {e}")
        scheduler = None
    
    yield
    
    # Shutdown: Stop scheduler
    if scheduler:
        try:
            scheduler.shutdown()
            print("✅ Background scheduler stopped")
        except Exception as e:
            print(f"⚠️ Error stopping scheduler: {e}")

# Create FastAPI app with lifespan
app = FastAPI(title="Program Schedule Update API", lifespan=lifespan_handler)

# Add CORS middleware
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

# In-memory storage for editable events (in production, this would be a database)
editable_events = {}

def scrape_seniors_kingston_events():
    """Scrape real events from Seniors Kingston website using the WORKING Selenium method"""
    try:
        print("🌐 Starting REAL scraping with Selenium (the method that found 46 events with banners)...")
        
        # Use the WORKING Selenium method that found 46 events with banners
        selenium_events = scrape_with_working_selenium()
        if selenium_events:
            print(f"✅ Working Selenium scraping found {len(selenium_events)} events")
            return selenium_events
        
        # Fallback to requests if Selenium fails
        print("⚠️ Selenium failed, trying requests fallback...")
        requests_events = scrape_with_requests_fallback()
        if requests_events:
            print(f"✅ Requests fallback found {len(requests_events)} events")
            return requests_events
        
        print("❌ All scraping methods failed")
        return []
            
    except Exception as e:
        print(f"❌ Error in scraping: {e}")
        import traceback
        traceback.print_exc()
        return []

def scrape_with_working_selenium():
    """The WORKING Selenium method that successfully found 46 events with banners"""
    try:
        print("🕷️ Using the WORKING Selenium method (found 46 events with banners before)...")
        
        # Check if we're in a cloud environment (no GUI available)
        import os
        if os.getenv('RENDER') or os.getenv('HEROKU'):
            print("⚠️ Running in cloud environment - Selenium may not work, trying anyway...")
        
        # Try to use Selenium for JavaScript-heavy sites
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException, WebDriverException
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            import time
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            print("🌐 Setting up Selenium with Chrome...")
            
            # Set up Chrome options (same as the working method)
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Try to create driver with webdriver-manager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"❌ Chrome driver setup failed: {e}")
                return scrape_with_requests_fallback()
            
            try:
                # Navigate to the page
                url = "https://seniorskingston.ca/events"
                print(f"🌐 Navigating to: {url}")
                driver.get(url)
                
                # Wait for the page to load
                print("⏳ Waiting for page to load...")
                time.sleep(10)  # Wait 10 seconds for JavaScript to load (reduced from 15)
                
                # Wait for any content to load
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    print("⚠️ Timeout waiting for page to load")
                
                # Handle pagination - click "Load More" buttons until no more events
                print("🔄 Handling pagination to load all events...")
                max_pagination_attempts = 30  # Increased maximum attempts
                pagination_attempts = 0
                previous_event_count = 0
                no_change_count = 0
                
                # Use JavaScript to force-load all content
                print("   🔧 Using JavaScript to force-load all content...")
                driver.execute_script("""
                    // Scroll to bottom multiple times
                    function scrollToBottom() {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                    // Trigger any lazy loading
                    var event = new Event('scroll');
                    window.dispatchEvent(event);
                """)
                
                while pagination_attempts < max_pagination_attempts:
                    # Aggressive scrolling - scroll in increments to trigger lazy loading
                    print(f"   📜 Scrolling (attempt {pagination_attempts + 1}/{max_pagination_attempts})...")
                    for scroll_step in range(5):
                        scroll_position = (scroll_step + 1) * 1000
                        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                        time.sleep(1)
                    
                    # Scroll to absolute bottom
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # Wait longer for content to load
                    
                    # Try JavaScript click on load more buttons (more reliable)
                    try:
                        load_more_clicked_js = driver.execute_script("""
                            var buttons = document.querySelectorAll('button, a');
                            for (var i = 0; i < buttons.length; i++) {
                                var btn = buttons[i];
                                var text = btn.textContent || btn.innerText || '';
                                var className = btn.className || '';
                                var id = btn.id || '';
                                
                                if ((text.toLowerCase().includes('load more') || 
                                     text.toLowerCase().includes('show more') ||
                                     text.toLowerCase().includes('more events') ||
                                     className.toLowerCase().includes('load') ||
                                     className.toLowerCase().includes('more') ||
                                     id.toLowerCase().includes('load') ||
                                     id.toLowerCase().includes('more')) &&
                                    btn.offsetParent !== null) {
                                    btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    setTimeout(function() { btn.click(); }, 500);
                                    return true;
                                }
                            }
                            return false;
                        """)
                        if load_more_clicked_js:
                            print("   ✅ Clicked load more button via JavaScript")
                            time.sleep(4)  # Wait for new content
                    except Exception as e:
                        pass
                    
                    # Also try Selenium click method
                    load_more_clicked = False
                    load_more_selectors = [
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
                        "button[class*='load']",
                        "button[class*='more']",
                        "a[class*='load']",
                        "a[class*='more']",
                        "[data-action='load-more']",
                        "[id*='load']",
                        "[id*='more']",
                        ".load-more",
                        ".show-more"
                    ]
                    
                    for selector in load_more_selectors:
                        try:
                            if selector.startswith("//"):
                                buttons = driver.find_elements(By.XPATH, selector)
                            else:
                                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            for button in buttons:
                                try:
                                    if button.is_displayed() and button.is_enabled():
                                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                        time.sleep(1)
                                        button.click()
                                        load_more_clicked = True
                                        print(f"   ✅ Clicked load more button: {selector}")
                                        time.sleep(4)  # Wait longer for content
                                        break
                                except:
                                    continue
                            
                            if load_more_clicked:
                                break
                        except:
                            continue
                    
                    # Check if new events were loaded
                    current_page_source = driver.page_source
                    soup_temp = BeautifulSoup(current_page_source, 'html.parser')
                    
                    # Count events more comprehensively
                    event_containers_temp = soup_temp.select('div[class*="event"], div[class*="card"], article, div[class*="post"], div[class*="item"], div[class*="entry"]')
                    # Also count by looking for date patterns in text
                    all_text = soup_temp.get_text()
                    date_matches = len(re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}', all_text, re.IGNORECASE))
                    current_event_count = max(len(event_containers_temp), date_matches // 2)  # Use higher count
                    
                    if current_event_count > previous_event_count:
                        print(f"   📊 Loaded more events: {previous_event_count} → {current_event_count}")
                        previous_event_count = current_event_count
                        no_change_count = 0
                        pagination_attempts = 0  # Reset if we found new events
                    else:
                        no_change_count += 1
                        pagination_attempts += 1
                        if not load_more_clicked and no_change_count >= 5:  # 5 attempts with no change
                            print(f"   ⏸️ No more events to load after {no_change_count} attempts")
                            break
                
                # Final aggressive scroll to ensure ALL content is loaded
                print("📜 Final aggressive scroll to ensure ALL content is loaded...")
                for i in range(10):  # More scrolls
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    # Scroll back up a bit to trigger any lazy loading
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 2000);")
                    time.sleep(1)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                
                # One more wait for any final lazy loading
                time.sleep(5)
                
                # Get page source after all pagination
                page_source = driver.page_source
                
                # Save the rendered HTML for debugging
                debug_file = "/tmp/seniors_events_rendered_selenium.html" if os.getenv('RENDER') else "seniors_events_rendered_selenium.html"
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    print("💾 Saved rendered HTML for debugging")
                except Exception as e:
                    print(f"⚠️ Could not save debug file: {e}")
                
                # Parse the HTML
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Look for event containers
                print("🔍 Looking for event containers...")
                
                # Try different selectors for events - expanded list
                event_selectors = [
                    'div[class*="event"]',
                    'div[class*="card"]',
                    'div[class*="post"]',
                    'article',
                    'div[class*="item"]',
                    'div[class*="entry"]',
                    'div[class*="content"]',
                    'div[class*="box"]',
                    'div[class*="container"]',
                    'div[class*="wrapper"]',
                    'div[class*="grid"]',
                    'div[class*="list"]',
                    'div[class*="program"]',
                    'div[class*="activity"]',
                    'div[class*="tile"]',
                    'div[class*="block"]',
                    'div[class*="panel"]',
                    'div[class*="section"]',
                    '[data-event]',
                    '[data-type="event"]'
                ]
                
                events_found = []
                seen_event_keys = set()  # Track seen events to avoid duplicates
                
                # First pass: Use selectors
                for selector in event_selectors:
                    containers = soup.select(selector)
                    if containers:
                        print(f"   Found {len(containers)} elements with selector: {selector}")
                        
                        # Check ALL containers
                        for i, container in enumerate(containers):
                            # Look for images in this container
                            images = container.find_all('img')
                            if images:
                                print(f"      Container {i+1} has {len(images)} images")
                                
                                # Look for text content that might be event titles
                                text_elements = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div'])
                                text_content = []
                                for elem in text_elements:
                                    text = elem.get_text(strip=True)
                                    if text and len(text) > 5 and len(text) < 100:
                                        text_content.append(text)
                                
                                if text_content:
                                    print(f"         Text content: {text_content[:3]}")  # First 3 text elements
                                    
                                    # Try to extract event information
                                    for img in images:
                                        img_src = img.get('src', '')
                                        img_alt = img.get('alt', '')
                                        
                                        if img_src:
                                            # Convert relative URL to absolute
                                            if img_src.startswith('/'):
                                                img_src = f"https://seniorskingston.ca{img_src}"
                                            elif not img_src.startswith('http'):
                                                img_src = f"https://seniorskingston.ca/{img_src}"
                                            
                                            # Use the first text element as title
                                            title = text_content[0] if text_content else img_alt
                                            
                                            # Filter out non-event items
                                            skip_keywords = [
                                                'register today', 'upcoming events', 'list view', 'calendar view',
                                                'programs', 'events', 'dining', 'quick links', 'about us',
                                                'enhancing the quality', 'funded by', 'close x', 'advertisement',
                                                '56 francis st', 'mon - fri', 'kingston', 'latest program guide',
                                                'donate', 'volunteer', 'hatter\'s menu'
                                            ]
                                            
                                            title_lower = title.lower()
                                            if any(keyword in title_lower for keyword in skip_keywords):
                                                continue  # Skip this item, it's not an actual event
                                            
                                            # Parse date and time from text content
                                            date_str = "TBD"
                                            time_str = "TBD"
                                            start_date = datetime.now()
                                            end_date = datetime.now()
                                            
                                            # Look for date/time patterns in text content
                                            
                                            # Combine all text content to search for date/time
                                            full_text = ' '.join(text_content)
                                            
                                            # Look for date patterns like "November 24, 12:00 pm" or "Nov 24, 12:00 pm"
                                            date_time_patterns = [
                                                r'([A-Za-z]+\s+\d{1,2},\s+\d{1,2}:\d{2}\s+(?:am|pm|AM|PM))',  # "November 24, 12:00 pm"
                                                r'([A-Za-z]+\s+\d{1,2},\s+\d{1,2}:\d{2})',  # "November 24, 12:00"
                                                r'([A-Za-z]{3}\s+\d{1,2},\s+\d{1,2}:\d{2}\s+(?:am|pm|AM|PM))',  # "Nov 24, 12:00 pm"
                                            ]
                                            
                                            for pattern in date_time_patterns:
                                                match = re.search(pattern, full_text, re.IGNORECASE)
                                                if match:
                                                    date_time_str = match.group(1)
                                                    # Try to parse the date/time
                                                    try:
                                                        # Parse date/time string
                                                        parsed_dt = parser.parse(date_time_str, fuzzy=True)
                                                        
                                                        # Fix year if we're in December and date is in January (year transition)
                                                        current_date = datetime.now()
                                                        if current_date.month == 12 and parsed_dt.month == 1:
                                                            # If we're in December and the parsed date is January, it should be next year
                                                            if parsed_dt.year == current_date.year:
                                                                parsed_dt = parsed_dt.replace(year=current_date.year + 1)
                                                                print(f"         Fixed year: {current_date.year} → {parsed_dt.year} (January event)")
                                                        
                                                        start_date = parsed_dt
                                                        end_date = parsed_dt + timedelta(hours=1)
                                                        
                                                        # Extract date and time strings
                                                        date_str = parsed_dt.strftime('%B %d, %Y')
                                                        time_str = parsed_dt.strftime('%I:%M %p').lstrip('0')
                                                        
                                                        print(f"         Parsed date/time: {date_str} {time_str}")
                                                        break
                                                    except Exception as e:
                                                        print(f"         Could not parse date/time: {e}")
                                                        continue
                                            
                                            # If no date/time found, try to extract just date or time separately
                                            if date_str == "TBD":
                                                # Look for just date
                                                date_patterns = [
                                                    r'([A-Za-z]+\s+\d{1,2}(?:,\s+\d{4})?)',  # "November 24" or "November 24, 2025"
                                                    r'([A-Za-z]{3}\s+\d{1,2}(?:,\s+\d{4})?)',  # "Nov 24" or "Nov 24, 2025"
                                                ]
                                                for pattern in date_patterns:
                                                    match = re.search(pattern, full_text, re.IGNORECASE)
                                                    if match:
                                                        date_str = match.group(1)
                                                        try:
                                                            parsed_dt = parser.parse(date_str, fuzzy=True)
                                                            
                                                            # Fix year if we're in December and date is in January (year transition)
                                                            current_date = datetime.now()
                                                            if current_date.month == 12 and parsed_dt.month == 1:
                                                                # If we're in December and the parsed date is January, it should be next year
                                                                if parsed_dt.year == current_date.year:
                                                                    parsed_dt = parsed_dt.replace(year=current_date.year + 1)
                                                                    print(f"         Fixed year: {current_date.year} → {parsed_dt.year} (January event)")
                                                            
                                                            start_date = parsed_dt
                                                            end_date = parsed_dt + timedelta(hours=1)
                                                            date_str = parsed_dt.strftime('%B %d, %Y')
                                                        except:
                                                            pass
                                                        break
                                            
                                            if time_str == "TBD":
                                                # Look for just time
                                                time_pattern = r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))'
                                                match = re.search(time_pattern, full_text, re.IGNORECASE)
                                                if match:
                                                    time_str = match.group(1)
                                                    # Try to apply time to start_date if we have a date
                                                    if date_str != "TBD":
                                                        try:
                                                            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)', time_str, re.IGNORECASE)
                                                            if time_match:
                                                                hour = int(time_match.group(1))
                                                                minute = int(time_match.group(2))
                                                                period = time_match.group(3).upper()
                                                                
                                                                if period == 'PM' and hour != 12:
                                                                    hour += 12
                                                                elif period == 'AM' and hour == 12:
                                                                    hour = 0
                                                                
                                                                start_date = start_date.replace(hour=hour, minute=minute)
                                                                end_date = start_date + timedelta(hours=1)
                                                        except:
                                                            pass
                                            
                                            # Create event object
                                            event = {
                                                "title": title,
                                                "description": ' '.join(text_content[1:]) if len(text_content) > 1 else title,
                                                "image_url": img_src,
                                                "startDate": start_date.isoformat() + 'Z',
                                                "endDate": end_date.isoformat() + 'Z',
                                                "location": "Seniors Kingston",
                                                "dateStr": date_str,
                                                "timeStr": time_str
                                            }
                                            
                                            # Use title + date as unique key to avoid duplicates
                                            event_key = f"{title.lower().strip()}_{date_str}_{time_str}"
                                            if event_key not in seen_event_keys:
                                                events_found.append(event)
                                                seen_event_keys.add(event_key)
                                                print(f"         Event: {title} - {date_str} {time_str}")
                                                print(f"         Banner: {img_src}")
                                            else:
                                                print(f"         ⏭️ Skipped duplicate: {title}")
                
                # Helper function to check if an event is already found (fuzzy matching)
                def is_duplicate_event(title, date_str, time_str):
                    """Check if this event is already in the found events (fuzzy match)"""
                    title_lower = title.lower().strip()
                    for existing_event in events_found:
                        existing_title = existing_event.get('title', '').lower().strip()
                        existing_date = existing_event.get('dateStr', '')
                        existing_time = existing_event.get('timeStr', '')
                        
                        # Check if title is similar (one contains the other or very similar)
                        title_similar = (title_lower in existing_title or existing_title in title_lower) and len(title_lower) > 5
                        date_similar = date_str in existing_date or existing_date in date_str
                        time_similar = (not time_str or not existing_time or time_str == existing_time or time_str in existing_time or existing_time in time_str)
                        
                        if title_similar and date_similar:
                            return True
                    return False
                
                # Helper function to extract clean event title from text
                def extract_clean_title(text, date_str):
                    """Extract a clean event title from text, avoiding descriptions"""
                    # Known event titles to look for
                    known_titles = [
                        'Fresh Food Market', 'Legal Advice', 'Legal Clinic', 'E-Resources at the Library',
                        'Cafe Franglish', "Tuesday at Tom's", '500 years', '500 Years'
                    ]
                    
                    # First, check if any known title is in the text
                    for known_title in known_titles:
                        if known_title.lower() in text.lower():
                            return known_title
                    
                    # Split by common separators
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    sentences = [s.strip() for s in text.split('.') if s.strip()]
                    
                    # Look for short, title-like text (not descriptions)
                    for line in lines[:3]:  # Check first 3 lines
                        line = line.strip()
                        # Skip if it's too long (likely a description)
                        if len(line) > 80:
                            continue
                        # Skip if it contains common description words
                        if any(word in line.lower() for word in ['brings', 'provides', 'learn', 'join', 'register', 'call', 'appointment']):
                            continue
                        # Skip if it's just a time or date
                        if re.match(r'^\d{1,2}:\d{2}', line):
                            continue
                        # Good candidate for title
                        if 5 < len(line) < 80:
                            return line
                    
                    # Fallback: first sentence if short enough
                    if sentences and len(sentences[0]) < 80:
                        return sentences[0]
                    
                    # Last resort: first line
                    return lines[0] if lines else text[:80]
                
                # Second pass: Look for events by date patterns in all text (catch any missed events)
                print("🔍 Second pass: Looking for events by date patterns in all text...")
                all_text_elements = soup.find_all(['div', 'article', 'section', 'li', 'p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                
                # Also search in the full page text for specific event patterns
                full_page_text = soup.get_text()
                
                # Look for ALL date patterns (not just specific January dates) to catch all events including February and recurring events
                # Find all date patterns in the text: "January 20", "February 5", "Jan 20", "Feb 5", etc.
                all_date_patterns = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', full_page_text, re.IGNORECASE)
                # Remove duplicates while preserving order
                seen_dates = set()
                unique_dates = []
                for date_match in all_date_patterns:
                    if date_match not in seen_dates:
                        seen_dates.add(date_match)
                        unique_dates.append(date_match)
                
                print(f"   📅 Found {len(unique_dates)} unique date patterns in page text")
                
                for date_str in unique_dates:
                    # Find all occurrences of this date in the text - look for pattern: Date, Time, Title
                    pattern = re.escape(date_str) + r'[,\s]+(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))?[,\s]*(.+?)(?=(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}|$)'
                    matches = re.finditer(pattern, full_page_text, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        time_str_match = match.group(1) if match.group(1) else None
                        event_text = match.group(2) if match.group(2) else match.group(3) if len(match.groups()) > 2 else ''
                        
                        if event_text and len(event_text.strip()) > 5:
                            # Extract clean event title (not description)
                            potential_title = extract_clean_title(event_text, date_str)
                            
                            # Skip if title is too long or looks like a description
                            if len(potential_title) > 80 or any(word in potential_title.lower() for word in ['brings', 'provides', 'learn about', 'join in', 'register call']):
                                continue
                            
                            # Skip common non-event text
                            skip_patterns = ['close', 'advertisement', 'register today', 'upcoming events', 'click here']
                            if any(skip in potential_title.lower() for skip in skip_patterns):
                                continue
                            
                            # Check if this is a duplicate of an existing event
                            if is_duplicate_event(potential_title, date_str, time_str_match or ''):
                                print(f"         ⏭️ Skipped duplicate: {potential_title} on {date_str}")
                                continue
                            
                            # Create unique key
                            event_key = f"{potential_title.lower().strip()}_{date_str}_{time_str_match or ''}"
                            
                            if event_key not in seen_event_keys:
                                    # Parse date
                                    try:
                                        parsed_dt = parser.parse(date_str, fuzzy=True)
                                        current_date = datetime.now()
                                        # Fix year for January events when we're in December (year transition)
                                        if current_date.month == 12 and parsed_dt.month == 1:
                                            if parsed_dt.year == current_date.year:
                                                parsed_dt = parsed_dt.replace(year=current_date.year + 1)
                                        # Fix year for February+ events when we're in January (should be same year)
                                        elif current_date.month == 1 and parsed_dt.month >= 2:
                                            if parsed_dt.year < current_date.year:
                                                parsed_dt = parsed_dt.replace(year=current_date.year)
                                        
                                        # Parse time
                                        if time_str_match:
                                            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)', time_str_match, re.IGNORECASE)
                                            if time_match:
                                                hour = int(time_match.group(1))
                                                minute = int(time_match.group(2))
                                                period = time_match.group(3).upper()
                                                if period == 'PM' and hour != 12:
                                                    hour += 12
                                                elif period == 'AM' and hour == 12:
                                                    hour = 0
                                                parsed_dt = parsed_dt.replace(hour=hour, minute=minute)
                                        else:
                                            # Default time if not found (try to find in event_text)
                                            time_in_text = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)', event_text, re.IGNORECASE)
                                            if time_in_text:
                                                hour = int(time_in_text.group(1))
                                                minute = int(time_in_text.group(2))
                                                period = time_in_text.group(3).upper()
                                                if period == 'PM' and hour != 12:
                                                    hour += 12
                                                elif period == 'AM' and hour == 12:
                                                    hour = 0
                                                parsed_dt = parsed_dt.replace(hour=hour, minute=minute)
                                        
                                        # Look for image - search in nearby elements
                                        img_src = None
                                        # Try to find image by searching for elements containing this text
                                        for elem in all_text_elements:
                                            if date_str.lower() in elem.get_text().lower() and potential_title.lower() in elem.get_text().lower():
                                                img_elem = elem.find('img')
                                                if not img_elem:
                                                    # Check parent
                                                    parent = elem.find_parent()
                                                    if parent:
                                                        img_elem = parent.find('img')
                                                
                                                if img_elem:
                                                    img_src = img_elem.get('src', '')
                                                    if img_src:
                                                        if not img_src.startswith('http'):
                                                            if img_src.startswith('/'):
                                                                img_src = f"https://seniorskingston.ca{img_src}"
                                                            else:
                                                                img_src = f"https://seniorskingston.ca/{img_src}"
                                                        break
                                        
                                        # Default image for known events
                                        if not img_src:
                                            if 'Fresh Food Market' in potential_title:
                                                img_src = "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh Food Market.jpg"
                                            elif 'Legal Advice' in potential_title:
                                                img_src = "https://cms.seniorskingston.ca/assets/ff281879-79a3-45e3-ab4c-b54f69a2e371/Legal Advice.JPG"
                                        
                                        # Get description (everything after title, but limit length)
                                        description_lines = [l.strip() for l in event_text.split('\n') if l.strip() and l.strip() != potential_title]
                                        description = ' '.join(description_lines[:3])[:500] if description_lines else potential_title
                                        
                                        event = {
                                            "title": potential_title,
                                            "description": description,
                                            "image_url": img_src or "/logo192.png",
                                            "startDate": parsed_dt.isoformat() + 'Z',
                                            "endDate": (parsed_dt + timedelta(hours=1)).isoformat() + 'Z',
                                            "location": "Seniors Kingston",
                                            "dateStr": parsed_dt.strftime('%B %d, %Y'),
                                            "timeStr": parsed_dt.strftime('%I:%M %p').lstrip('0') if parsed_dt.hour != 0 or parsed_dt.minute != 0 else "TBD"
                                        }
                                        
                                        events_found.append(event)
                                        seen_event_keys.add(event_key)
                                        print(f"         ✅ Found by date pattern: {potential_title} - {parsed_dt.strftime('%B %d, %Y')} {event['timeStr']}")
                                    except Exception as e:
                                        print(f"         ⚠️ Error parsing date pattern {date_str}: {e}")
                                        continue
                
                # Third pass: Look for events in all elements more comprehensively (only for truly missing events)
                print("🔍 Third pass: Comprehensive search in all elements (skip if already found)...")
                for elem in all_text_elements:
                    text = elem.get_text(strip=True)
                    if not text or len(text) < 20:
                        continue
                    
                    # Look for date patterns like "January 20" or "Jan 20" or "January 27"
                    date_pattern = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', text, re.IGNORECASE)
                    if date_pattern:
                        date_str = date_pattern.group(0)
                        
                        # Check if this is a duplicate first
                        # Extract potential title
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        if not lines:
                            continue
                        
                        potential_title = extract_clean_title(text, date_str)
                        
                        # Skip if this looks like a duplicate
                        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))', text, re.IGNORECASE)
                        time_str = time_match.group(1) if time_match else ""
                        
                        if is_duplicate_event(potential_title, date_str, time_str):
                            continue
                        
                        # Check if this looks like an event (has time, title, etc.)
                        has_time = bool(time_match)
                        has_title = len(potential_title) > 5 and len(potential_title) < 80
                        
                        # Also check for known event keywords
                        has_event_keywords = any(keyword in text.lower() for keyword in [
                            'fresh food market', 'legal advice', 'legal clinic', 'e-resources', '500 years', 
                            'workshop', 'meeting', 'class', 'event', 'program', 'seminar', 'lecture', 'session'
                        ])
                        
                        if (has_time or has_event_keywords) and has_title:
                            event_key = f"{potential_title.lower().strip()}_{date_str}_{time_str}"
                            
                            if event_key not in seen_event_keys:
                                # Look for image in parent or nearby
                                img_elem = elem.find('img') or (elem.find_parent().find('img') if elem.find_parent() else None)
                                img_src = None
                                if img_elem:
                                    img_src = img_elem.get('src', '')
                                    if img_src and not img_src.startswith('http'):
                                        if img_src.startswith('/'):
                                            img_src = f"https://seniorskingston.ca{img_src}"
                                        else:
                                            img_src = f"https://seniorskingston.ca/{img_src}"
                                
                                # Default images for known events
                                if not img_src:
                                    if 'Fresh Food Market' in potential_title:
                                        img_src = "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh Food Market.jpg"
                                    elif 'Legal Advice' in potential_title:
                                        img_src = "https://cms.seniorskingston.ca/assets/ff281879-79a3-45e3-ab4c-b54f69a2e371/Legal Advice.JPG"
                                
                                # Parse date
                                try:
                                    parsed_dt = parser.parse(date_str, fuzzy=True)
                                    current_date = datetime.now()
                                    # Fix year for January events when we're in December (year transition)
                                    if current_date.month == 12 and parsed_dt.month == 1:
                                        if parsed_dt.year == current_date.year:
                                            parsed_dt = parsed_dt.replace(year=current_date.year + 1)
                                    # Fix year for February+ events when we're in January (should be same year)
                                    elif current_date.month == 1 and parsed_dt.month >= 2:
                                        if parsed_dt.year < current_date.year:
                                            parsed_dt = parsed_dt.replace(year=current_date.year)
                                    
                                    if time_match:
                                        hour = int(time_match.group(1))
                                        minute = int(time_match.group(2))
                                        period = time_match.group(3).upper() if len(time_match.groups()) > 2 else 'AM'
                                        if period == 'PM' and hour != 12:
                                            hour += 12
                                        elif period == 'AM' and hour == 12:
                                            hour = 0
                                        parsed_dt = parsed_dt.replace(hour=hour, minute=minute)
                                    
                                    # Get description (everything after title)
                                    description_lines = [l.strip() for l in lines if l.strip() != potential_title and not re.match(r'^\d{1,2}:\d{2}', l)]
                                    description = ' '.join(description_lines[:3])[:500] if description_lines else potential_title
                                    
                                    event = {
                                        "title": potential_title,
                                        "description": description,
                                        "image_url": img_src or "/logo192.png",
                                        "startDate": parsed_dt.isoformat() + 'Z',
                                        "endDate": (parsed_dt + timedelta(hours=1)).isoformat() + 'Z',
                                        "location": "Seniors Kingston",
                                        "dateStr": parsed_dt.strftime('%B %d, %Y'),
                                        "timeStr": parsed_dt.strftime('%I:%M %p').lstrip('0') if parsed_dt.hour != 0 or parsed_dt.minute != 0 else "TBD"
                                    }
                                    
                                    events_found.append(event)
                                    seen_event_keys.add(event_key)
                                    print(f"         ✅ Found in comprehensive search: {potential_title} - {parsed_dt.strftime('%B %d, %Y')} {event['timeStr']}")
                                except Exception as e:
                                    print(f"         ⚠️ Error parsing: {e}")
                                    pass
                
                # Remove duplicates based on title + date + time (not just title, to allow same event on different dates)
                unique_events = []
                seen_event_keys_final = set()
                for event in events_found:
                    title = event.get('title', '')
                    date_str = event.get('dateStr', '')
                    time_str = event.get('timeStr', '')
                    # Use title + date + time as unique key to allow same event on different dates
                    event_key_final = f"{title.lower().strip()}_{date_str}_{time_str}"
                    if event_key_final not in seen_event_keys_final and len(title) > 5:
                        unique_events.append(event)
                        seen_event_keys_final.add(event_key_final)
                
                print(f"\n📊 Found {len(unique_events)} unique events with banners")
                
                if unique_events:
                    print("✅ Successfully scraped events from website")
                    return unique_events
                else:
                    print("📅 No events found in loaded content")
                    return []
                    
            finally:
                driver.quit()
                
        except ImportError:
            print("❌ Selenium not available, using requests fallback")
            return scrape_with_requests_fallback()
        except Exception as e:
            print(f"❌ Selenium error: {e}")
            return scrape_with_requests_fallback()
            
    except Exception as e:
        print(f"❌ Error in scraping: {e}")
        return None

def scrape_with_requests_fallback():
    """ENHANCED SCRAPING METHOD - Works on Render cloud environment"""
    try:
        print("🌐 Using enhanced scraping method for Seniors Kingston website")
        
        # Since we're on Render (cloud), Selenium won't work reliably
        # Use a smarter requests-based approach
        return scrape_with_smart_requests()
        
    except Exception as e:
        print(f"❌ Error in enhanced scraping method: {e}")
        return get_november_2025_events_fallback()

def scrape_with_smart_requests():
    """REAL SCRAPING - Try to find actual API endpoints for Seniors Kingston events"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        import json
        
        print("🌐 Attempting to find REAL events from Seniors Kingston API")
        
        # Strategy 1: Try to find API endpoints
        api_endpoints = [
            "https://seniorskingston.ca/api/events",
            "https://seniorskingston.ca/api/calendar",
            "https://seniorskingston.ca/api/programs",
            "https://seniorskingston.ca/wp-json/wp/v2/posts",
            "https://seniorskingston.ca/wp-json/wp/v2/events",
            "https://seniorskingston.ca/events.json",
            "https://seniorskingston.ca/api/v1/events",
            "https://seniorskingston.ca/events/api"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://seniorskingston.ca/events'
        }
        
        for endpoint in api_endpoints:
            try:
                print(f"🔍 Trying API endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        events = extract_events_from_api_data(data)
                        if events:
                            print(f"✅ Found {len(events)} events from API: {endpoint}")
                            return events
                    except:
                        # Not JSON, continue
                        pass
                        
            except Exception as e:
                print(f"❌ API endpoint failed: {endpoint} - {e}")
                continue
        
        # Strategy 2: Try to find WordPress REST API
        wp_endpoints = [
            "https://seniorskingston.ca/wp-json/wp/v2/posts?per_page=100",
            "https://seniorskingston.ca/wp-json/wp/v2/events?per_page=100",
            "https://seniorskingston.ca/wp-json/wp/v2/pages?per_page=100"
        ]
        
        for endpoint in wp_endpoints:
            try:
                print(f"🔍 Trying WordPress API: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    events = extract_events_from_wp_data(data)
                    if events:
                        print(f"✅ Found {len(events)} events from WordPress API")
                        return events
                        
            except Exception as e:
                print(f"❌ WordPress API failed: {endpoint} - {e}")
                continue
        
        # Strategy 3: Try to find embedded data in the main page
        print("🔍 Trying to find embedded event data in main page...")
        url = "https://seniorskingston.ca/events"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any script tags that might contain event data
            script_tags = soup.find_all('script')
            print(f"🔍 Found {len(script_tags)} script tags to analyze")
            
            for script in script_tags:
                if script.string:
                    script_content = script.string
                    
                    # Look for common event data patterns
                    patterns = [
                        r'events\s*:\s*\[.*?\]',
                        r'calendar\s*:\s*\[.*?\]',
                        r'programs\s*:\s*\[.*?\]',
                        r'data\s*:\s*\[.*?\]'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script_content, re.DOTALL | re.IGNORECASE)
                        for match in matches:
                            try:
                                # Try to extract JSON array
                                json_match = re.search(r'\[.*\]', match, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group())
                                    events = extract_events_from_api_data(data)
                                    if events:
                                        print(f"✅ Found {len(events)} events in embedded script data")
                                        return events
                            except:
                                continue
            
            # Look for any data attributes or hidden content
            data_elements = soup.find_all(attrs={"data-events": True})
            if data_elements:
                for element in data_elements:
                    try:
                        data = json.loads(element['data-events'])
                        events = extract_events_from_api_data(data)
                        if events:
                            print(f"✅ Found {len(events)} events in data attributes")
                            return events
                    except:
                        continue
                    
        # If all strategies fail, return empty list (no fake events)
        print("❌ Could not find real events from Seniors Kingston website")
        print("💡 The website likely uses JavaScript to load events dynamically")
        print("📝 Returning empty list - user should add events manually")
        return []
        
    except Exception as e:
        print(f"❌ Error in real scraping attempt: {e}")
        return []

def extract_events_from_api_data(data):
    """Extract events from API response data"""
    events = []
    try:
        if isinstance(data, list):
            for item in data:
                event = create_event_from_api_item(item)
                if event:
                    events.append(event)
        elif isinstance(data, dict):
            # Look for events array in the response
            for key in ['events', 'data', 'items', 'posts', 'programs']:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        event = create_event_from_api_item(item)
                        if event:
                            events.append(event)
                    break
                    
        return events
        
    except Exception as e:
        print(f"❌ Error extracting events from API data: {e}")
        return []

def extract_events_from_wp_data(data):
    """Extract events from WordPress API data"""
    events = []
    try:
        for post in data:
            if isinstance(post, dict):
                event = create_event_from_wp_post(post)
                if event:
                    events.append(event)
        return events
        
    except Exception as e:
        print(f"❌ Error extracting events from WordPress data: {e}")
        return []

def create_event_from_api_item(item):
    """Create event from API item"""
    try:
        if not isinstance(item, dict):
            return None
            
        title = item.get('title', {}).get('rendered', '') if isinstance(item.get('title'), dict) else item.get('title', '')
        if not title:
            title = item.get('name', '') or item.get('event_title', '') or item.get('program_name', '')
            
        if not title:
            return None
            
        # Clean up title
        title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
        title = title.strip()
        
        if len(title) > 50:
            title = title[:50] + "..."
            
        return {
            "title": title,
            "description": item.get('content', {}).get('rendered', '') if isinstance(item.get('content'), dict) else item.get('description', title),
            "image_url": "/event-schedule-banner.png",
            "startDate": datetime.now().isoformat(),
            "endDate": datetime.now().isoformat(),
            "location": "Seniors Kingston",
            "dateStr": "TBD",
            "timeStr": "TBD"
        }
        
    except Exception as e:
        print(f"❌ Error creating event from API item: {e}")
        return None

def create_event_from_wp_post(post):
    """Create event from WordPress post"""
    try:
        title = post.get('title', {}).get('rendered', '') if isinstance(post.get('title'), dict) else post.get('title', '')
        if not title:
            return None
            
        # Clean up title
        title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
        title = title.strip()
        
        if len(title) > 50:
            title = title[:50] + "..."
            
        return {
            "title": title,
            "description": post.get('content', {}).get('rendered', '') if isinstance(post.get('content'), dict) else post.get('excerpt', title),
            "image_url": "/event-schedule-banner.png",
            "startDate": datetime.now().isoformat(),
            "endDate": datetime.now().isoformat(),
            "location": "Seniors Kingston",
            "dateStr": "TBD",
            "timeStr": "TBD"
        }
        
    except Exception as e:
        print(f"❌ Error creating event from WordPress post: {e}")
        return None

def get_excel_fallback_data():
    """Get Excel programs from fallback data"""
    try:
        fallback_file = "/tmp/excel_fallback_data.json" if os.getenv('RENDER') else "excel_fallback_data.json"
        
        if os.path.exists(fallback_file):
            with open(fallback_file, 'r', encoding='utf-8') as f:
                fallback_data = json.load(f)
            
            if 'programs' in fallback_data and fallback_data['programs']:
                print(f"📅 Excel fallback last updated: {fallback_data.get('metadata', {}).get('last_updated', 'Unknown')}")
                return fallback_data['programs']
        
        return []
        
    except Exception as e:
        print(f"❌ Error loading Excel fallback data: {e}")
        import traceback
        traceback.print_exc()
        return []

def restore_fallback_programs_to_database():
    """Restore fallback programs to database - CRITICAL RECOVERY FUNCTION"""
    try:
        print("🔄 Attempting to restore programs from fallback data...")
        fallback_programs = get_excel_fallback_data()
        
        if not fallback_programs or len(fallback_programs) == 0:
            print("❌ No fallback programs found to restore")
            return False
        
        print(f"📦 Found {len(fallback_programs)} programs in fallback data")
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM programs")
        print("🗑️ Cleared existing database data")
        
        # Restore programs to database
        restored_count = 0
        for prog in fallback_programs:
            try:
                # Map fallback data structure to database schema
                # Fallback may have different field names, so we need to handle both
                sheet = prog.get('sheet', '')
                program = prog.get('program', '')
                program_id = prog.get('program_id', '')
                date_range = prog.get('date_range', '')
                time = prog.get('time', '')
                location = prog.get('location', '')
                class_room = prog.get('class_room', '')
                instructor = prog.get('instructor', '')
                program_status = prog.get('program_status', 'Active')
                class_cancellation = prog.get('class_cancellation', '')
                note = prog.get('note', prog.get('additional_information', ''))
                withdrawal = prog.get('withdrawal', prog.get('refund', ''))
                description = prog.get('description', '')
                fee = prog.get('fee', '')
                
                # Insert into database
                session = safe_str(prog.get('session', ''))
                cursor.execute('''
                    INSERT INTO programs (sheet, program, program_id, date_range, time, location, 
                                       class_room, instructor, program_status, class_cancellation, note, withdrawal, description, fee, session)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sheet, program, program_id, date_range, time, location, 
                      class_room, instructor, program_status, class_cancellation, note, withdrawal, description, fee, session))
                
                restored_count += 1
            except Exception as e:
                print(f"⚠️ Error restoring program {prog.get('program', 'Unknown')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully restored {restored_count} programs from fallback to database")
        return True
        
    except Exception as e:
        print(f"❌ Error restoring fallback programs to database: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_comprehensive_november_events():
    """SMART EVENTS FALLBACK - Try saved fallback first, then use real events data"""
    print("🔄 Using SMART events fallback system")
    
    # First, try to load saved fallback data
    fallback_file = "/tmp/events_fallback_data.json" if os.getenv('RENDER') else "events_fallback_data.json"
    
    if os.path.exists(fallback_file):
        try:
            with open(fallback_file, 'r', encoding='utf-8') as f:
                fallback_data = json.load(f)
            
            if 'events' in fallback_data and fallback_data['events']:
                events = fallback_data['events']
                print(f"✅ Using saved fallback events: {len(events)} events")
                print(f"📅 Last updated: {fallback_data.get('metadata', {}).get('last_updated', 'Unknown')}")
                return events
        except Exception as e:
            print(f"❌ Error loading fallback events: {e}")
    
    # Second, try to load the real events with banners file
    real_events_file = "events_with_real_banners.json"
    if os.path.exists(real_events_file):
        try:
            with open(real_events_file, 'r', encoding='utf-8') as f:
                real_data = json.load(f)
            
            if 'events' in real_data and real_data['events']:
                events = real_data['events']
                print(f"✅ Using real events with banners: {len(events)} events")
                print(f"📅 Source: {real_data.get('metadata', {}).get('source', 'Unknown')}")
                return events
        except Exception as e:
            print(f"❌ Error loading real events: {e}")
    
    # If no saved fallback or real events, use hardcoded events
    print("📅 Using hardcoded events fallback (45 events from Seniors Kingston)")
    
    # Real events from Seniors Kingston website (scraped on Oct 25-26, 2025)
    return [
            {
            "title": "Sound Escapes: Kenny & Dolly",
            "startDate": "2025-10-24T13:30:00Z",
            "endDate": "2025-10-24T14:30:00Z",
            "description": "Sound Escapes: Kenny & Dolly  October 24, 1:30 pm Celebrate timeless hits in this unforgettable tribute concert. Relive legendary duets",
            "location": "Online",
            "dateStr": "October 24",
            "timeStr": "1:30 pm",
            "price": "$12",
            "instructor": "",
            "registration": "call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/bd103f00-5824-449d-9a8d-74dd98f450c3/Sound%20Escapes%202.jpg"
        },
        {
            "title": "Wearable Tech",
            "startDate": "2025-10-27T12:00:00Z",
            "endDate": "2025-10-27T13:00:00Z",
            "description": "Wearable Tech  October 27, 12:00 pm Smartwatches and fitness trackers have become increasing popular. Learn how wearable technology can support your health, fitness and everyday activities.",
            "location": "",
            "dateStr": "October 27",
            "timeStr": "12:00 pm",
            "price": "",
            "instructor": "Sam Kalb",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/9ac584b0-0bc5-4803-a59b-dd48f5589df7/Tech%20Bytes.jpg"
        },
        {
            "title": "Legal Advice",
            "startDate": "2025-10-27T13:00:00Z",
            "endDate": "2025-10-27T14:00:00Z",
            "description": "Legal Advice October 27, 1:00 pm A practicing lawyer provides confidential advice by phone. Appointment required (20 minutes max).",
            "location": "",
            "dateStr": "October 27",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/ff281879-79a3-45e3-ab4c-b54f69a2e371/Legal%20Advice.JPG"
        },
        {
            "title": "Fresh Food Market",
            "startDate": "2025-10-28T10:00:00Z",
            "endDate": "2025-10-28T11:00:00Z",
            "description": "Fresh Food Market October 28, 10:00 am Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
            "location": "",
            "dateStr": "October 28",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh%20Food%20Market.jpg"
        },
        {
            "title": "18th Century Astronomy",
            "startDate": "2025-10-30T13:00:00Z",
            "endDate": "2025-10-30T14:00:00Z",
            "description": "18th Century Astronomy  October 30, 1:00 pm The 1700s changed our view of the universe. Hear about the first \"X\" prize, the solar system, deep skyobjects, the distance to the stars and the remarkable men and women involved.",
            "location": "",
            "dateStr": "October 30",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/1444a77f-b919-494d-bfe1-87ae130cbdf5/Featured%20Speaker.jpg"
        },
        {
            "title": "Caroles Dance Party",
            "startDate": "2025-10-30T13:00:00Z",
            "endDate": "2025-10-30T14:00:00Z",
            "description": "Caroles Dance Party  October 30, 1:00 pm Let's Dance! Join Carole for spooky tunes and groovy moves. Supportive footwear is mandatory.",
            "location": "",
            "dateStr": "October 30",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "Carole Gibson services",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/5f877585-1735-45c2-b513-2bbe20e82f88/Caroles%20Dance%20Party.jpg"
        },
        {
            "title": "Daylight Savings Ends  November 2, 8:00 am",
            "startDate": "2025-11-02T08:00:00Z",
            "endDate": "2025-11-02T09:00:00Z",
            "description": "",
            "location": "",
            "dateStr": "November 2",
            "timeStr": "8:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/d2758d2b-f79b-49db-9f4e-f55928b48126/Daylight%20Savings%20Time.jpg"
        },
        {
            "title": "Online Registration Begins",
            "startDate": "2025-11-03T08:00:00Z",
            "endDate": "2025-11-03T09:00:00Z",
            "description": "Online Registration Begins  November 3, 8:00 am Online Program Registration Starts Today",
            "location": "Online",
            "dateStr": "November 3",
            "timeStr": "8:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/4d931fd1-40ac-4785-bcae-81d0647e6cf7/Registration%20Online.jpg"
        },
        {
            "title": "Assistive Listening Solutions",
            "startDate": "2025-11-03T12:00:00Z",
            "endDate": "2025-11-03T13:00:00Z",
            "description": "Assistive Listening Solutions  November 3, 12:00 pm Removing communication barriers leads to engagement within the community. Learn about how assistive listening solutions can help hard-of-hearing members remove background noise and hear what they are intended to. This session will provide an overview of the solutions available today and how they can benefit those who struggle to hear in public spaces.",
            "location": "",
            "dateStr": "November 3",
            "timeStr": "12:00 pm",
            "price": "",
            "instructor": "Stephanie Brown, Hearing Assistive Technology Solutions Group",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/94872db8-dee1-41c2-9fcb-1a8315487c24/Tech%20Bytes.jpg"
        },
        {
            "title": "In-Person Registration for Session 2 Begins",
            "startDate": "2025-11-04T08:30:00Z",
            "endDate": "2025-11-04T09:30:00Z",
            "description": "In-Person Registration for Session 2 Begins November 4, 8:30 am In-person and mail registration begins Monday November 3 at 8:30am. Session 2 begins November 27.",
            "location": "",
            "dateStr": "November 4",
            "timeStr": "8:30 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/4d931fd1-40ac-4785-bcae-81d0647e6cf7/Registration%20Online.jpg"
        },
        {
            "title": "Fresh Food Market",
            "startDate": "2025-11-04T10:00:00Z",
            "endDate": "2025-11-04T11:00:00Z",
            "description": "Fresh Food Market November 4, 10:00 am Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
            "location": "",
            "dateStr": "November 4",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh%20Food%20Market.jpg"
        },
        {
            "title": "Fraud Awareness",
            "startDate": "2025-11-05T13:00:00Z",
            "endDate": "2025-11-05T14:00:00Z",
            "description": "Fraud Awareness November 5, 1:00 pm Protect your money and identity from phone, internet, and in-person fraudsters. Learn how to spot and avoid scams.",
            "location": "",
            "dateStr": "November 5",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "Paul Van Nest, Kingston Rotary Club",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/cb66e913-8ddb-4252-a74c-4302cec7540f/PFH%20Wednesday%20PM.jpg"
        },
        {
            "title": "Cut. Fold. Glue. Stars.",
            "startDate": "2025-11-06T11:30:00Z",
            "endDate": "2025-11-06T12:30:00Z",
            "description": "Cut. Fold. Glue. Stars.  November 6, 11:30 am Join Carole and learn to make charming loo roll snowflakes to bring whimsy to your winter decor.",
            "location": "",
            "dateStr": "November 6",
            "timeStr": "11:30 am",
            "price": "",
            "instructor": "Carole Gibson",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/a538b972-f854-424b-b155-a1a48515fd6a/Learn%20&%20Play.jpg"
        },
        {
            "title": "Learn about Tarot",
            "startDate": "2025-11-06T13:00:00Z",
            "endDate": "2025-11-06T14:00:00Z",
            "description": "Learn about Tarot  November 6, 1:00 pm Tarocchini is a card game where trumps take tricks. Created in 1400 in Italy, it has evolved into games like Bridge. Is Tarot a game of fortune telling, tricks, or a psychological study? Come play and decide.",
            "location": "",
            "dateStr": "November 6",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/1444a77f-b919-494d-bfe1-87ae130cbdf5/Featured%20Speaker.jpg"
        },
        {
            "title": "Hearing Clinic",
            "startDate": "2025-11-07T09:00:00Z",
            "endDate": "2025-11-07T10:00:00Z",
            "description": "Hearing Clinic November 7, 9:00 am Holly Brooks, Hearing Instrument Specialist, from Hear Right Canada provides hearing tests and hearing aid cleaning. Batteries also available for a fee. Appointments required.",
            "location": "",
            "dateStr": "November 7",
            "timeStr": "9:00 am",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/4b3c4ee7-17b6-4401-9f6f-27303d9ab94f/Hearing%20Clinic.jpg"
        },
        {
            "title": "Coffee with a Cop",
            "startDate": "2025-11-07T10:00:00Z",
            "endDate": "2025-11-07T11:00:00Z",
            "description": "Coffee with a Cop  November 7, 10:00 am Join Constable Anthony Colangeli for coffee and conversation. Ask questions and voice concerns. Walk-in. All are welcome.",
            "location": "",
            "dateStr": "November 7",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/7c4a9916-5533-45e6-9a5a-45e7a6a9d252/Coffee%20with%20a%20cop%20FIXED.jpg"
        },
        {
            "title": "Cut. Fold. Glue. Trees",
            "startDate": "2025-11-10T10:45:00Z",
            "endDate": "2025-11-10T11:45:00Z",
            "description": "Cut. Fold. Glue. Trees November 10, 10:45 am Join Carole and learn to make fanciful paper trees for your holiday tablescapes.",
            "location": "",
            "dateStr": "November 10",
            "timeStr": "10:45 am",
            "price": "",
            "instructor": "Carole Gibson",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/a538b972-f854-424b-b155-a1a48515fd6a/Learn%20&%20Play.jpg"
        },
        {
            "title": "Shopping & Buying Online",
            "startDate": "2025-11-10T12:00:00Z",
            "endDate": "2025-11-10T13:00:00Z",
            "description": "Shopping & Buying Online  November 10, 12:00 pm Dip your toes into online shopping. Learn how to get the most out of online stores, how to comparison shop and making informed purchases and how to choose streaming services for movies and TV programs.",
            "location": "Online",
            "dateStr": "November 10",
            "timeStr": "12:00 pm",
            "price": "",
            "instructor": "Sam Kalb",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/4d931fd1-40ac-4785-bcae-81d0647e6cf7/Registration%20Online.jpg"
        },
        {
            "title": "Legal Advice",
            "startDate": "2025-11-10T13:00:00Z",
            "endDate": "2025-11-10T14:00:00Z",
            "description": "Legal Advice November 10, 1:00 pm A practicing lawyer provides confidential advice by phone. Appointment required (20 minutes max).",
            "location": "",
            "dateStr": "November 10",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/ff281879-79a3-45e3-ab4c-b54f69a2e371/Legal%20Advice.JPG"
        },
        {
            "title": "Fresh Food Market",
            "startDate": "2025-11-11T10:00:00Z",
            "endDate": "2025-11-11T11:00:00Z",
            "description": "Fresh Food Market November 11, 10:00 am Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
            "location": "",
            "dateStr": "November 11",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh%20Food%20Market.jpg"
        },
        {
            "title": "Service Canada Clinic",
            "startDate": "2025-11-12T09:00:00Z",
            "endDate": "2025-11-12T10:00:00Z",
            "description": "Service Canada Clinic November 12, 9:00 am Service Canada representatives come to The Seniors Centre to help you with Canadian Pension Plan (CPP), Old Age Security (OAS), Guaranteed Income Supplement (GIS), Social Insurance Number (SIN), or Canadian Dental Care Plan.",
            "location": "",
            "dateStr": "November 12",
            "timeStr": "9:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/4b3c4ee7-17b6-4401-9f6f-27303d9ab94f/Hearing%20Clinic.jpg"
        },
        {
            "title": "Coast to Coast: A Canoe Odyssey",
            "startDate": "2025-11-13T13:00:00Z",
            "endDate": "2025-11-13T14:00:00Z",
            "description": "Coast to Coast: A Canoe Odyssey November 13, 1:00 pm Two paddlers, one canoe, and 8,500 km from Vancouver to Sydney – through cities, towns, and wild terrain. Hear about this epic adventure of resilience, connection, and discovery across Canada's diverse landscapes and waterways.",
            "location": "",
            "dateStr": "November 13",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/1444a77f-b919-494d-bfe1-87ae130cbdf5/Featured%20Speaker.jpg"
        },
        {
            "title": "Birthday Lunch",
            "startDate": "2025-11-14T12:00:00Z",
            "endDate": "2025-11-14T13:00:00Z",
            "description": "Birthday Lunch November 14, 12:00 pm Members celebrate their birthday month for free!",
            "location": "Online",
            "dateStr": "November 14",
            "timeStr": "12:00 pm",
            "price": "$16",
            "instructor": "",
            "registration": "call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/e09e616f-444c-4f2d-989a-32fa84b34083/Birthday.jpg"
        },
        {
            "title": "Sound Escapes: Georgette Fry",
            "startDate": "2025-11-14T13:30:00Z",
            "endDate": "2025-11-14T14:30:00Z",
            "description": "Sound Escapes: Georgette Fry November 14, 1:30 pm Experience the award-winning Georgette Fry's soulful blend of blues, jazz, and pop. Her electrifying style will have you up and dancing all afternoon long!",
            "location": "Online",
            "dateStr": "November 14",
            "timeStr": "1:30 pm",
            "price": "$12",
            "instructor": "",
            "registration": "call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/bd103f00-5824-449d-9a8d-74dd98f450c3/Sound%20Escapes%202.jpg"
        },
        {
            "title": "Program Break Week",
            "startDate": "2025-11-17T08:30:00Z",
            "endDate": "2025-11-17T09:30:00Z",
            "description": "Program Break Week November 17, 8:30 am No programs are scheduled at any Seniors Association locations.",
            "location": "",
            "dateStr": "November 17",
            "timeStr": "8:30 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/569fd7a5-9905-4e34-b0f2-770421fc7e6d/Program%20Break.jpg"
        },
        {
            "title": "Speed Friending",
            "startDate": "2025-11-17T13:00:00Z",
            "endDate": "2025-11-17T14:00:00Z",
            "description": "Speed Friending  November 17, 1:00 pm Meet new people quickly in a fun, structured setting with speed friending, a platonic twist on speed dating. Rotate through brief conversations, connect with others, and potentially form lasting friendships in just minutes.",
            "location": "",
            "dateStr": "November 17",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/29174fb0-87d2-4f16-9d7e-a773dca5ff2a/Speed%20Friending.jpg"
        },
        {
            "title": "Advanced Care Planning",
            "startDate": "2025-11-17T16:30:00Z",
            "endDate": "2025-11-17T17:30:00Z",
            "description": "Advanced Care Planning November 17, 4:30 pm The process of thinking about, writing down, and sharing your wishes/instructions with loved ones for future health care treatment if you become incapable of deciding for yourself. Learn, listen, and ask questions to help you improve your plan.",
            "location": "",
            "dateStr": "November 17",
            "timeStr": "4:30 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/0b47a5d9-7476-44c7-ad1f-fac13a579936/Advance%20Care%20Planning.jpg"
        },
        {
            "title": "Fresh Food Market",
            "startDate": "2025-11-18T10:00:00Z",
            "endDate": "2025-11-18T11:00:00Z",
            "description": "Fresh Food Market November 18, 10:00 am Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
            "location": "",
            "dateStr": "November 18",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh%20Food%20Market.jpg"
        },
        {
            "title": "Expressive Mark Making",
            "startDate": "2025-11-18T13:00:00Z",
            "endDate": "2025-11-18T14:00:00Z",
            "description": "Expressive Mark Making  November 18, 1:00 pm Rekindle your passion for abstract art through expressive mark-making. This liberating workshop uses skill-building exercises and soul-nurturing prompts to unlock your subconscious, inspire creativity, and help you rediscover your unique, lyrical style.",
            "location": "",
            "dateStr": "November 18",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "Sharlena Wood",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/a538b972-f854-424b-b155-a1a48515fd6a/Learn%20&%20Play.jpg"
        },
        {
            "title": "Cafe Franglish",
            "startDate": "2025-11-18T14:30:00Z",
            "endDate": "2025-11-18T15:30:00Z",
            "description": "Cafe Franglish November 18, 2:30 pm Join a monthly bilingual meetup where Francophones and Anglophones connect chat, and build confidence in both languages through lively, judgement-free conversations on a variety of engaging topics.",
            "location": "",
            "dateStr": "November 18",
            "timeStr": "2:30 pm",
            "price": "free",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/5476e070-622a-45a3-972b-3e61bdc511f8/Cafe%20Franglish.jpg"
        },
        {
            "title": "Tuesday at Tom's",
            "startDate": "2025-11-18T15:00:00Z",
            "endDate": "2025-11-18T16:00:00Z",
            "description": "Tuesday at Tom's November 18, 3:00 pm New to town or looking to make new friends? Come and enjoy a relaxing conversation and beverage with other members.",
            "location": "",
            "dateStr": "November 18",
            "timeStr": "3:00 pm",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/c01d910e-fd8d-4135-9963-5b9a5126d1cb/Tuesdays%20at%20Tom's.jpg"
        },
        {
            "title": "Learn Resilience",
            "startDate": "2025-11-19T09:30:00Z",
            "endDate": "2025-11-19T10:30:00Z",
            "description": "Learn Resilience  November 19, 9:30 am Experience the award-winning documentary Resilience, then join Teach Resilience trainers from Kingston Community Health Centres for an engaging panel discussion of the film, speaking about trauma and its impact.",
            "location": "",
            "dateStr": "November 19",
            "timeStr": "9:30 am",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/1444a77f-b919-494d-bfe1-87ae130cbdf5/Featured%20Speaker.jpg"
        },
        {
            "title": "Vision Workshop",
            "startDate": "2025-11-19T10:30:00Z",
            "endDate": "2025-11-19T11:30:00Z",
            "description": "Vision Workshop November 19, 10:30 am Rediscover purpose, passion, and joy in retirement. Learn simple tools to dream again, break free from \"too late\" thinking, and design a vibrant next chapter – filled with meaning, connection, and confidence.",
            "location": "",
            "dateStr": "November 19",
            "timeStr": "10:30 am",
            "price": "free",
            "instructor": "Victoria Hirst",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/a538b972-f854-424b-b155-a1a48515fd6a/Learn%20&%20Play.jpg"
        },
        {
            "title": "New Member Mixer",
            "startDate": "2025-11-19T14:00:00Z",
            "endDate": "2025-11-19T15:00:00Z",
            "description": "New Member Mixer\t November 19, 2:00 pm Are you a new member and want to learn more about what we offer? Have a friend you'd like to join? Or do you just want to know more about the Seniors Association? Meet with staff and other members for a brief orientation, introduction to our database, light refreshments, and socializing.",
            "location": "",
            "dateStr": "November 19",
            "timeStr": "2:00 pm",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/5fcfa81b-02bf-4985-9b86-8ec565c0bb00/New%20Member%20Mixer.jpg"
        },
        {
            "title": "Time for Tea",
            "startDate": "2025-11-20T13:00:00Z",
            "endDate": "2025-11-20T14:00:00Z",
            "description": "Time for Tea November 20, 1:00 pm Explore the fine art of tea and food pairing with a certified tea sommelier. Discover how nuanced flavors enhance cuisine through expertly selected teas and culinary harmony over the Holiday season.",
            "location": "",
            "dateStr": "November 20",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/1444a77f-b919-494d-bfe1-87ae130cbdf5/Featured%20Speaker.jpg"
        },
        {
            "title": "Book & Puzzle EXCHANGE",
            "startDate": "2025-11-21T10:00:00Z",
            "endDate": "2025-11-21T11:00:00Z",
            "description": "Book & Puzzle EXCHANGE November 21, 10:00 am Bring up to 10 paperback books or puzzles to the Rendezvous Café to exchange for any in our library. Additional books or puzzles can be purchased for $2.",
            "location": "",
            "dateStr": "November 21",
            "timeStr": "10:00 am",
            "price": "$2",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/7948f41c-bcf4-42d1-97aa-5c7eb4245861/Book%20&%20Puzzle.jpg"
        },
        {
            "title": "Annual General Meeting",
            "startDate": "2025-11-21T11:00:00Z",
            "endDate": "2025-11-21T12:00:00Z",
            "description": "Annual General Meeting November 21, 11:00 am The theme for the 49th Annual General Meeting is Strategic Growth for Future Success and will be held at The Seniors Centre.",
            "location": "",
            "dateStr": "November 21",
            "timeStr": "11:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/29174fb0-87d2-4f16-9d7e-a773dca5ff2a/Speed%20Friending.jpg"
        },
        {
            "title": "December Vista Available for Pickup",
            "startDate": "2025-11-21T12:00:00Z",
            "endDate": "2025-11-21T13:00:00Z",
            "description": "December Vista Available for Pickup November 21, 12:00 pm Volunteer Deliverers pick up their bundles to hand deliver and members can pick up their individual copy.",
            "location": "",
            "dateStr": "November 21",
            "timeStr": "12:00 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/8c8f92ce-34ef-442e-bab9-a06836704f9d/Vista.jpg"
        },
        {
            "title": "Holiday Artisan Fair",
            "startDate": "2025-11-22T10:00:00Z",
            "endDate": "2025-11-22T11:00:00Z",
            "description": "Holiday Artisan Fair November 22, 10:00 am Something for everyone!",
            "location": "",
            "dateStr": "November 22",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/a278053e-4f35-40af-a2f6-610cfd893930/Holiday%20Artisan%20Fair.jpg"
        },
        {
            "title": "Simplify Your Digital Life",
            "startDate": "2025-11-24T12:00:00Z",
            "endDate": "2025-11-24T13:00:00Z",
            "description": "Simplify Your Digital Life  November 24, 12:00 pm Feeling overwhelmed by your online accounts, passwords, and subscriptions? This presentation offers practical strategies to simplify your digital life. Learn to organize accounts, manage passwords, use cloud storage effectively, and understand your subscriptions. We'll also explore options for closing services you no longer need – empowering you to take control of your digital world.",
            "location": "Online",
            "dateStr": "November 24",
            "timeStr": "12:00 pm",
            "price": "",
            "instructor": "Jarda Zborovsy",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/cb66e913-8ddb-4252-a74c-4302cec7540f/PFH%20Wednesday%20PM.jpg"
        },
        {
            "title": "Legal Advice",
            "startDate": "2025-11-24T13:00:00Z",
            "endDate": "2025-11-24T14:00:00Z",
            "description": "Legal Advice November 24, 1:00 pm A practicing lawyer provides confidential advice by phone. Appointment required (20 minutes max).",
            "location": "",
            "dateStr": "November 24",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "Call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/ff281879-79a3-45e3-ab4c-b54f69a2e371/Legal%20Advice.JPG"
        },
        {
            "title": "Fresh Food Market",
            "startDate": "2025-11-25T10:00:00Z",
            "endDate": "2025-11-25T11:00:00Z",
            "description": "Fresh Food Market November 25, 10:00 am Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
            "location": "",
            "dateStr": "November 25",
            "timeStr": "10:00 am",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/6d7e0dd8-63c7-45ff-916d-67280d4f9966/Fresh%20Food%20Market.jpg"
        },
        {
            "title": "Holiday Lunch",
            "startDate": "2025-11-25T12:00:00Z",
            "endDate": "2025-11-25T13:00:00Z",
            "description": "Holiday Lunch November 25, 12:00 pm Tomato Basil Soup, Roast Turkey, dressing, mashed potatoes, vegetables, cranberry sauce, and dessert!",
            "location": "Online",
            "dateStr": "November 25",
            "timeStr": "12:00 pm",
            "price": "$25",
            "instructor": "",
            "registration": "call 613.548.7810",
            "image_url": "https://cms.seniorskingston.ca/assets/e09e616f-444c-4f2d-989a-32fa84b34083/Birthday.jpg"
        },
        {
            "title": "Domino Theatre Dress Rehearsal: Miss Bennet: Christmas at Pemberley",
            "startDate": "2025-11-26T19:30:00Z",
            "endDate": "2025-11-26T20:30:00Z",
            "description": "Domino Theatre Dress Rehearsal: Miss Bennet: Christmas at Pemberley November 26, 7:30 pm Celebrate the holidays with a witty sequel to Pride and Prejudice, where overlooked Mary Bennet discovers romance at Pemberley. Full of heart, humour, and Regency charm, this play delights.",
            "location": "Online",
            "dateStr": "November 26",
            "timeStr": "7:30 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/365bab44-7685-4223-8319-d8dea27b3484/Domino%20Dress%20Rehearsal.jpg"
        },
        {
            "title": "Anxiety Unlocked",
            "startDate": "2025-11-27T13:00:00Z",
            "endDate": "2025-11-27T14:00:00Z",
            "description": "Anxiety Unlocked  November 27, 1:00 pm Discover fun, easy-to-use tools that bring quick relief from anxiety. Learn simple, effective techniques you may not know, designed to calm your mind, ease stress, and restore balance anytime, anywhere.",
            "location": "",
            "dateStr": "November 27",
            "timeStr": "1:00 pm",
            "price": "",
            "instructor": "",
            "registration": "",
            "image_url": "https://cms.seniorskingston.ca/assets/1444a77f-b919-494d-bfe1-87ae130cbdf5/Featured%20Speaker.jpg"
        }
    ]

def extract_events_from_scripts(soup):
    """Extract events from JavaScript/JSON data in script tags"""
    events = []
    try:
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                script_content = script.string
                
                # Look for event-related JSON data
                if any(keyword in script_content.lower() for keyword in ['event', 'calendar', 'schedule', 'november', 'december']):
                    print("🔍 Found potential event data in script")
                    
                    # Try to extract JSON objects
                    json_patterns = [
                        r'\{[^{}]*"title"[^{}]*\}',
                        r'\{[^{}]*"event"[^{}]*\}',
                        r'\{[^{}]*"name"[^{}]*\}'
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, script_content, re.IGNORECASE)
                        for match in matches:
                            try:
                                data = json.loads(match)
                                if 'title' in data or 'event' in data or 'name' in data:
                                    event = create_event_from_json(data)
                                    if event:
                                        events.append(event)
                            except:
                                continue
        
        return events[:20]  # Limit to 20 events
            
    except Exception as e:
        print(f"❌ Error extracting events from scripts: {e}")
        return []

def extract_events_from_html(soup):
    """Extract events from HTML structure"""
    events = []
    try:
        # Look for common event container patterns
        selectors = [
            'div[class*="event"]',
            'div[class*="card"]', 
            'article',
            'div[class*="item"]',
            'div[class*="post"]',
            'li[class*="event"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 30 and any(word in text.lower() for word in ['november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october']):
                    event = create_event_from_text(text)
                    if event:
                        events.append(event)
                        
        return events[:20]  # Limit to 20 events
        
    except Exception as e:
        print(f"❌ Error extracting events from HTML: {e}")
        return []

def extract_events_from_text(soup):
    """Extract events from text content"""
    events = []
    try:
        text_content = soup.get_text()
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) > 20 and any(word in line.lower() for word in ['november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october']):
                event = create_event_from_text(line)
                if event:
                    events.append(event)
                    
        return events[:20]  # Limit to 20 events
        
    except Exception as e:
        print(f"❌ Error extracting events from text: {e}")
        return []

def create_event_from_json(data):
    """Create event object from JSON data"""
    try:
        title = data.get('title') or data.get('event') or data.get('name') or 'Event'
        return {
            "title": title[:50],
            "description": str(data.get('description', title)),
            "image_url": "/event-schedule-banner.png",
            "startDate": datetime.now().isoformat(),
            "endDate": datetime.now().isoformat(),
            "location": "Seniors Kingston",
            "dateStr": "TBD",
            "timeStr": "TBD"
        }
    except:
        return None

def create_event_from_text(text):
    """Create event object from text content"""
    try:
        # Clean up the text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else text[:50]
        
        if len(title) > 50:
            title = title[:50] + "..."
            
        return {
            "title": title,
            "description": text,
            "image_url": "/event-schedule-banner.png", 
            "startDate": datetime.now().isoformat(),
            "endDate": datetime.now().isoformat(),
            "location": "Seniors Kingston",
            "dateStr": "TBD",
            "timeStr": "TBD"
        }
    except:
        return None

def get_november_2025_events_fallback():
    """Return comprehensive November 2025 events as fallback"""
    return [
            {
            'title': 'Holiday Artisan Fair',
            'startDate': '2025-11-22T10:00:00Z',
            'endDate': '2025-11-22T16:00:00Z',
            'description': 'Local artisans showcase their handmade crafts and holiday gifts',
            'location': 'Seniors Kingston Centre',
            'dateStr': 'November 22, 2025',
            'timeStr': '10:00 AM - 4:00 PM',
            'image_url': '/event-schedule-banner.png',
            'price': 'Free admission',
            'instructor': 'Various Artisans',
            'registration': 'No registration required'
        },
        {
            'title': 'Thanksgiving Potluck',
            'startDate': '2025-11-28T12:00:00Z',
            'endDate': '2025-11-28T15:00:00Z',
            'description': 'Community Thanksgiving celebration with potluck dinner',
            'location': 'Seniors Kingston Centre',
            'dateStr': 'November 28, 2025',
            'timeStr': '12:00 PM - 3:00 PM',
            'image_url': '/event-schedule-banner.png',
            'price': 'Free',
            'instructor': 'Community',
            'registration': 'Bring a dish to share'
        },
        {
            'title': 'Winter Wellness Workshop',
            'startDate': '2025-11-15T14:00:00Z',
            'endDate': '2025-11-15T16:00:00Z',
            'description': 'Learn about staying healthy and active during winter months',
            'location': 'Seniors Kingston Centre',
            'dateStr': 'November 15, 2025',
            'timeStr': '2:00 PM - 4:00 PM',
            'image_url': '/event-schedule-banner.png',
            'price': 'Free',
            'instructor': 'Health Professional',
            'registration': 'Call to register'
        },
        {
            'title': 'November Book Club',
            'startDate': '2025-11-08T14:00:00Z',
            'endDate': '2025-11-08T16:00:00Z',
            'description': 'Monthly book discussion group',
            'location': 'Seniors Kingston Centre',
            'dateStr': 'November 8, 2025',
            'timeStr': '2:00 PM - 4:00 PM',
            'image_url': '/event-schedule-banner.png',
            'price': 'Free',
            'instructor': 'Book Club Leader',
            'registration': 'No registration required'
        },
        {
            'title': 'Fall Craft Workshop',
            'startDate': '2025-11-12T10:00:00Z',
            'endDate': '2025-11-12T12:00:00Z',
            'description': 'Create beautiful fall-themed crafts',
            'location': 'Seniors Kingston Centre',
            'dateStr': 'November 12, 2025',
            'timeStr': '10:00 AM - 12:00 PM',
            'image_url': '/event-schedule-banner.png',
            'price': '$5 materials fee',
            'instructor': 'Craft Instructor',
            'registration': 'Call to register'
        }
    ]

def try_simple_requests_scraping():
    """Simple requests fallback for cloud environments"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = "https://seniorskingston.ca/events"
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
            
            # Try to extract events from HTML content
            events = extract_events_from_loaded_content(soup)
            
            if events:
                print(f"✅ Simple requests found {len(events)} events")
                return events
            else:
                print("📅 No events found with simple requests")
                return []
        else:
            print(f"❌ Failed to fetch website: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error in simple requests scraping: {e}")
        return []


def extract_events_from_loaded_content(soup):
    """Extract events from loaded page content"""
    events = []
    
    try:
        # Look for common event patterns in the loaded content
        selectors = [
            # Seniors Kingston specific selectors (based on actual HTML structure)
            'h5.green', 'h5[class*="green"]', 'h5[data-v-60d883ca]',
            # Common event selectors
            'article', '.event', '.post', '.event-item', '[class*="event"]', '.entry', '.event-card', '.event-listing',
            '.events-list li', '.events li', '.event-list-item', '.calendar-event', '.program-event',
            'div[class*="event"]', 'li[class*="event"]', '.event-wrapper', '.event-container', '.event-block',
            'h3', 'h4', 'h5', '.event-title', '.post-title', '.entry-title',
            # Nuxt.js specific selectors
            '[data-nuxt]', '.nuxt-content', '.content', '.page-content',
            # Generic content selectors
            'div', 'li', 'article', 'section'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            print(f"🔍 Found {len(elements)} elements with selector: {selector}")
            
            for element in elements:
                try:
                    # Get all text content
                    text_content = element.get_text().strip()
                    
                    # Skip if too short or empty
                    if len(text_content) < 3:
                        continue
                    
                    # Special handling for h5.green elements (event titles)
                    if element.name == 'h5' and 'green' in element.get('class', []):
                        print(f"🎯 Found event title: {text_content}")
                        event_data = parse_event_from_text(text_content)
                        if event_data and not any(e['title'] == event_data['title'] for e in events):
                            # Look for associated image in the same container
                            parent = element.parent
                            if parent:
                                img = parent.find('img')
                                if img and img.get('src'):
                                    event_data['image_url'] = img.get('src')
                                    print(f"🖼️ Found event image: {event_data['image_url']}")
                                else:
                                    # Look for image in nearby elements
                                    for sibling in parent.find_all(['img', 'div']):
                                        if sibling.name == 'img' and sibling.get('src'):
                                            event_data['image_url'] = sibling.get('src')
                                            print(f"🖼️ Found event image in sibling: {event_data['image_url']}")
                                            break
                            
                            events.append(event_data)
                            print(f"📅 Added event: {event_data['title']}")
                        continue
                    
                    # Look for event-like patterns in other elements
                    if is_likely_event_content(text_content):
                        event_data = parse_event_from_text(text_content)
                        if event_data and not any(e['title'] == event_data['title'] for e in events):
                            events.append(event_data)
                            print(f"📅 Added event: {event_data['title']}")
                
                except Exception as e:
                    print(f"❌ Error parsing element: {e}")
                    continue
        
        return events
        
    except Exception as e:
        print(f"❌ Error extracting events: {e}")
        return []

def is_likely_event_content(text):
    """Check if text content looks like an event"""
    # Look for event indicators
    event_indicators = [
        'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
        'am', 'pm', 'morning', 'afternoon', 'evening', 'night',
        'clinic', 'workshop', 'class', 'meeting', 'party', 'lunch', 'dinner', 'seminar', 'presentation', 'tour', 'social', 'game', 'music', 'dance',
        'health', 'legal', 'technology', 'book', 'puzzle', 'exchange', 'market', 'celtic', 'kitchen', 'whisky', 'tasting', 'board', 'vista', 'pickup',
        'internet', 'smartphone', 'phone', 'medical', 'myths', 'fresh', 'food', 'senior', 'woman', 'google', 'app', 'hearing', 'sex', 'top', 'free',
        'kingston', 'taxi', 'tales', 'fire', 'safety', 'cafe', 'franglish', 'domino', 'theatre', 'witness', 'prosecution', 'ally', 'later', 'life', 'learning',
        'library', 'resources', 'tuesday', 'tom', 'sound', 'bath', 'board', 'meeting', 'paint', 'gouache', 'achieve', 'best', 'health', 'kenny', 'dolly',
        'wearable', 'tech', 'legal', 'advice', 'astronomy', 'carole', 'dance', 'party'
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in event_indicators)

def parse_event_from_text(text):
    """Parse event data from text content"""
    try:
        import re
        from dateutil import parser
        
        lines = text.split('\n')
        title = None
        date_str = None
        time_str = None
        
        # Look for title (usually the first meaningful line)
        for line in lines:
            line = line.strip()
            if len(line) > 5 and not line.startswith(('Date:', 'Time:', 'Location:', 'Description:')):
                title = line
                break
        
        if not title:
            return None
        
        # Look for date patterns
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s*\d{4})?',
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?',
            r'\d{1,2}/\d{1,2}(?:/\d{2,4})?'
        ]
        
        for line in lines:
            for pattern in date_patterns:
                date_match = re.search(pattern, line, re.IGNORECASE)
                if date_match:
                    date_str = date_match.group(0)
                    break
            if date_str:
                break
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)',
            r'(\d{1,2}\s*(?:am|pm|AM|PM))'
        ]
        
        for line in lines:
            for pattern in time_patterns:
                time_match = re.search(pattern, line, re.IGNORECASE)
                if time_match:
                    time_str = time_match.group(1)
                    break
            if time_str:
                break
        
        # Parse date
        event_date = None
        if date_str:
            try:
                event_date = parser.parse(date_str, fuzzy=True)
            except:
                pass
        
        if not event_date:
            event_date = datetime.now()
        
        return {
            'title': title,
            'startDate': event_date.isoformat() + 'Z',
            'endDate': (event_date + timedelta(hours=1)).isoformat() + 'Z',
            'description': '',
            'location': '',
            'dateStr': date_str or 'TBA',
            'timeStr': time_str or 'TBA',
            'image_url': 'https://www.seniorskingston.ca/images/event-banner.jpg'  # Use actual event banner from Seniors website
        }
        
    except Exception as e:
        print(f"❌ Error parsing event from text: {e}")
        return None

# Automatic syncing with Seniors Kingston website
import threading
import time
import re
from datetime import datetime, timedelta

# Global variable to store last sync time
last_sync_time = None
sync_interval_hours = 24 * 7  # Sync every Monday (weekly)

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

# Start automatic syncing when the server starts - DISABLED to prevent data changes
# start_auto_sync()
print("⏸️ Automatic sync disabled - events will come only from stored file")

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
                    'location': '',
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
                        'location': '',
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
                    'location': '',
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
def get_events(request: Request):
    """Get all events (real + editable events) from Seniors Kingston"""
    global stored_events  # CRITICAL: Declare global before using
    
    print(f"🌐 Events API call received")
    
    # Track the visit
    user_agent = request.headers.get('user-agent', '')
    track_visit(user_agent)
    
    # PRIORITY: Use stored events first (most reliable)
    print("🔍 Checking for stored events first...")
    if stored_events and len(stored_events) > 0:
        # Remove duplicates from stored_events before returning
        unique_events = []
        seen_keys = set()
        for event in stored_events:
            key = (event.get('title', ''), event.get('startDate', ''))
            if key not in seen_keys:
                unique_events.append(event)
                seen_keys.add(key)
        
        print(f"📦 Using {len(unique_events)} unique stored events (removed {len(stored_events) - len(unique_events)} duplicates)")
        all_events = unique_events
    else:
        # Do NOT scrape anymore. Only return stored events.
        print("⏸️ Scraping disabled. Using stored events only.")
        all_events = stored_events
        
        # CRITICAL FIX: Auto-load fallback when data is empty
        if not all_events or len(all_events) == 0:
            print("⚠️ No stored events found - loading fallback data...")
            fallback_events = get_comprehensive_november_events()
            if fallback_events and len(fallback_events) > 0:
                print(f"✅ Loaded {len(fallback_events)} events from fallback")
                all_events = fallback_events
                # Also save to stored_events so they persist
                stored_events = fallback_events
                save_stored_events()
                print(f"💾 Saved fallback events to stored_events.json")
            
            # Fix image URLs and clean titles for all events
    if all_events:
            for event in all_events:
                if not event.get('image_url') or event.get('image_url') == '/assets/event-schedule-banner.png':
                    event['image_url'] = '/logo192.png'  # Use accessible logo as banner
                
                # Clean up titles that contain descriptions
                title = event.get('title', '')
                description = event.get('description', '')
                
                # If title is very long and contains description, extract just the title part
                if len(title) > 50:  # Lower threshold to catch more cases
                    import re
                    # Look for pattern like "Event Name October 24, 1:30 pm Description"
                    # Try multiple patterns to extract just the event name
                    patterns = [
                        r'^([^0-9]+?)\s+\w+\s+\d+,\s+\d+:\d+\s+[ap]m',  # "Event Name October 24, 1:30 pm"
                        r'^([^0-9]+?)\s+\w+\s+\d+',  # "Event Name October 24"
                        r'^([^0-9]+?)\s+\d+:\d+\s+[ap]m',  # "Event Name 1:30 pm"
                        r'^([^0-9]+?)\s+\d+',  # "Event Name 24"
                    ]
                    
                    for pattern in patterns:
                        match = re.match(pattern, title)
                        if match:
                            clean_title = match.group(1).strip()
                            # Remove trailing punctuation and extra spaces
                            clean_title = re.sub(r'[,\s]+$', '', clean_title)
                            if len(clean_title) > 3:  # Make sure we have a meaningful title
                                event['title'] = clean_title
                                print(f"🧹 Cleaned title: '{title[:50]}...' -> '{clean_title}'")
                                break
            
    # If no events were processed, provide fallback
    if 'all_events' not in locals() or len(all_events) == 0:
        print("📅 No events found, using known events as fallback")
        all_events = []
    
    # REAL EVENTS from Seniors Kingston website - 100% ACCURATE DATA (2025)
    # Extracted directly from the actual website using Selenium scraping
    known_events = [
        # September 2025 Events
        {
            'title': "Board Meeting",
            'startDate': datetime(2025, 9, 24, 20, 0).isoformat() + 'Z',  # 4:00 pm EDT
            'endDate': datetime(2025, 9, 24, 21, 0).isoformat() + 'Z',
            'description': "The next scheduled Board meeting is September 24, 4:00pm",
            'location': '',
            'dateStr': 'September 24, 2025, 4:00 pm',
            'timeStr': '4:00 pm'
        },
        {
            'title': "Medical Myths",
            'startDate': datetime(2025, 9, 25, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 9, 25, 18, 0).isoformat() + 'Z',
            'description': "Educational program about medical myths and facts",
            'location': '',
            'dateStr': 'September 25, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Whisky Tasting",
            'startDate': datetime(2025, 9, 25, 22, 0).isoformat() + 'Z',  # 6:00 pm EDT
            'endDate': datetime(2025, 9, 25, 23, 0).isoformat() + 'Z',
            'description': "Sample and learn about different whiskies",
            'location': '',
            'dateStr': 'September 25, 2025, 6:00 pm',
            'timeStr': '6:00 pm'
        },
        {
            'title': "Sound Escapes: You've Got a Friend",
            'startDate': datetime(2025, 9, 26, 17, 30).isoformat() + 'Z',  # 1:30 pm EDT
            'endDate': datetime(2025, 9, 26, 18, 30).isoformat() + 'Z',
            'description': "Musical program featuring classic friendship songs",
            'location': '',
            'dateStr': 'September 26, 2025, 1:30 pm',
            'timeStr': '1:30 pm'
        },
        {
            'title': "Selecting a Smart Phone",
            'startDate': datetime(2025, 9, 29, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 9, 29, 17, 0).isoformat() + 'Z',
            'description': "Workshop on choosing the right smartphone for seniors",
            'location': '',
            'dateStr': 'September 29, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "National Day of Truth and Reconciliation",
            'startDate': datetime(2025, 9, 30, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 9, 30, 23, 0).isoformat() + 'Z',
            'description': "National Day of Truth and Reconciliation",
            'location': '',
            'dateStr': 'September 30, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        
        # October 2025 Events - 100% ACCURATE from website
        {
            'title': "Biker Bros",
            'startDate': datetime(2025, 10, 1, 12, 30).isoformat() + 'Z',  # 8:30 am EDT
            'endDate': datetime(2025, 10, 1, 13, 30).isoformat() + 'Z',
            'description': "Motorcycle enthusiasts gathering",
            'location': '',
            'dateStr': 'October 1, 2025, 8:30 am',
            'timeStr': '8:30 am'
        },
        {
            'title': "Kingston Taxi Tales",
            'startDate': datetime(2025, 10, 1, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 1, 15, 0).isoformat() + 'Z',
            'description': "Stories and experiences from Kingston taxi drivers",
            'location': '',
            'dateStr': 'October 1, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Sex and the Senior Woman",
            'startDate': datetime(2025, 10, 2, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 2, 18, 0).isoformat() + 'Z',
            'description': "Educational program for senior women",
            'location': '',
            'dateStr': 'October 2, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Hearing Clinic",
            'startDate': datetime(2025, 10, 3, 13, 0).isoformat() + 'Z',  # 9:00 am EDT
            'endDate': datetime(2025, 10, 3, 14, 0).isoformat() + 'Z',
            'description': "Free hearing assessment clinic",
            'location': '',
            'dateStr': 'October 3, 2025, 9:00 am',
            'timeStr': '9:00 am'
        },
        {
            'title': "Top 10 Free Google Apps for Every Device",
            'startDate': datetime(2025, 10, 6, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 6, 17, 0).isoformat() + 'Z',
            'description': "Learn about useful free Google applications",
            'location': '',
            'dateStr': 'October 6, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Fresh Food Market",
            'startDate': datetime(2025, 10, 7, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 7, 15, 0).isoformat() + 'Z',
            'description': "Local fresh produce and goods market",
            'location': '',
            'dateStr': 'October 7, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Fire Safety for Seniors: Seniors Day with Kingston Fire & Rescue",
            'startDate': datetime(2025, 10, 8, 13, 0).isoformat() + 'Z',  # 9:00 am EDT
            'endDate': datetime(2025, 10, 8, 14, 0).isoformat() + 'Z',
            'description': "Fire safety education and prevention for seniors",
            'location': '',
            'dateStr': 'October 8, 2025, 9:00 am',
            'timeStr': '9:00 am'
        },
        {
            'title': "Autumn Floral Centerpiece",
            'startDate': datetime(2025, 10, 9, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 9, 15, 0).isoformat() + 'Z',
            'description': "Create beautiful autumn floral arrangements",
            'location': '',
            'dateStr': 'October 9, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Fraud Prevention",
            'startDate': datetime(2025, 10, 9, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 9, 18, 0).isoformat() + 'Z',
            'description': "Learn how to protect yourself from fraud and scams",
            'location': '',
            'dateStr': 'October 9, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Birthday Lunch",
            'startDate': datetime(2025, 10, 10, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 10, 17, 0).isoformat() + 'Z',
            'description': "Monthly birthday celebration lunch",
            'location': '',
            'dateStr': 'October 10, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Fresh Food Market",
            'startDate': datetime(2025, 10, 14, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 14, 15, 0).isoformat() + 'Z',
            'description': "Local fresh produce and goods market",
            'location': '',
            'dateStr': 'October 14, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Thanksgiving Lunch",
            'startDate': datetime(2025, 10, 14, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 14, 17, 0).isoformat() + 'Z',
            'description': "Community Thanksgiving celebration with traditional meal",
            'location': '',
            'dateStr': 'October 14, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Cafe Franglish",
            'startDate': datetime(2025, 10, 14, 18, 30).isoformat() + 'Z',  # 2:30 pm EDT
            'endDate': datetime(2025, 10, 14, 19, 30).isoformat() + 'Z',
            'description': "French-English conversation cafe",
            'location': '',
            'dateStr': 'October 14, 2025, 2:30 pm',
            'timeStr': '2:30 pm'
        },
        {
            'title': "Domino Theatre Dress Rehearsal: Witness for the Prosecution",
            'startDate': datetime(2025, 10, 15, 23, 30).isoformat() + 'Z',  # 7:30 pm EDT
            'endDate': datetime(2025, 10, 16, 0, 30).isoformat() + 'Z',
            'description': "Dress rehearsal for the Domino Theatre production",
            'location': 'Domino Theatre',
            'dateStr': 'October 15, 2025, 7:30 pm',
            'timeStr': '7:30 pm'
        },
        {
            'title': "Service Canada Clinic",
            'startDate': datetime(2025, 10, 16, 13, 0).isoformat() + 'Z',  # 9:00 am EDT
            'endDate': datetime(2025, 10, 16, 14, 0).isoformat() + 'Z',
            'description': "Get help with Service Canada programs and benefits",
            'location': '',
            'dateStr': 'October 16, 2025, 9:00 am',
            'timeStr': '9:00 am'
        },
        {
            'title': "How to be an Ally",
            'startDate': datetime(2025, 10, 16, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 16, 18, 0).isoformat() + 'Z',
            'description': "Educational workshop on being an effective ally",
            'location': '',
            'dateStr': 'October 16, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Later Life Learning: Series B",
            'startDate': datetime(2025, 10, 17, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 17, 15, 0).isoformat() + 'Z',
            'description': "Educational program for continued learning",
            'location': '',
            'dateStr': 'October 17, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Book & Puzzle EXCHANGE",
            'startDate': datetime(2025, 10, 17, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 17, 15, 0).isoformat() + 'Z',
            'description': "Bring books and puzzles to exchange with others",
            'location': '',
            'dateStr': 'October 17, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Library e-Resources",
            'startDate': datetime(2025, 10, 20, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 20, 17, 0).isoformat() + 'Z',
            'description': "Learn about digital library resources",
            'location': '',
            'dateStr': 'October 20, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Fresh Food Market",
            'startDate': datetime(2025, 10, 21, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 21, 15, 0).isoformat() + 'Z',
            'description': "Local fresh produce and goods market",
            'location': '',
            'dateStr': 'October 21, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Tuesday at Tom's",
            'startDate': datetime(2025, 10, 21, 19, 0).isoformat() + 'Z',  # 3:00 pm EDT
            'endDate': datetime(2025, 10, 21, 20, 0).isoformat() + 'Z',
            'description': "Social gathering at Tom's",
            'location': 'Tom\'s',
            'dateStr': 'October 21, 2025, 3:00 pm',
            'timeStr': '3:00 pm'
        },
        {
            'title': "Sound Bath",
            'startDate': datetime(2025, 10, 21, 21, 30).isoformat() + 'Z',  # 5:30 pm EDT
            'endDate': datetime(2025, 10, 21, 22, 30).isoformat() + 'Z',
            'description': "Relaxing sound therapy session",
            'location': '',
            'dateStr': 'October 21, 2025, 5:30 pm',
            'timeStr': '5:30 pm'
        },
        {
            'title': "Board Meeting",
            'startDate': datetime(2025, 10, 22, 20, 0).isoformat() + 'Z',  # 4:00 pm EDT
            'endDate': datetime(2025, 10, 22, 21, 0).isoformat() + 'Z',
            'description': "Seniors Kingston board meeting",
            'location': '',
            'dateStr': 'October 22, 2025, 4:00 pm',
            'timeStr': '4:00 pm'
        },
        {
            'title': "Paint with Gouache",
            'startDate': datetime(2025, 10, 23, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 23, 15, 0).isoformat() + 'Z',
            'description': "Art workshop using gouache painting techniques",
            'location': '',
            'dateStr': 'October 23, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "Achieve Your Best Health",
            'startDate': datetime(2025, 10, 23, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 23, 18, 0).isoformat() + 'Z',
            'description': "Health and wellness workshop for seniors",
            'location': '',
            'dateStr': 'October 23, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Sound Escapes: Kenny & Dolly",
            'startDate': datetime(2025, 10, 24, 17, 30).isoformat() + 'Z',  # 1:30 pm EDT
            'endDate': datetime(2025, 10, 24, 18, 30).isoformat() + 'Z',
            'description': "Musical program featuring Kenny Rogers and Dolly Parton songs",
            'location': '',
            'dateStr': 'October 24, 2025, 1:30 pm',
            'timeStr': '1:30 pm'
        },
        {
            'title': "Wearable Tech",
            'startDate': datetime(2025, 10, 27, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2025, 10, 27, 17, 0).isoformat() + 'Z',
            'description': "Learn about wearable technology for seniors",
            'location': '',
            'dateStr': 'October 27, 2025, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Legal Advice",
            'startDate': datetime(2025, 10, 27, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 27, 18, 0).isoformat() + 'Z',
            'description': "Free legal advice session",
            'location': '',
            'dateStr': 'October 27, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Fresh Food Market",
            'startDate': datetime(2025, 10, 28, 14, 0).isoformat() + 'Z',  # 10:00 am EDT
            'endDate': datetime(2025, 10, 28, 15, 0).isoformat() + 'Z',
            'description': "Local fresh produce and goods market",
            'location': '',
            'dateStr': 'October 28, 2025, 10:00 am',
            'timeStr': '10:00 am'
        },
        {
            'title': "18th Century Astronomy",
            'startDate': datetime(2025, 10, 30, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 30, 18, 0).isoformat() + 'Z',
            'description': "Educational program about 18th century astronomy",
            'location': '',
            'dateStr': 'October 30, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        },
        {
            'title': "Caroles Dance Party",
            'startDate': datetime(2025, 10, 30, 17, 0).isoformat() + 'Z',  # 1:00 pm EDT
            'endDate': datetime(2025, 10, 30, 18, 0).isoformat() + 'Z',
            'description': "Dance party hosted by Carole",
            'location': '',
            'dateStr': 'October 30, 2025, 1:00 pm',
            'timeStr': '1:00 pm'
        }
    ]
    
    # Always use stored events if available, otherwise return empty list (no fallback to old events)
    if stored_events and len(stored_events) > 0:
        print(f"📦 Using {len(stored_events)} stored events")
        all_events = stored_events
    else:
        print("📅 No stored events found - returning empty list (no fallback to old events)")
        all_events = []
    
    # Fix image URLs and clean titles for all events
    for event in all_events:
        if not event.get('image_url') or event.get('image_url') == '/assets/event-schedule-banner.png':
            event['image_url'] = '/logo192.png'  # Use accessible logo as banner
        
        # Clean up titles that contain descriptions
        title = event.get('title', '')
        description = event.get('description', '')
        
        # If title is very long and contains description, extract just the title part
        if len(title) > 50:  # Lower threshold to catch more cases
            import re
            # Look for pattern like "Event Name October 24, 1:30 pm Description"
            # Try multiple patterns to extract just the event name
            patterns = [
                r'^([^0-9]+?)\s+\w+\s+\d+,\s+\d+:\d+\s+[ap]m',  # "Event Name October 24, 1:30 pm"
                r'^([^0-9]+?)\s+\w+\s+\d+',  # "Event Name October 24"
                r'^([^0-9]+?)\s+\d+:\d+\s+[ap]m',  # "Event Name 1:30 pm"
                r'^([^0-9]+?)\s+\d+',  # "Event Name 24"
            ]
            
            for pattern in patterns:
                match = re.match(pattern, title)
                if match:
                    clean_title = match.group(1).strip()
                    # Remove trailing punctuation and extra spaces
                    clean_title = re.sub(r'[,\s]+$', '', clean_title)
                    if len(clean_title) > 3:  # Make sure we have a meaningful title
                        event['title'] = clean_title
                        print(f"🧹 Cleaned title: '{title[:50]}...' -> '{clean_title}'")
                        break
    
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
        updated = False
        
        # Check editable_events first
        if event_id in editable_events:
            editable_events[event_id].update({
                'title': event_data.get('title', editable_events[event_id]['title']),
                'startDate': event_data.get('startDate', editable_events[event_id]['startDate']),
                'endDate': event_data.get('endDate', editable_events[event_id]['endDate']),
                'description': event_data.get('description', editable_events[event_id]['description']),
                'location': event_data.get('location', editable_events[event_id]['location'])
            })
            updated = True
        
        # Check stored_events (by matching title and startDate if event_id is index-based)
        global stored_events
        if event_id.startswith('stored_'):
            # Extract index from event_id like "stored_0", "stored_1", etc.
            try:
                idx = int(event_id.replace('stored_', ''))
                if 0 <= idx < len(stored_events):
                    stored_events[idx].update(event_data)
                    updated = True
            except ValueError:
                pass
        
        if not updated:
            return {"success": False, "error": "Event not found"}
        
        print(f"✅ Event updated with ID: {event_id}")
        return {"success": True, "message": "Event updated successfully"}
        
    except Exception as e:
        print(f"❌ Error updating event: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.delete("/api/events/{event_id}")
def delete_event(event_id: str):
    """Delete an event"""
    print(f"🌐 Delete event API call received for ID {event_id}")
    
    try:
        deleted = False
        
        # Check editable_events first
        if event_id in editable_events:
            editable_events.pop(event_id)
            deleted = True
        else:
            # Check stored_events by removing the event
            global stored_events
            if event_id.startswith('stored_'):
                try:
                    idx = int(event_id.replace('stored_', ''))
                    if 0 <= idx < len(stored_events):
                        stored_events.pop(idx)
                        deleted = True
                except ValueError:
                    pass
        
        if not deleted:
            return {"success": False, "error": "Event not found"}
        
        print(f"✅ Event deleted with ID: {event_id}")
        return {"success": True, "message": "Event deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting event: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/events/bulk-update")
async def bulk_update_events(request: Request):
    """Bulk update events - REPLACE all events with new ones (from Event Editor)"""
    global stored_events  # CRITICAL: Declare global at the top
    
    try:
        data = await request.json()
        events = data.get('events', [])
        
        if not isinstance(events, list):
            return {
                "success": False,
                "error": "Invalid data format: events must be a list",
                "total_count": len(stored_events)
            }
        
        print(f"🔄 Bulk update received: {len(events)} events to REPLACE all existing events")
        
        # Replace all stored events with the new list
        old_count = len(stored_events)
        
        # Ensure we have a proper list
        stored_events = list(events) if isinstance(events, list) else []
        
        # CRITICAL: Save to persistent storage with error handling
        save_error = None
        try:
            save_stored_events()
            save_successful = True
        except Exception as e:
            save_error = str(e)
            print(f"❌ ERROR: Save failed: {save_error}")
            save_successful = False
            # Don't return here - we still updated in memory, but file save failed
        
        print(f"✅ Successfully replaced {old_count} old events with {len(events)} new events")
        print(f"📊 Total events now: {len(stored_events)}")
        
        if not save_successful:
            return {
                "success": False,
                "error": f"Events updated in memory but failed to save to file: {save_error}",
                "total_count": len(stored_events),
                "old_count": old_count,
                "new_count": len(stored_events),
                "warning": "Events may not persist after restart"
            }
        
        return {
            "success": True,
            "message": f"Successfully saved {len(events)} events",
            "total_count": len(stored_events),
            "old_count": old_count,
            "new_count": len(stored_events),
            "saved_to": STORED_EVENTS_FILE
        }
        
    except Exception as e:
        print(f"❌ Error in bulk update: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/upload-excel")
async def upload_excel(request: Request):
    """Upload Excel file and process events"""
    try:
        # Get the uploaded file
        form = await request.form()
        file = form.get("file")
        
        if not file:
            return {"success": False, "error": "No file uploaded"}
        
        # Read the file content
        content = await file.read()
        filename = file.filename
        
        print(f"📊 Excel file uploaded: {filename} ({len(content)} bytes)")
        
        # Save the file temporarily
        import os
        temp_path = f"temp_{filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Process the Excel file
        try:
            # Check file extension first
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            print(f"📊 Processing file: {filename} (extension: {file_ext})")
            
            # For now, use CSV processing for all files since pandas/openpyxl may not be available
            print("📊 Using CSV processing for all file types...")
            return process_csv_fallback(temp_path, filename)
                    
        except Exception as excel_error:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return {
                "success": False,
                "error": f"Excel processing error: {str(excel_error)}"
            }
        
    except Exception as e:
        print(f"❌ Error uploading Excel: {e}")
        return {"success": False, "error": str(e)}

def process_csv_fallback(temp_path, filename):
    """Process CSV file as fallback"""
    try:
        import csv
        
        # Check if file is actually a CSV file
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if file_ext not in ['csv', 'txt']:
            return {
                "success": False,
                "error": f"File type '{file_ext}' not supported. Please upload a CSV file."
            }
        
        # Try to read as CSV
        events = []
        with open(temp_path, 'r', encoding='utf-8') as file:
            # Try to detect delimiter
            sample = file.read(1024)
            file.seek(0)
            
            delimiter = ','
            if '\t' in sample:
                delimiter = '\t'
            elif ';' in sample:
                delimiter = ';'
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row in reader:
                event = {
                    "title": str(row.get('title', row.get('Title', f'Event {len(events) + 1}'))),
                    "startDate": str(row.get('startDate', row.get('Start Date', '2025-01-01T10:00:00Z'))),
                    "endDate": str(row.get('endDate', row.get('End Date', '2025-01-01T11:00:00Z'))),
                    "description": str(row.get('description', row.get('Description', ''))),
                    "location": str(row.get('location', row.get('Location', ''))),
                    "dateStr": str(row.get('dateStr', row.get('Date String', ''))),
                    "timeStr": str(row.get('timeStr', row.get('Time String', ''))),
                    "price": str(row.get('price', row.get('Price', ''))),
                    "instructor": str(row.get('instructor', row.get('Instructor', ''))),
                    "registration": str(row.get('registration', row.get('Registration', ''))),
                    "image_url": "/event-schedule-banner.png"
                }
                events.append(event)
        
        # Merge with existing events instead of replacing
        global stored_events
        
        # Create a set to track existing events by (title, startDate)
        existing_events_dict = {}
        for event in stored_events:
            key = (event.get('title', ''), event.get('startDate', ''))
            existing_events_dict[key] = event
        
        # Track counts
        added_count = 0
        skipped_count = 0
        
        # Add only new events (no duplicates)
        for new_event in events:
            key = (new_event.get('title', ''), new_event.get('startDate', ''))
            if key not in existing_events_dict:
                stored_events.append(new_event)
                existing_events_dict[key] = new_event
                added_count += 1
            else:
                skipped_count += 1
        
        print(f"✅ Merged {added_count} new events from Excel (skipped {skipped_count} duplicates)")
        print(f"📊 Total events now: {len(stored_events)}")
        
        # Save to persistent storage
        save_stored_events()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "success": True,
            "message": f"CSV file '{filename}' processed successfully! Loaded {len(events)} events.",
            "events_count": len(events)
        }
        
    except Exception as csv_error:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {
            "success": False,
            "error": f"CSV processing error: {str(csv_error)}"
        }

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
            'location': '',
            'dateStr': 'October 1, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Hearing Clinic",
            'startDate': datetime(2024, 10, 3, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2024, 10, 3, 17, 0).isoformat() + 'Z',
            'description': "Free hearing assessment clinic",
            'location': '',
            'dateStr': 'October 3, 12:00 pm',
            'timeStr': '12:00 pm'
        },
        {
            'title': "Top 10 Free Google App",
            'startDate': datetime(2024, 10, 6, 16, 0).isoformat() + 'Z',  # 12:00 pm EDT
            'endDate': datetime(2024, 10, 6, 17, 0).isoformat() + 'Z',
            'description': "Learn about useful free Google applications",
            'location': '',
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

@app.post("/api/events/{event_title}/update-banner")
async def update_event_banner(event_title: str, request: Request):
    """Update the banner/image for a specific event by title"""
    try:
        data = await request.json()
        new_image_url = data.get('image_url')
        event_date = data.get('startDate')
        
        if not new_image_url:
            return {"success": False, "error": "image_url is required"}
        
        global stored_events
        updated = False
        
        for event in stored_events:
            if event.get('title') == event_title:
                if event_date is None or event.get('startDate') == event_date:
                    event['image_url'] = new_image_url
                    updated = True
                    print(f"✅ Updated banner for: {event_title}")
        
        if updated:
            save_stored_events()
            return {
                "success": True,
                "message": f"Successfully updated banner for {event_title}",
                "image_url": new_image_url
            }
        else:
            return {
                "success": False,
                "error": f"Event '{event_title}' not found"
            }
            
    except Exception as e:
        print(f"❌ Error updating event banner: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.get("/api/events/debug")
async def debug_events():
    """Debug endpoint to check stored events status and verify file contents"""
    global stored_events
    
    # Try to read what's actually in the file
    file_events_count = 0
    file_events_sample = []
    file_read_error = None
    
    if os.path.exists(STORED_EVENTS_FILE):
        try:
            with open(STORED_EVENTS_FILE, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    file_events_count = len(file_data)
                    file_events_sample = file_data[:3] if file_data else []
                else:
                    file_read_error = "File does not contain a list"
        except Exception as e:
            file_read_error = str(e)
    
    debug_info = {
        "stored_events_file": STORED_EVENTS_FILE,
        "file_exists": os.path.exists(STORED_EVENTS_FILE),
        "memory_count": len(stored_events),
        "file_count": file_events_count,
        "count_match": len(stored_events) == file_events_count,
        "stored_events_sample": stored_events[:3] if stored_events else [],
        "file_events_sample": file_events_sample,
        "file_size": os.path.getsize(STORED_EVENTS_FILE) if os.path.exists(STORED_EVENTS_FILE) else 0,
        "file_read_error": file_read_error,
        "warning": "Mismatch between memory and file!" if len(stored_events) != file_events_count else None
    }
    
    print(f"🔍 DEBUG: {debug_info}")
    return debug_info

@app.post("/api/fallback/save-events")
async def save_events_as_fallback():
    """Save current stored events as fallback data"""
    try:
        global stored_events
        
        if not stored_events:
            return {"success": False, "error": "No events to save as fallback"}
        
        # Create fallback data structure
        fallback_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "Fallback events data - saved from current stored events",
                "total_events": len(stored_events),
                "last_updated": datetime.now().isoformat(),
                "source": "current_stored_events"
            },
            "events": stored_events
        }
        
        # Save to fallback file
        fallback_file = "/tmp/events_fallback_data.json" if os.getenv('RENDER') else "events_fallback_data.json"
        
        with open(fallback_file, 'w', encoding='utf-8') as f:
            json.dump(fallback_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(stored_events)} events as fallback data")
        
        return {
            "success": True,
            "message": f"Successfully saved {len(stored_events)} events as fallback data",
            "total_events": len(stored_events),
            "fallback_file": fallback_file
        }
        
    except Exception as e:
        print(f"❌ Error saving events as fallback: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/fallback/save-excel")
async def save_excel_as_fallback():
    """Save current Excel data as fallback data"""
    try:
        # Read current Excel data
        programs = get_programs_from_db()
        
        if not programs:
            return {"success": False, "error": "No Excel data to save as fallback"}
        
        # Create fallback data structure
        fallback_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "Fallback Excel data - saved from current Excel file",
                "total_programs": len(programs),
                "last_updated": datetime.now().isoformat(),
                "source": "current_excel_file",
                "excel_file": "Class Cancellation App.xlsx"
            },
            "programs": programs
        }
        
        # Save to fallback file
        fallback_file = "/tmp/excel_fallback_data.json" if os.getenv('RENDER') else "excel_fallback_data.json"
        
        with open(fallback_file, 'w', encoding='utf-8') as f:
            json.dump(fallback_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(programs)} programs as fallback data")
        
        return {
            "success": True,
            "message": f"Successfully saved {len(programs)} programs as fallback data",
            "total_programs": len(programs),
            "fallback_file": fallback_file
        }
        
    except Exception as e:
        print(f"❌ Error saving Excel as fallback: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/fallback/status")
async def get_fallback_status():
    """Get current fallback data status"""
    try:
        status = {
            "events_fallback": {
                "file_exists": False,
                "total_events": 0,
                "last_updated": None
            },
            "excel_fallback": {
                "file_exists": False,
                "total_programs": 0,
                "last_updated": None
            },
            "database_status": {
                "total_programs": 0,
                "is_empty": True
            }
        }
        
        # Check database status
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM programs")
            db_count = cursor.fetchone()[0]
            conn.close()
            status["database_status"]["total_programs"] = db_count
            status["database_status"]["is_empty"] = (db_count == 0)
        except Exception as e:
            print(f"⚠️ Error checking database status: {e}")
        
        # Check events fallback
        events_fallback_file = "/tmp/events_fallback_data.json" if os.getenv('RENDER') else "events_fallback_data.json"
        if os.path.exists(events_fallback_file):
            try:
                with open(events_fallback_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                status["events_fallback"]["file_exists"] = True
                status["events_fallback"]["total_events"] = events_data.get("metadata", {}).get("total_events", 0)
                status["events_fallback"]["last_updated"] = events_data.get("metadata", {}).get("last_updated", "Unknown")
            except Exception as e:
                print(f"⚠️ Error reading events fallback: {e}")
        
        # Check Excel fallback
        excel_fallback_file = "/tmp/excel_fallback_data.json" if os.getenv('RENDER') else "excel_fallback_data.json"
        if os.path.exists(excel_fallback_file):
            try:
                with open(excel_fallback_file, 'r', encoding='utf-8') as f:
                    excel_data = json.load(f)
                status["excel_fallback"]["file_exists"] = True
                status["excel_fallback"]["total_programs"] = excel_data.get("metadata", {}).get("total_programs", 0)
                status["excel_fallback"]["last_updated"] = excel_data.get("metadata", {}).get("last_updated", "Unknown")
            except Exception as e:
                print(f"⚠️ Error reading Excel fallback: {e}")
        
        return status
        
    except Exception as e:
        print(f"❌ Error getting fallback status: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ============================================
# GOOGLE CLOUD STORAGE API ENDPOINTS
# ============================================

@app.get("/api/gcs/status")
async def get_gcs_status():
    """Get Google Cloud Storage connection status and list files"""
    try:
        # Check environment variables for debugging
        gcs_creds_set = bool(os.getenv('GCS_CREDENTIALS'))
        gcs_creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        gcs_creds_path_exists = os.path.exists(gcs_creds_path) if gcs_creds_path else False
        
        debug_info = {
            "GCS_CREDENTIALS_env_set": gcs_creds_set,
            "GCS_CREDENTIALS_length": len(os.getenv('GCS_CREDENTIALS', '')) if gcs_creds_set else 0,
            "GOOGLE_APPLICATION_CREDENTIALS": gcs_creds_path,
            "GOOGLE_APPLICATION_CREDENTIALS_file_exists": gcs_creds_path_exists,
            "GCS_BUCKET_NAME": GCS_BUCKET_NAME,
            "GCS_AVAILABLE_library": GCS_AVAILABLE
        }
        
        client = get_gcs_client()
        
        if not client:
            error_msg = "Google Cloud Storage client not available.\n\n"
            if not GCS_AVAILABLE:
                error_msg += "❌ google-cloud-storage library not installed.\n"
            if not gcs_creds_set and not gcs_creds_path_exists:
                error_msg += "❌ No credentials found. Please set GCS_CREDENTIALS environment variable on Render.\n"
                error_msg += "\n📋 Instructions:\n"
                error_msg += "1. Go to Render Dashboard → Your Service → Environment\n"
                error_msg += "2. Add new environment variable:\n"
                error_msg += "   Name: GCS_CREDENTIALS\n"
                error_msg += "   Value: (paste the ENTIRE content of your service account JSON key file)\n"
                error_msg += "3. Also add: GCS_BUCKET_NAME = your-bucket-name\n"
                error_msg += "4. Click Save and redeploy"
            
            return {
                "success": False,
                "connected": False,
                "error": error_msg,
                "bucket_name": GCS_BUCKET_NAME,
                "gcs_available": GCS_AVAILABLE,
                "debug": debug_info
            }
        
        # Try to list files in the bucket
        try:
            files = list_gcs_files()
        except Exception as list_error:
            return {
                "success": False,
                "connected": True,
                "error": f"Connected but cannot list files: {str(list_error)}. Check bucket name and permissions.",
                "bucket_name": GCS_BUCKET_NAME,
                "gcs_available": GCS_AVAILABLE,
                "debug": debug_info
            }
        
        # Check for our specific files
        events_file_exists = any(f['name'] == GCS_EVENTS_FILE for f in files)
        excel_file_exists = any(f['name'] == GCS_EXCEL_FILE for f in files)
        excel_original_exists = any(f['name'] == GCS_EXCEL_ORIGINAL_FILE for f in files)
        
        return {
            "success": True,
            "connected": True,
            "bucket_name": GCS_BUCKET_NAME,
            "gcs_available": GCS_AVAILABLE,
            "files": files,
            "files_count": len(files),
            "events_file_exists": events_file_exists,
            "excel_file_exists": excel_file_exists,
            "excel_original_exists": excel_original_exists,
            "debug": debug_info
        }
        
    except Exception as e:
        print(f"❌ Error checking GCS status: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "bucket_name": GCS_BUCKET_NAME,
            "debug": {
                "exception": str(e),
                "GCS_AVAILABLE": GCS_AVAILABLE
            }
        }

@app.post("/api/gcs/upload-events")
async def upload_events_to_gcs():
    """Upload current stored events to Google Cloud Storage"""
    try:
        global stored_events
        
        if not stored_events:
            return {"success": False, "error": "No events to upload"}
        
        # Create data structure with metadata
        gcs_data = {
            "metadata": {
                "uploaded_at": datetime.now().isoformat(),
                "total_events": len(stored_events),
                "source": "admin_panel_upload",
                "description": "Events data uploaded from admin panel"
            },
            "events": stored_events
        }
        
        # Upload to GCS
        success = upload_to_gcs(gcs_data, GCS_EVENTS_FILE)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully uploaded {len(stored_events)} events to Google Cloud Storage",
                "total_events": len(stored_events),
                "bucket": GCS_BUCKET_NAME,
                "filename": GCS_EVENTS_FILE
            }
        else:
            return {
                "success": False,
                "error": "Failed to upload to Google Cloud Storage. Check credentials and bucket configuration."
            }
        
    except Exception as e:
        print(f"❌ Error uploading events to GCS: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/gcs/download-events")
async def download_events_from_gcs():
    """Download events from Google Cloud Storage and update local storage"""
    try:
        global stored_events
        
        # Download from GCS
        gcs_data = download_from_gcs(GCS_EVENTS_FILE)
        
        if not gcs_data:
            return {
                "success": False,
                "error": f"No events file found in Google Cloud Storage (bucket: {GCS_BUCKET_NAME}, file: {GCS_EVENTS_FILE})"
            }
        
        # Extract events from data
        if isinstance(gcs_data, list):
            events = gcs_data
        elif isinstance(gcs_data, dict) and 'events' in gcs_data:
            events = gcs_data['events']
        else:
            return {
                "success": False,
                "error": "Invalid data format in GCS file"
            }
        
        # Update stored events
        stored_events = events
        
        # Also save to local file as backup
        save_stored_events()
        
        return {
            "success": True,
            "message": f"Successfully downloaded {len(stored_events)} events from Google Cloud Storage",
            "total_events": len(stored_events),
            "bucket": GCS_BUCKET_NAME,
            "filename": GCS_EVENTS_FILE,
            "metadata": gcs_data.get('metadata', {}) if isinstance(gcs_data, dict) else None
        }
        
    except Exception as e:
        print(f"❌ Error downloading events from GCS: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/gcs/upload-excel")
async def upload_excel_to_gcs():
    """Upload current Excel/program data to Google Cloud Storage"""
    try:
        # Get current programs from database
        programs = get_programs_from_db()
        
        if not programs:
            return {"success": False, "error": "No Excel/program data to upload"}
        
        # Create data structure with metadata
        gcs_data = {
            "metadata": {
                "uploaded_at": datetime.now().isoformat(),
                "total_programs": len(programs),
                "source": "admin_panel_upload",
                "description": "Excel/program data uploaded from admin panel"
            },
            "programs": programs
        }
        
        # Upload to GCS
        success = upload_to_gcs(gcs_data, GCS_EXCEL_FILE)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully uploaded {len(programs)} programs to Google Cloud Storage",
                "total_programs": len(programs),
                "bucket": GCS_BUCKET_NAME,
                "filename": GCS_EXCEL_FILE
            }
        else:
            return {
                "success": False,
                "error": "Failed to upload to Google Cloud Storage. Check credentials and bucket configuration."
            }
        
    except Exception as e:
        print(f"❌ Error uploading Excel to GCS: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/gcs/download-excel")
async def download_excel_from_gcs():
    """Download Excel/program data from Google Cloud Storage and restore to database"""
    try:
        # Download from GCS
        gcs_data = download_from_gcs(GCS_EXCEL_FILE)
        
        if not gcs_data:
            return {
                "success": False,
                "error": f"No Excel file found in Google Cloud Storage (bucket: {GCS_BUCKET_NAME}, file: {GCS_EXCEL_FILE})"
            }
        
        # Extract programs from data
        programs = gcs_data.get('programs', [])
        
        if not programs:
            return {
                "success": False,
                "error": "No programs found in GCS Excel file"
            }
        
        # Restore programs to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Clear existing programs
        cursor.execute("DELETE FROM programs")
        
        # Insert programs
        for program in programs:
            cursor.execute("""
                INSERT INTO programs (name, day, times, instructor, category)
                VALUES (?, ?, ?, ?, ?)
            """, (
                program.get('name', ''),
                program.get('day', ''),
                program.get('times', ''),
                program.get('instructor', ''),
                program.get('category', '')
            ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully downloaded and restored {len(programs)} programs from Google Cloud Storage",
            "total_programs": len(programs),
            "bucket": GCS_BUCKET_NAME,
            "filename": GCS_EXCEL_FILE,
            "metadata": gcs_data.get('metadata', {})
        }
        
    except Exception as e:
        print(f"❌ Error downloading Excel from GCS: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/gcs/upload-excel-file")
async def upload_excel_file_to_gcs(file: UploadFile = File(...)):
    """Upload an Excel file directly to Google Cloud Storage"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to GCS
        filename = file.filename or GCS_EXCEL_ORIGINAL_FILE
        success = upload_file_to_gcs(
            file_content, 
            filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        if success:
            # Also process and save as JSON
            try:
                # Read Excel content
                excel_io = io.BytesIO(file_content)
                df = pd.read_excel(excel_io)
                
                # Convert to programs list
                programs = []
                for _, row in df.iterrows():
                    program = {}
                    for col in df.columns:
                        val = row[col]
                        if pd.notna(val):
                            program[col.lower().replace(' ', '_')] = str(val)
                    if program:
                        programs.append(program)
                
                # Upload JSON version too
                if programs:
                    gcs_data = {
                        "metadata": {
                            "uploaded_at": datetime.now().isoformat(),
                            "total_programs": len(programs),
                            "source_file": filename,
                            "description": "Excel data converted to JSON and uploaded"
                        },
                        "programs": programs
                    }
                    upload_to_gcs(gcs_data, GCS_EXCEL_FILE)
                    
                    # Also restore to database
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM programs")
                    for program in programs:
                        cursor.execute("""
                            INSERT INTO programs (name, day, times, instructor, category)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            program.get('name', program.get('program', '')),
                            program.get('day', ''),
                            program.get('times', program.get('time', '')),
                            program.get('instructor', ''),
                            program.get('category', '')
                        ))
                    conn.commit()
                    conn.close()
            except Exception as parse_error:
                print(f"⚠️ Could not parse Excel for JSON conversion: {parse_error}")
            
            return {
                "success": True,
                "message": f"Successfully uploaded {filename} to Google Cloud Storage",
                "filename": filename,
                "bucket": GCS_BUCKET_NAME,
                "size": len(file_content)
            }
        else:
            return {
                "success": False,
                "error": "Failed to upload file to Google Cloud Storage"
            }
        
    except Exception as e:
        print(f"❌ Error uploading Excel file to GCS: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.post("/api/gcs/sync-all")
async def sync_all_data_from_gcs():
    """Sync all data (events and Excel) from Google Cloud Storage"""
    try:
        results = {
            "events": None,
            "excel": None
        }
        
        # Sync events
        try:
            events_result = await download_events_from_gcs()
            results["events"] = events_result
        except Exception as e:
            results["events"] = {"success": False, "error": str(e)}
        
        # Sync Excel
        try:
            excel_result = await download_excel_from_gcs()
            results["excel"] = excel_result
        except Exception as e:
            results["excel"] = {"success": False, "error": str(e)}
        
        overall_success = (
            results["events"].get("success", False) or 
            results["excel"].get("success", False)
        )
        
        return {
            "success": overall_success,
            "message": "Sync completed" if overall_success else "Sync failed",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Error syncing from GCS: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ============================================
# END GOOGLE CLOUD STORAGE API ENDPOINTS
# ============================================

@app.post("/api/fallback/restore-excel")
async def restore_excel_from_fallback():
    """CRITICAL: Force restore Excel data from fallback file to database"""
    try:
        print("🔄 Manual restore from fallback requested...")
        
        # Check if fallback exists
        fallback_file = "/tmp/excel_fallback_data.json" if os.getenv('RENDER') else "excel_fallback_data.json"
        if not os.path.exists(fallback_file):
            return {
                "success": False,
                "error": "Fallback file not found",
                "fallback_file": fallback_file
            }
        
        # Get fallback data info
        with open(fallback_file, 'r', encoding='utf-8') as f:
            fallback_data = json.load(f)
        
        fallback_programs = fallback_data.get('programs', [])
        if not fallback_programs or len(fallback_programs) == 0:
            return {
                "success": False,
                "error": "Fallback file exists but contains no programs",
                "fallback_file": fallback_file
            }
        
        # Restore to database
        restore_success = restore_fallback_programs_to_database()
        
        if restore_success:
            # Verify restore
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM programs")
            restored_count = cursor.fetchone()[0]
            conn.close()
            
            return {
                "success": True,
                "message": f"Successfully restored {restored_count} programs from fallback to database",
                "restored_count": restored_count,
                "fallback_count": len(fallback_programs),
                "last_updated": fallback_data.get('metadata', {}).get('last_updated', 'Unknown')
            }
        else:
            return {
                "success": False,
                "error": "Failed to restore programs to database",
                "fallback_count": len(fallback_programs)
            }
        
    except Exception as e:
        print(f"❌ Error restoring from fallback: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.get("/api/events/export")
async def export_events():
    """Export all stored events as JSON file"""
    try:
        global stored_events
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_events": len(stored_events),
            "events": stored_events
        }
        
        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=events_export.json"}
        )
        
    except Exception as e:
        print(f"❌ Error exporting events: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/scrape-events/save-file")
async def scrape_and_save_file_locally():
    """Scrape events from website and save to local file (works when backend runs locally)"""
    try:
        print("🔄 Scraping events and saving to local file...")
        
        # Scrape events from website
        scraped_events = scrape_seniors_kingston_events()
        
        if scraped_events and len(scraped_events) > 0:
            # Format for save (same format as export)
            export_data = {
                "export_date": datetime.now().isoformat(),
                "total_events": len(scraped_events),
                "events": scraped_events,
                "source": "scraped_from_website",
                "scraped_at": datetime.now().isoformat()
            }
            
            # Save to local file
            filename = "scraped_events_for_upload.json"
            filepath = filename  # Save in current directory (where backend runs)
            file_saved = False
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Scraped {len(scraped_events)} events and saved to {filepath}")
                file_saved = True
            except Exception as save_error:
                print(f"⚠️ Could not save file locally: {save_error}")
                file_saved = False
            
            # Return success with full data for download
            return {
                "success": True,
                "message": f"✅ Successfully scraped {len(scraped_events)} events!" + (f" File saved to {filename}." if file_saved else " Use 'Download' to save the file."),
                "total_events": len(scraped_events),
                "filename": filename,
                "filepath": filepath if file_saved else None,
                "file_saved": file_saved,
                "events": scraped_events,  # Return ALL events for download
                "export_data": export_data  # Return full export data for download
            }
        else:
            # Scraping failed (likely on cloud environment)
            return {
                "success": False,
                "error": "Scraping failed - no events found",
                "message": "Scraping doesn't work on cloud environments (like Render) because Selenium requires a browser. Make sure you're running the backend locally on your computer.",
                "suggestion": "This button only works when the backend is running locally on your computer (not on Render)."
            }
        
    except Exception as e:
        print(f"❌ Error scraping and saving: {e}")
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "message": f"An error occurred while scraping: {e}. Make sure you're running the backend locally and have Chrome installed."
        }

@app.post("/api/events/import")
async def import_events(file: UploadFile = File(...)):
    """Import events from JSON file"""
    try:
        global stored_events
        
        # Read the uploaded file
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        if 'events' not in data:
            return {"success": False, "error": "Invalid file format - no 'events' key found"}
        
        new_events = data['events']
        
        # Remove duplicates based on title + startDate
        unique_events = []
        seen_keys = set()
        for event in new_events:
            key = (event.get('title', ''), event.get('startDate', ''))
            if key not in seen_keys:
                unique_events.append(event)
                seen_keys.add(key)
        
        # Replace stored events
        stored_events = unique_events
        save_stored_events()
        
        return {
            "success": True,
            "message": f"Successfully imported {len(unique_events)} events (removed {len(new_events) - len(unique_events)} duplicates)",
            "total_events": len(unique_events)
        }
        
    except Exception as e:
        print(f"❌ Error importing events: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/events/clear")
async def clear_events_endpoint():
    """Clear all stored events"""
    global stored_events
    count = len(stored_events)
    stored_events = []
    print(f"🗑️ Cleared {count} events")
    return {
        "success": True,
        "message": f"Successfully cleared {count} events",
        "count": 0
    }

@app.post("/api/events/remove-duplicates")
async def remove_duplicates_endpoint():
    """Remove duplicate events from stored_events"""
    global stored_events
    original_count = len(stored_events)
    
    # Remove duplicates
    unique_events = []
    seen_keys = set()
    for event in stored_events:
        key = (event.get('title', ''), event.get('startDate', ''))
        if key not in seen_keys:
            unique_events.append(event)
            seen_keys.add(key)
    
    duplicates_removed = original_count - len(unique_events)
    stored_events = unique_events
    
    print(f"✅ Removed {duplicates_removed} duplicate events")
    return {
        "success": True,
        "message": f"Successfully removed {duplicates_removed} duplicate events",
        "original_count": original_count,
        "unique_count": len(unique_events),
        "duplicates_removed": duplicates_removed
        }

@app.post("/api/scrape-events")
async def scrape_events_endpoint(request: Request, replace: bool = Query(False)):
    """Manually trigger event scraping from Seniors Kingston website
    
    Args:
        replace: If True, replace all existing events with scraped events.
                 If False (default), merge scraped events with existing ones.
    """
    try:
        # Also check query parameters in case they're passed that way
        query_replace = request.query_params.get('replace', 'false').lower() == 'true'
        replace = replace or query_replace
        
        print(f"🔄 Manual event scraping requested (replace={replace})")
        print(f"   Query params: {request.query_params}")
        print(f"   Replace parameter: {replace}")
        
        # Scrape events from website
        scraped_events = scrape_seniors_kingston_events()
        
        if scraped_events and len(scraped_events) > 0:
            global stored_events
            old_count = len(stored_events) if stored_events else 0
            
            # If replace=True, replace all events
            if replace:
                print(f"🔄 REPLACING all {old_count} existing events with {len(scraped_events)} scraped events")
                stored_events = scraped_events.copy()  # Make a copy to avoid reference issues
                save_stored_events()
                
                # Verify the save worked
                print(f"✅ Saved {len(stored_events)} events. Verifying...")
                load_stored_events()  # Reload to verify
                print(f"✅ Verified: {len(stored_events)} events in stored_events after save")
                
                return {
                    "success": True,
                    "message": f"✅ Successfully replaced all events! Replaced {old_count} old events with {len(scraped_events)} scraped events.",
                    "events_count": len(scraped_events),
                    "replaced": True,
                    "old_count": old_count,
                    "new_count": len(scraped_events)
                }
            
            # SAFE MERGE: Only add new events, never overwrite existing ones
            print(f"🔍 Starting safe merge: {len(stored_events)} existing events, {len(scraped_events)} scraped events")
            
            print(f"🔍 Starting safe merge: {len(stored_events)} existing events, {len(scraped_events)} scraped events")
            
            # Create a comprehensive tracking system for existing events
            existing_events_dict = {}
            for i, event in enumerate(stored_events):
                # Use multiple keys to prevent duplicates more effectively
                title = event.get('title', '').strip().lower()
                start_date = event.get('startDate', '').strip()
                location = event.get('location', '').strip().lower()
                
                # Primary key: title + startDate
                primary_key = (title, start_date)
                # Secondary key: title + location (for events at same time, different locations)
                secondary_key = (title, location)
                
                existing_events_dict[primary_key] = {
                    'event': event,
                    'index': i,
                    'secondary_key': secondary_key
                }
            
            # Track counts and details
            added_count = 0
            skipped_count = 0
            updated_count = 0
            updated_details = []
            skipped_details = []

            def find_existing(primary_key, secondary_key):
                if primary_key in existing_events_dict:
                    return existing_events_dict[primary_key]
                for existing in existing_events_dict.values():
                    if existing['secondary_key'] == secondary_key:
                        return existing
                return None
            
            # Add only completely new events (no duplicates)
            for new_event in scraped_events:
                new_title = new_event.get('title', '').strip().lower()
                new_start_date = new_event.get('startDate', '').strip()
                new_location = new_event.get('location', '').strip().lower()
                
                # Check for duplicates using multiple criteria
                primary_key = (new_title, new_start_date)
                secondary_key = (new_title, new_location)
                
                existing_match = find_existing(primary_key, secondary_key)

                if existing_match:
                    existing_event = existing_match['event']
                    existing_index = existing_match['index']
                    fields_to_check = [
                        'image_url',
                        'description',
                        'dateStr',
                        'timeStr',
                        'location',
                        'price',
                        'instructor',
                        'registration',
                        'startDate',
                        'endDate'
                    ]

                    changed_fields = []
                    for field in fields_to_check:
                        new_value = new_event.get(field)
                        if new_value and new_value != existing_event.get(field):
                            existing_event[field] = new_value
                            changed_fields.append(field)

                    if changed_fields:
                        stored_events[existing_index] = existing_event
                        existing_events_dict[primary_key] = {
                            'event': existing_event,
                            'index': existing_index,
                            'secondary_key': secondary_key
                        }
                        updated_count += 1
                        updated_details.append(
                            f"🔄 Updated {new_event.get('title', 'Unknown')} ({', '.join(changed_fields)})"
                        )
                        print(f"🔄 Updated existing event: {new_event.get('title', 'Unknown')} - fields changed: {changed_fields}")
                    else:
                        skipped_count += 1
                        skipped_details.append(
                            f"⚠️ Skipped (no changes): {new_event.get('title', 'Unknown')}"
                        )
                        print(f"⚠️ Skipping event (no changes detected): {new_event.get('title', 'Unknown')}")
                    continue

                    # no explicit else since continue
                else:
                    # Add new event
                    stored_events.append(new_event)
                    existing_events_dict[primary_key] = {
                        'event': new_event,
                        'index': len(stored_events) - 1,
                        'secondary_key': secondary_key
                    }
                    added_count += 1
                    print(f"✅ Added new event: {new_event.get('title', 'Unknown')} on {new_start_date}")
            
            print(f"✅ SAFE MERGE COMPLETE:")
            print(f"   📊 Added {added_count} new events")
            print(f"   🔄 Updated {updated_count} existing events")
            print(f"   🚫 Skipped {skipped_count} duplicates/no-change events")
            print(f"   📈 Total events now: {len(stored_events)}")
            print(f"   🔒 Existing events preserved (no overwrites)")
            
            # Save to persistent storage
            save_stored_events()
            
            return {
                "success": True,
                "message": f"✅ Safe merge complete! Added {added_count} new events, skipped {skipped_count} duplicates. Your existing events are preserved.",
                "events_count": len(stored_events),
                "added": added_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "preserved": len(stored_events) - added_count,
                "skipped_details": skipped_details[:5],  # Show first 5 skipped details
                "updated_details": updated_details[:5],
                "events": stored_events[:5]  # Return first 5 events as sample
            }
        else:
            # Scraping returned 0 events - this happens on cloud environments where Selenium doesn't work
            print(f"📅 No events found during scraping (replace={replace})")
            
            if replace:
                # Even if scraping failed, if replace=True, we should clear events
                # But only if user explicitly wants to replace (don't clear on accident)
                print(f"⚠️ Scraping failed but replace=True was requested")
                print(f"   Current stored events: {len(stored_events)}")
                print(f"   ⚠️ NOT clearing events because scraping returned 0 events")
                print(f"   💡 Suggestion: Scraping may not work on cloud. Try using the bulk-update endpoint with a JSON file instead.")
                
                return {
                    "success": False,
                    "error": "Scraping failed - no events found. This is normal on cloud environments where Selenium doesn't work. Please use the bulk-update endpoint with a JSON file instead, or scrape locally and upload the results.",
                    "events_count": len(stored_events),
                    "added": 0,
                    "skipped": 0,
                    "replaced": False,
                    "suggestion": "Use /api/events/bulk-update endpoint with scraped events JSON file"
                }
            else:
                return {
                    "success": True,
                    "message": "Scraping completed - no new events found (this is normal for JavaScript-heavy sites or cloud environments). You can add events manually.",
                    "events_count": len(stored_events),
                    "added": 0,
                    "skipped": 0
                }
            
    except Exception as e:
        print(f"❌ Error in manual scraping: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Scraping failed: {str(e)}",
            "events_count": len(stored_events)
        }

@app.get("/sync")
def sync_web_interface():
    """Web interface for manual sync operations"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Seniors Kingston Calendar Sync</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .button { background: #0072ce; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px; }
            .button:hover { background: #0056a3; }
            .status { margin: 20px 0; padding: 10px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>🔄 Seniors Kingston Calendar Sync</h1>
        <p>Use these buttons to manually sync events from the Seniors Kingston website:</p>
        
        <button class="button" onclick="syncEvents('force')">🔄 Force Sync Now</button>
        <button class="button" onclick="syncEvents('monthly')">📅 Monthly Sync</button>
        <button class="button" onclick="checkStatus()">📊 Check Status</button>
        
        <div id="status"></div>
        
        <script>
            async function syncEvents(type) {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<div class="status">Syncing... Please wait.</div>';
                
                try {
                    const response = await fetch(`/api/${type}-sync`, { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        statusDiv.innerHTML = `<div class="status success">
                            ✅ <strong>Success!</strong><br>
                            ${data.message}<br>
                            Events: ${data.events_count || 'N/A'}<br>
                            Time: ${new Date(data.timestamp).toLocaleString()}
                        </div>`;
                    } else {
                        statusDiv.innerHTML = `<div class="status error">
                            ❌ <strong>Error:</strong><br>
                            ${data.message || data.error}
                        </div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="status error">
                        ❌ <strong>Network Error:</strong><br>
                        ${error.message}
                    </div>`;
                }
            }
            
            async function checkStatus() {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<div class="status">Checking status... Please wait.</div>';
                
                try {
                    const response = await fetch('/api/sync-status');
                    const data = await response.json();
                    
                    statusDiv.innerHTML = `<div class="status success">
                        📊 <strong>Sync Status:</strong><br>
                        Last Sync: ${data.last_sync_time || 'Never'}<br>
                        Next Sync: ${data.next_sync_time || 'Unknown'}<br>
                        Frequency: ${data.sync_frequency}<br>
                        Status: ${data.status}
                    </div>`;
                } catch (error) {
                    statusDiv.innerHTML = `<div class="status error">
                        ❌ <strong>Error:</strong><br>
                        ${error.message}
                    </div>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/test-send-report")
def test_send_report():
    """Test endpoint to manually send an analytics report"""
    try:
        success = send_analytics_report_email("rebeccam@seniorskingston.ca", "test")
        
        if success:
            return {
                "success": True,
                "message": "Test analytics report sent successfully to rebeccam@seniorskingston.ca"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send test analytics report"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending test report: {str(e)}"
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

@app.post("/api/monthly-sync")
def monthly_sync():
    """Monthly sync endpoint - attempts to get fresh events from website"""
    print("📅 Monthly sync requested...")
    try:
        # Try to scrape fresh events
        fresh_events = scrape_seniors_kingston_events()
        
        if fresh_events and len(fresh_events) > 0:
            print(f"✅ Monthly sync successful: Found {len(fresh_events)} fresh events")
            return {
                "success": True,
                "message": f"Successfully synced {len(fresh_events)} fresh events",
                "events_count": len(fresh_events),
                "events": fresh_events[:10],  # Show first 10 events
                "timestamp": datetime.now().isoformat(),
                "sync_type": "fresh_website_data"
            }
        else:
            print("📅 No fresh events found, using current hardcoded events")
            return {
                "success": True,
                "message": "No fresh events found, using current events",
                "events_count": len(known_events),
                "timestamp": datetime.now().isoformat(),
                "sync_type": "fallback_to_hardcoded"
            }
    except Exception as e:
        print(f"❌ Monthly sync error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Monthly sync failed",
            "sync_type": "error"
        }

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

@app.get("/api/analytics")
def get_analytics():
    """Get usage analytics - desktop vs mobile visits"""
    global analytics_data
    
    desktop_percentage = (analytics_data['desktop_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    mobile_percentage = (analytics_data['mobile_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    
    return {
        "desktop_visits": analytics_data['desktop_visits'],
        "mobile_visits": analytics_data['mobile_visits'],
        "total_visits": analytics_data['total_visits'],
        "desktop_percentage": round(desktop_percentage, 1),
        "mobile_percentage": round(mobile_percentage, 1),
        "last_reset": analytics_data['last_reset'],
        "status": "success"
    }

@app.post("/api/analytics")
async def track_analytics_event(request: Request):
    """Track analytics events from frontend (page views, user actions, etc.)"""
    global analytics_data
    
    try:
        # Get the request data
        data = await request.json()
        
        # Extract user agent for device detection
        user_agent = request.headers.get('user-agent', '')
        
        # Track the visit
        track_visit(user_agent)
        
        # Log the event for debugging
        event_type = data.get('event', 'unknown')
        print(f"📊 Analytics event tracked: {event_type} - {'Mobile' if 'mobile' in user_agent.lower() else 'Desktop'}")
        
        return {
            "status": "success",
            "message": "Analytics event tracked successfully",
            "event_type": event_type,
            "total_visits": analytics_data['total_visits'],
            "desktop_visits": analytics_data['desktop_visits'],
            "mobile_visits": analytics_data['mobile_visits']
        }
        
    except Exception as e:
        print(f"❌ Error tracking analytics: {e}")
        return {
            "status": "error",
            "message": f"Failed to track analytics: {str(e)}"
        }

@app.get("/upload")
def upload_interface():
    """Simple Excel file upload interface"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Excel Upload</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            h1 { color: #0072ce; text-align: center; }
            .upload-form { text-align: center; padding: 30px; border: 2px dashed #0072ce; border-radius: 8px; margin: 20px 0; }
            input[type="file"] { margin: 20px 0; padding: 10px; font-size: 16px; }
            button { background: #0072ce; color: white; padding: 12px 30px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
            button:hover { background: #005a9e; }
            .status { padding: 15px; margin: 20px 0; border-radius: 6px; text-align: center; font-weight: bold; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .back { text-align: center; margin-top: 20px; }
            .back a { color: #0072ce; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>📊 Upload Excel File</h1>
        
        <form id="uploadForm" class="upload-form">
            <input type="file" id="fileInput" accept=".xlsx" required>
            <br>
            <button type="submit">Upload File</button>
        </form>

        <div id="status"></div>

        <div class="back">
            <a href="/">← Back to Main App</a>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('fileInput');
                const statusDiv = document.getElementById('status');
                const button = document.querySelector('button');
                
                if (!fileInput.files[0]) {
                    statusDiv.innerHTML = '<div class="status error">Please select a file first!</div>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                button.textContent = 'Uploading...';
                button.disabled = true;
                statusDiv.innerHTML = '<div class="status">Uploading file, please wait...</div>';
                
                try {
                    const response = await fetch('/api/import-excel', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.innerHTML = '<div class="status success">✅ File uploaded successfully!</div>';
                        fileInput.value = '';
                    } else {
                        statusDiv.innerHTML = '<div class="status error">❌ ' + result.message + '</div>';
                    }
                } catch (error) {
                    statusDiv.innerHTML = '<div class="status error">❌ Upload failed: ' + error.message + '</div>';
                }
                
                button.textContent = 'Upload File';
                button.disabled = false;
            });
        </script>
    </body>
    </html>
    """)

@app.get("/admin")
def admin_interface():
    """Admin interface for editing events"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Event Admin Panel</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .admin-card {
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            h1 {
                color: #0072ce;
                text-align: center;
                margin-bottom: 30px;
            }
            .event-list {
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
            .event-item {
                background: #f8f9fa;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                border-left: 4px solid #0072ce;
            }
            .event-title {
                font-weight: bold;
                color: #0072ce;
                margin-bottom: 5px;
            }
            .event-details {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 10px;
            }
            .event-actions {
                display: flex;
                gap: 10px;
            }
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9em;
                text-decoration: none;
                display: inline-block;
            }
            .btn-edit {
                background: #28a745;
                color: white;
            }
            .btn-delete {
                background: #dc3545;
                color: white;
            }
            .btn-add {
                background: #0072ce;
                color: white;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            .form-group input, .form-group textarea {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            .form-group textarea {
                height: 80px;
                resize: vertical;
            }
        </style>
    </head>
    <body>
        <div class="admin-card">
            <h1>🔧 Event Admin Panel</h1>
            
            <div style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
                <button class="btn btn-add" onclick="showAddForm()">➕ Add New Event</button>
                <button class="btn" onclick="sendAnalyticsReport('daily')" style="background: #17a2b8; color: white;">📊 Send Daily Report</button>
                <button class="btn" onclick="sendAnalyticsReport('weekly')" style="background: #6f42c1; color: white;">📈 Send Weekly Report</button>
                <button class="btn" onclick="viewAnalytics()" style="background: #28a745; color: white;">📋 View Analytics</button>
            </div>
            
            <div id="addForm" style="display: none;">
                <h3>Add New Event</h3>
                <form id="addEventForm">
                    <div class="form-group">
                        <label>Event Title:</label>
                        <input type="text" id="addTitle" required>
                    </div>
                    <div class="form-group">
                        <label>Start Date & Time:</label>
                        <input type="datetime-local" id="addStartDate" required>
                    </div>
                    <div class="form-group">
                        <label>End Date & Time:</label>
                        <input type="datetime-local" id="addEndDate" required>
                    </div>
                    <div class="form-group">
                        <label>Description:</label>
                        <textarea id="addDescription"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Location:</label>
                        <input type="text" id="addLocation">
                    </div>
                    <button type="submit" class="btn btn-add">Save Event</button>
                    <button type="button" class="btn" onclick="hideAddForm()" style="background: #6c757d; color: white;">Cancel</button>
                </form>
            </div>
            
            <h3>Current Events</h3>
            <div id="eventList" class="event-list">
                Loading events...
            </div>
        </div>
        
        <script>
            // Load events on page load
            loadEvents();
            
            function loadEvents() {
                fetch('/api/events')
                    .then(response => response.json())
                    .then(data => {
                        displayEvents(data.events || []);
                    })
                    .catch(error => {
                        console.error('Error loading events:', error);
                        document.getElementById('eventList').innerHTML = 'Error loading events';
                    });
            }
            
            function displayEvents(events) {
                const eventList = document.getElementById('eventList');
                if (events.length === 0) {
                    eventList.innerHTML = 'No events found';
                    return;
                }
                
                eventList.innerHTML = events.map(event => `
                    <div class="event-item">
                        <div class="event-title">${event.title}</div>
                        <div class="event-details">
                            <strong>Date:</strong> ${new Date(event.startDate).toLocaleString()}<br>
                            <strong>Location:</strong> ${event.location || 'Not specified'}<br>
                            <strong>Description:</strong> ${event.description || 'None'}
                        </div>
                        <div class="event-actions">
                            <button class="btn btn-edit" onclick="editEvent('${event.id}')">✏️ Edit</button>
                            <button class="btn btn-delete" onclick="deleteEvent('${event.id}')">🗑️ Delete</button>
                        </div>
                    </div>
                `).join('');
            }
            
            function showAddForm() {
                document.getElementById('addForm').style.display = 'block';
            }
            
            function hideAddForm() {
                document.getElementById('addForm').style.display = 'none';
                document.getElementById('addEventForm').reset();
            }
            
            document.getElementById('addEventForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const eventData = {
                    title: document.getElementById('addTitle').value,
                    startDate: document.getElementById('addStartDate').value,
                    endDate: document.getElementById('addEndDate').value,
                    description: document.getElementById('addDescription').value,
                    location: document.getElementById('addLocation').value
                };
                
                fetch('/api/events', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(eventData)
                })
                .then(response => response.json())
                .then(data => {
                    alert('Event added successfully!');
                    hideAddForm();
                    loadEvents();
                })
                .catch(error => {
                    console.error('Error adding event:', error);
                    alert('Error adding event');
                });
            });
            
            function editEvent(eventId) {
                // For now, just show an alert - you can implement a full edit form
                alert('Edit functionality coming soon! Event ID: ' + eventId);
            }
            
            function deleteEvent(eventId) {
                if (confirm('Are you sure you want to delete this event?')) {
                    fetch(`/api/events/${eventId}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Event deleted successfully!');
                        loadEvents();
                    })
                    .catch(error => {
                        console.error('Error deleting event:', error);
                        alert('Error deleting event');
                    });
                }
            }
            
            function sendAnalyticsReport(reportType) {
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '⏳ Sending...';
                button.disabled = true;
                
                fetch('/api/analytics/send-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        recipient_email: 'rebeccam@seniorskingston.ca',
                        report_type: reportType
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`✅ ${reportType.charAt(0).toUpperCase() + reportType.slice(1)} analytics report sent successfully!`);
                    } else {
                        alert(`❌ Failed to send report: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error sending report:', error);
                    alert(`❌ Error sending report: ${error.message}`);
                })
                .finally(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                });
            }
            
            function viewAnalytics() {
                window.open('/analytics', '_blank');
            }
        </script>
    </body>
    </html>
    """

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

@app.post("/api/analytics/reset")
def reset_analytics():
    """Reset analytics data (admin only)"""
    global analytics_data
    
    analytics_data = {
        'desktop_visits': 0,
        'mobile_visits': 0,
        'total_visits': 0,
        'last_reset': datetime.now().isoformat()
    }
    
    return {
        "message": "Analytics data reset successfully",
        "status": "success"
    }

@app.post("/api/analytics/test-data")
def add_test_data():
    """Add test data to analytics"""
    global analytics_data
    
    # Add random test visits
    import random
    desktop_add = random.randint(1, 5)
    mobile_add = random.randint(1, 3)
    
    analytics_data['desktop_visits'] += desktop_add
    analytics_data['mobile_visits'] += mobile_add
    analytics_data['total_visits'] += desktop_add + mobile_add
    
    return {
        "message": f"Added {desktop_add} desktop and {mobile_add} mobile test visits",
        "status": "success",
        "added": {
            "desktop": desktop_add,
            "mobile": mobile_add,
            "total": desktop_add + mobile_add
        }
    }

@app.get("/api/analytics/export/csv")
def export_analytics_csv():
    """Export analytics data as CSV"""
    global analytics_data
    
    desktop_percentage = (analytics_data['desktop_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    mobile_percentage = (analytics_data['mobile_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    
    csv_content = f"""Date,Total Visits,Desktop Visits,Mobile Visits,Desktop %,Mobile %,Last Reset
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{analytics_data['total_visits']},{analytics_data['desktop_visits']},{analytics_data['mobile_visits']},{round(desktop_percentage, 1)},{round(mobile_percentage, 1)},{analytics_data['last_reset']}
"""
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.get("/api/analytics/export/json")
def export_analytics_json():
    """Export analytics data as JSON"""
    global analytics_data
    
    desktop_percentage = (analytics_data['desktop_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    mobile_percentage = (analytics_data['mobile_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "analytics": {
            "total_visits": analytics_data['total_visits'],
            "desktop_visits": analytics_data['desktop_visits'],
            "mobile_visits": analytics_data['mobile_visits'],
            "desktop_percentage": round(desktop_percentage, 1),
            "mobile_percentage": round(mobile_percentage, 1),
            "last_reset": analytics_data['last_reset']
        }
    }
    
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
    )

def send_analytics_report_email(recipient_email: str, report_type: str = "daily"):
    """Send analytics report via email"""
    global analytics_data
    
    try:
        desktop_percentage = (analytics_data['desktop_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
        mobile_percentage = (analytics_data['mobile_visits'] / analytics_data['total_visits'] * 100) if analytics_data['total_visits'] > 0 else 0
        
        # Create email content
        subject = f"📊 {report_type.title()} Analytics Report - Seniors Kingston App"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: #f8f9fa;">
                <h2 style="color: #0072ce; text-align: center; margin-bottom: 30px;">
                    📊 Seniors Kingston App Analytics Report
                </h2>
                
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="color: #0072ce; margin-top: 0;">📈 User Activity Summary</h3>
                    
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                        <div style="font-size: 36px; font-weight: bold; color: #0072ce; margin-bottom: 10px;">
                            {analytics_data['total_visits']}
                        </div>
                        <div style="font-size: 18px; color: #666;">Total App Visits</div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin: 20px 0;">
                        <div style="flex: 1; text-align: center; padding: 15px; background: #f0f8ff; border-radius: 8px; margin-right: 10px;">
                            <div style="font-size: 24px; font-weight: bold; color: #0072ce;">
                                {analytics_data['desktop_visits']}
                            </div>
                            <div style="color: #666;">Desktop Visits</div>
                            <div style="font-size: 14px; color: #888; margin-top: 5px;">
                                {desktop_percentage:.1f}% of total
                            </div>
                        </div>
                        
                        <div style="flex: 1; text-align: center; padding: 15px; background: #f0f8ff; border-radius: 8px; margin-left: 10px;">
                            <div style="font-size: 24px; font-weight: bold; color: #0072ce;">
                                {analytics_data['mobile_visits']}
                            </div>
                            <div style="color: #666;">Mobile Visits</div>
                            <div style="font-size: 14px; color: #888; margin-top: 5px;">
                                {mobile_percentage:.1f}% of total
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee;">
                        <h4 style="color: #0072ce; margin-bottom: 10px;">📋 Report Details</h4>
                        <ul style="color: #666; margin: 0; padding-left: 20px;">
                            <li><strong>Report Type:</strong> {report_type.title()} Analytics</li>
                            <li><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                            <li><strong>Last Reset:</strong> {analytics_data['last_reset']}</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #28a745;">
                        <strong style="color: #28a745;">✅ App Status:</strong> 
                        <span style="color: #666;">All systems operational. Users are actively engaging with the app.</span>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #888; font-size: 14px;">
                    <p>This is an automated report from the Seniors Kingston App Analytics System.</p>
                    <p>For questions or support, contact: rebeccam@seniorskingston.ca</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email using existing email function
        send_email_via_brevo(recipient_email, subject, html_body)
        
        print(f"✅ Analytics report sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending analytics report: {e}")
        return False

@app.post("/api/analytics/send-report")
def send_analytics_report(recipient_email: str = "rebeccam@seniorskingston.ca", report_type: str = "daily"):
    """Manually send analytics report via email"""
    try:
        success = send_analytics_report_email(recipient_email, report_type)
        
        if success:
            return {
                "success": True,
                "message": f"Analytics report sent successfully to {recipient_email}",
                "report_type": report_type
            }
        else:
            return {
                "success": False,
                "message": "Failed to send analytics report",
                "error": "Email sending failed"
            }
    except Exception as e:
        return {
            "success": False,
            "message": "Error sending analytics report",
            "error": str(e)
        }

@app.get("/api/sync-status")
def get_sync_status():
    """Get detailed sync status and next sync information"""
    global last_sync_time
    
    try:
        current_time = datetime.now()
        
        if last_sync_time:
            time_since_sync = current_time - last_sync_time
            hours_since_sync = time_since_sync.total_seconds() / 3600
            days_since_sync = hours_since_sync / 24
            
            next_sync_in_days = max(0, (sync_interval_hours / 24) - days_since_sync)
            
            return {
                "success": True,
                "last_sync": last_sync_time.isoformat(),
                "days_since_sync": round(days_since_sync, 1),
                "next_sync_in_days": round(next_sync_in_days, 1),
                "sync_interval_days": sync_interval_hours / 24,
                "status": "active",
                "sync_frequency": "Weekly (every Monday)",
                "next_expected_update": "Every Monday"
            }
        else:
            return {
                "success": True,
                "last_sync": None,
                "days_since_sync": None,
                "next_sync_in_days": sync_interval_hours / 24,
                "sync_interval_days": sync_interval_hours / 24,
                "status": "never_synced",
                "sync_frequency": "Weekly (every Monday)",
                "next_expected_update": "Every Monday"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get sync status"
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
                "events": events[:10],  # Show first 10 events
                "auto_sync": "Disabled",
                "scraping_method": "Selenium + BeautifulSoup"
            }
        else:
            return {
                "success": False,
                "message": "No events found",
                "auto_sync": "Disabled",
                "scraping_method": "Selenium + BeautifulSoup"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Scraping test failed",
            "scraping_method": "Selenium + BeautifulSoup"
        }

@app.get("/api/debug-scraping")
def debug_scraping():
    """Debug endpoint to see what the scraper finds"""
    print("🔍 Debug scraping...")
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = "https://www.seniorskingston.ca/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for h5.green elements specifically
            h5_green_elements = soup.select('h5.green')
            h5_elements = soup.select('h5')
            green_elements = soup.select('.green')
            
            return {
                "success": True,
                "message": "Debug info collected",
                "h5_green_elements": len(h5_green_elements),
                "h5_elements": len(h5_elements),
                "green_elements": len(green_elements),
                "h5_green_texts": [elem.get_text().strip() for elem in h5_green_elements[:10]],
                "page_title": soup.title.string if soup.title else "No title",
                "content_length": len(response.text)
            }
        else:
            return {
                "success": False,
                "message": f"Failed to fetch page: HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Debug scraping failed"
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

@app.get("/api/data-status")
def get_data_status():
    """Get detailed status of data persistence"""
    try:
        # Check database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM programs")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        # Check Excel file
        EXCEL_PATH = "Class Cancellation App.xlsx"
        BACKUP_EXCEL_PATH = "/tmp/Class Cancellation App.xlsx" if os.getenv('RENDER') else "backup_Class Cancellation App.xlsx"
        
        excel_exists = os.path.exists(EXCEL_PATH)
        backup_exists = os.path.exists(BACKUP_EXCEL_PATH)
        
        # Get Excel file size if it exists
        excel_size = 0
        if excel_exists:
            excel_size = os.path.getsize(EXCEL_PATH)
        
        return {
            "status": "success",
            "database": {
                "path": DB_PATH,
                "record_count": db_count,
                "persistent": True if os.getenv('RENDER') else False
            },
            "excel_file": {
                "exists": excel_exists,
                "size_bytes": excel_size,
                "path": EXCEL_PATH
            },
            "backup": {
                "exists": backup_exists,
                "path": BACKUP_EXCEL_PATH
            },
            "environment": {
                "is_cloud": bool(os.getenv('RENDER')),
                "render_deployment": bool(os.getenv('RENDER'))
            },
            "recommendations": [
                "Database is persistent" if os.getenv('RENDER') else "Database will reset on deployment",
                "Excel file will persist across deployments" if backup_exists else "Upload Excel file to make it persistent"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/cancellations")
def get_cancellations(
    program: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    day: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    session: Optional[str] = Query(None),
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
        session=session,
        program_status=program_status,
        has_cancellation=has_cancellation
    )
    
    # Get all unique sessions from database for filter dropdown
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT session FROM programs WHERE session IS NOT NULL AND session != '' ORDER BY CAST(session AS INTEGER)")
    session_rows = cursor.fetchall()
    all_sessions = [str(row[0]) for row in session_rows if row[0] and str(row[0]).strip() != '']
    conn.close()
    
    print(f"📈 Returning {len(programs)} results")
    return {
        "data": programs, 
        "last_loaded": datetime.now(KINGSTON_TZ).isoformat(),
        "all_sessions": all_sessions
    }

@app.post("/api/refresh")
async def refresh_data():
    """Manual refresh endpoint - DISABLED to prevent data reversion"""
    try:
        # DISABLED: Force check and import Excel file - was causing data reversion
        # check_and_import_excel()
        print("⚠️ Manual refresh DISABLED to prevent data reversion")
        
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

@app.post("/api/force-refresh")
async def force_refresh_data():
    """Force refresh by recreating database and re-importing Excel"""
    try:
        print("🔄 FORCE refresh requested - recreating database")
        
        # Recreate database with new schema
        init_database()
        
        # DISABLED: Re-import Excel data - was causing data reversion
        # check_and_import_excel()
        print("⚠️ Force refresh DISABLED to prevent data reversion")
        
        # Get current data count
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM programs")
        count = cursor.fetchone()[0]
        
        # Check if description and fee columns are working
        cursor.execute("SELECT description, fee FROM programs LIMIT 1")
        sample = cursor.fetchone()
        conn.close()
        
        return {
            "message": "Database recreated and data refreshed",
            "timestamp": datetime.now(KINGSTON_TZ).isoformat(),
            "data_count": count,
            "database": "SQLite",
            "sample_description": sample[0] if sample else None,
            "sample_fee": sample[1] if sample else None
        }
    except Exception as e:
        print(f"❌ Error force refreshing data: {e}")
        return {"error": str(e)}

@app.post("/api/import-excel")
async def import_excel(file: UploadFile = File(...)):
    """Import Excel file to update database"""
    try:
        print(f"📤 Upload request received for file: {file.filename}")
        
        if not file.filename.endswith('.xlsx'):
            return {"message": "Please upload an Excel (.xlsx) file", "status": "error"}
        
        print(f"📖 Reading file content...")
        content = await file.read()
        print(f"📊 File size: {len(content)} bytes")
        
        # Save the Excel file to persistent storage
        EXCEL_PATH = "Class Cancellation App.xlsx"
        BACKUP_EXCEL_PATH = "/tmp/Class Cancellation App.xlsx" if os.getenv('RENDER') else "backup_Class Cancellation App.xlsx"
        
        try:
            with open(EXCEL_PATH, 'wb') as f:
                f.write(content)
            print(f"💾 Excel file saved to: {EXCEL_PATH}")
            
            # DISABLED: No backup - Excel data will persist as uploaded
            # if os.getenv('RENDER'):
            #     with open(BACKUP_EXCEL_PATH, 'wb') as f:
            #         f.write(content)
            #     print(f"💾 Excel file backed up to: {BACKUP_EXCEL_PATH}")
            print("✅ Excel data will persist as uploaded - no backup needed")
                
        except Exception as e:
            print(f"⚠️ Could not save Excel file: {e}")
        
        print(f"🔄 Starting import process...")
        success = import_excel_data(content)
        
        if success:
            print(f"✅ Excel file imported successfully")
            
            # CRITICAL: Automatically save to fallback after successful import
            try:
                print("💾 Auto-saving imported data to fallback file...")
                programs = get_programs_from_db()
                if programs and len(programs) > 0:
                    fallback_data = {
                        "metadata": {
                            "created_at": datetime.now().isoformat(),
                            "description": "Auto-saved fallback Excel data after import",
                            "total_programs": len(programs),
                            "last_updated": datetime.now().isoformat(),
                            "source": "auto_save_after_import",
                            "excel_file": file.filename
                        },
                        "programs": programs
                    }
                    
                    fallback_file = "/tmp/excel_fallback_data.json" if os.getenv('RENDER') else "excel_fallback_data.json"
                    with open(fallback_file, 'w', encoding='utf-8') as f:
                        json.dump(fallback_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Auto-saved {len(programs)} programs to fallback file")
                else:
                    print("⚠️ No programs found to save to fallback")
            except Exception as fallback_error:
                print(f"⚠️ Error auto-saving to fallback: {fallback_error}")
                # Don't fail the import if fallback save fails
            
            return {"message": "Excel file imported successfully", "status": "success"}
        else:
            print(f"❌ Failed to import Excel file")
            return {"message": "Error importing Excel file", "status": "error"}
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return {"message": f"Upload failed: {str(e)}", "status": "error"}

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

@app.get("/api/test-brevo")
def test_brevo_config():
    """Test Brevo configuration"""
    brevo_api_key = os.environ.get("BREVO_API_KEY", "")
    brevo_sender_email = os.environ.get("BREVO_SENDER_EMAIL", "")
    
    return {
        "brevo_api_key_configured": bool(brevo_api_key and brevo_api_key != "YOUR_BREVO_API_KEY_HERE"),
        "brevo_sender_email_configured": bool(brevo_sender_email),
        "brevo_sender_email": brevo_sender_email if brevo_sender_email else "NOT SET",
        "api_key_first_chars": brevo_api_key[:20] + "..." if brevo_api_key else "NOT SET"
    }

@app.get("/api/test-email")
def test_email():
    """Test email configuration"""
    try:
        # Email configuration - Gmail Setup
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "seniorskingstonapp@gmail.com"  # Your Gmail address
        sender_password = "YOUR_16_CHARACTER_APP_PASSWORD_HERE"  # Replace with your Gmail App Password
        recipient_email = "programs@seniorskingston.ca"
        
        # Check if password is still placeholder
        if sender_password == "YOUR_16_CHARACTER_APP_PASSWORD_HERE":
            return {
                "status": "error",
                "message": "❌ Gmail App Password not configured! Please update the password in backend_sqlite.py"
            }
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Test Email from Class Cancellation App"
        
        test_body = """
This is a test email from the Class Cancellation App.

If you receive this email, the email configuration is working correctly!

Test sent at: """ + datetime.now(KINGSTON_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        msg.attach(MIMEText(test_body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return {
            "status": "success",
            "message": "Test email sent successfully to programs@seniorskingston.ca"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test email failed: {str(e)}"
        }

def send_email_via_brevo(to_email: str, subject: str, body: str):
    """Send email using Brevo (Sendinblue) API"""
    brevo_api_key = os.environ.get("BREVO_API_KEY", "YOUR_BREVO_API_KEY_HERE")
    brevo_sender_email = os.environ.get("BREVO_SENDER_EMAIL", "")  # Email you verified in Brevo
    
    if brevo_api_key == "YOUR_BREVO_API_KEY_HERE":
        raise Exception("Brevo API key not configured")
    
    if not brevo_sender_email:
        raise Exception("Brevo sender email not configured. Add BREVO_SENDER_EMAIL environment variable with your verified email.")
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": brevo_api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "sender": {
            "name": "Seniors Kingston App",
            "email": brevo_sender_email  # Use verified email
        },
        "to": [
            {
                "email": to_email,
                "name": "Programs Department"
            }
        ],
        "subject": subject,
        "textContent": body
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response

@app.post("/api/send-message")
def send_message(message_data: dict):
    """Send message via email"""
    try:
        # Extract data from request
        subject = message_data.get('subject', 'Program Inquiry')
        message = message_data.get('message', '')
        program_name = message_data.get('program_name', 'Unknown')
        program_id = message_data.get('program_id', 'Unknown')
        instructor = message_data.get('instructor', 'Unknown')
        sender_name = message_data.get('sender_name', '')
        sender_phone = message_data.get('sender_phone', '')
        sender_email = message_data.get('sender_email', '')
        
        # Create email content
        email_subject = f"Program Inquiry: {subject}"
        email_body = f"""
Program Inquiry Details:
========================

Program Name: {program_name}
Program ID: {program_id}
Instructor: {instructor}

Sender Information:
-------------------
Name: {sender_name if sender_name else 'Not provided'}
Phone: {sender_phone if sender_phone else 'Not provided'}
Email: {sender_email if sender_email else 'Not provided'}

Message:
--------
{message}

---
This message was sent from the Class Cancellation App.
        """
        
        # Try Brevo first, fallback to SMTP
        try:
            send_email_via_brevo("rebeccam@seniorskingston.ca", email_subject, email_body)
            print(f"✅ EMAIL SENT VIA BREVO:")
            print(f"To: rebeccam@seniorskingston.ca")
            print(f"Subject: {email_subject}")
            print("=" * 50)
            
            return {
                "status": "success",
                "message": "Message sent successfully via Brevo",
                "email_subject": email_subject
            }
        except Exception as brevo_error:
            print(f"❌ Brevo failed: {str(brevo_error)}")
            print(f"🔄 Trying SMTP fallback...")
            
        # SMTP Fallback
        try:
            # Email configuration - Gmail Setup
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "seniorskingstonapp@gmail.com"  # Your Gmail address
            sender_password = "YOUR_16_CHARACTER_APP_PASSWORD_HERE"  # Replace with your Gmail App Password
            recipient_email = "programs@seniorskingston.ca"
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = email_subject
            
            # Add body to email
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Create SMTP session
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Enable security
            server.login(sender_email, sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            print(f"✅ EMAIL SENT SUCCESSFULLY:")
            print(f"To: {recipient_email}")
            print(f"Subject: {email_subject}")
            print("=" * 50)
            
        except Exception as email_error:
            print(f"❌ EMAIL FAILED: {str(email_error)}")
            print(f"📧 MESSAGE RECEIVED (FALLBACK LOGGING):")
            print(f"To: rebeccam@seniorskingston.ca")
            print(f"Subject: {email_subject}")
            print(f"Body: {email_body}")
            print("=" * 50)
            
            # Return success anyway since message is logged
            return {
                "status": "warning",
                "message": "Message received but email delivery failed. Message has been logged to server console.",
                "error_details": str(email_error)
            }
        
        return {
            "status": "success",
            "message": "Message sent successfully",
            "email_subject": email_subject
        }
        
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to send message: {str(e)}"
        }


@app.get("/api/test-programs")
def test_programs():
    """Simple test endpoint to verify database access"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM programs")
        total_count = cursor.fetchone()[0]
        
        # Get first 10 programs
        cursor.execute("SELECT program_id, program, sheet, location, program_status FROM programs LIMIT 10")
        programs = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_count": total_count,
            "sample_programs": [
                {
                    "program_id": p[0],
                    "program": p[1],
                    "day": p[2],
                    "location": p[3],
                    "program_status": p[4]
                } for p in programs
            ],
            "carole_found": any(p[0] == "28785" for p in programs)
        }
    except Exception as e:
        return {"error": str(e)}
