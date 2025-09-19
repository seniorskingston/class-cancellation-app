import os
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import re
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Use environment variable for port, default to 8000 (Render uses PORT env var)
PORT = int(os.environ.get("PORT", 8000))

# Use environment variable for Excel path, fallback to local path
EXCEL_PATH = os.environ.get("EXCEL_PATH", './Class Cancellation App.xlsx')

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

cancellations_data = []
last_loaded = None
events_data = []
events_last_loaded = None

def get_col(row, possible_names):
    for name in possible_names:
        if name in row:
            return row[name]
    return ''

def safe_str(val):
    if pd.isnull(val):
        return ""
    return str(val)

def parse_date_range(date_range):
    match = re.findall(r'(\d{2}/\d{2}/\d{4})', date_range)
    if len(match) == 2:
        start = datetime.strptime(match[0], "%d/%m/%Y")
        end = datetime.strptime(match[1], "%d/%m/%Y")
        return start, end
    return None, None

def weekday_from_sheet(sheet):
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    sheet_lower = sheet.strip().lower()
    for i, d in enumerate(days):
        if d in sheet_lower:
            return i
    return None



def parse_cancel_dates(cancel_str):
    if not cancel_str:
        return set()
    dates = re.findall(r'(\d{2}/\d{2}/\d{4})', cancel_str)
    return set(datetime.strptime(d, "%d/%m/%Y").strftime("%d/%m/%Y") for d in dates)

def generate_class_dates(start, end, weekdays):
    dates = []
    current = start
    while current <= end and current <= datetime.now():
        if current.weekday() in weekdays:
            dates.append(current.date())
        current += timedelta(days=1)
    return dates

def group_programs(rows):
    grouped = {}
    for row in rows:
        key = (row['program_id'], row['date_range'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(row)
    return grouped

def parse_event_date(date_str):
    """Parse various date formats from the events page"""
    if not date_str:
        return None
    
    # Common date formats to try
    date_formats = [
        "%B %d, %Y",  # September 20, 2024
        "%b %d, %Y",  # Sep 20, 2024
        "%Y-%m-%d",   # 2024-09-20
        "%m/%d/%Y",   # 09/20/2024
        "%d/%m/%Y",   # 20/09/2024
        "%B %d",      # September 20
        "%b %d",      # Sep 20
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), fmt)
            # If no year provided, assume current year
            if parsed_date.year == 1900:
                parsed_date = parsed_date.replace(year=datetime.now().year)
            return parsed_date
        except ValueError:
            continue
    
    return None

def scrape_seniors_kingston_events():
    """Scrape events from Seniors Kingston events page using Selenium"""
    global events_data, events_last_loaded
    
    print("🔍 Scraping Seniors Kingston events with Selenium...")
    
    driver = None
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to the events page
        print("Loading https://www.seniorskingston.ca/events...")
        driver.get('https://www.seniorskingston.ca/events')
        
        # Wait for the page to load and any dynamic content
        wait = WebDriverWait(driver, 20)
        
        # Wait for any event elements to load
        try:
            # Wait for any element that might contain events
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("Page loaded, waiting for dynamic content...")
            
            # Wait a bit more for JavaScript to load content
            import time
            time.sleep(5)
            
        except Exception as e:
            print(f"Timeout waiting for page load: {e}")
        
        # Get the page source after JavaScript execution
        page_source = driver.page_source
        print(f"Page source length after JS execution: {len(page_source)}")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        events = []
        
        # Look for event elements with more specific selectors
        event_selectors = [
            '[class*="event"]',
            '[class*="card"]',
            '[class*="item"]',
            'article',
            '.post',
            '.entry',
            '[data-testid*="event"]',
            '[data-cy*="event"]'
        ]
        
        event_elements = []
        for selector in event_selectors:
            elements = soup.select(selector)
            if elements:
                event_elements = elements
                print(f"Found {len(elements)} elements using selector: {selector}")
                break
        
        if not event_elements:
            # Look for any divs that might contain event info
            all_divs = soup.find_all('div')
            print(f"Total divs found: {len(all_divs)}")
            
            # Look for divs with text that might be events
            for div in all_divs:
                text = div.get_text(strip=True)
                if len(text) > 10 and any(keyword in text.lower() for keyword in ['event', 'meeting', 'class', 'workshop', 'seminar']):
                    event_elements.append(div)
            
            print(f"Found {len(event_elements)} potential event divs")
        
        # Extract events from elements
        for element in event_elements:
            try:
                text = element.get_text(strip=True)
                if len(text) < 10:  # Skip very short text
                    continue
                
                # Extract title (look for headings or links)
                title = ""
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'strong', 'b'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    # Use first line of text as title
                    lines = text.split('\n')
                    title = lines[0] if lines else text[:50]
                
                if not title or len(title) < 3:
                    continue
                
                # Look for date patterns in the text
                date_patterns = [
                    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
                    r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY/MM/DD
                    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',  # Mon DD, YYYY
                ]
                
                date_str = ""
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        break
                
                # Look for time patterns
                time_pattern = r'(\d{1,2}:\d{2}\s*(AM|PM|am|pm)?)'
                time_match = re.search(time_pattern, text)
                time_str = time_match.group(1) if time_match else ""
                
                # Parse date
                start_date = parse_event_date(date_str)
                if not start_date:
                    # If no specific date found, create a sample date
                    start_date = datetime.now() + timedelta(days=len(events) + 1)
                
                # Parse time
                start_time = start_date
                if time_str:
                    try:
                        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', time_str)
                        if time_match:
                            hour = int(time_match.group(1))
                            minute = int(time_match.group(2))
                            period = time_match.group(3)
                            
                            if period and period.upper() == 'PM' and hour != 12:
                                hour += 12
                            elif period and period.upper() == 'AM' and hour == 12:
                                hour = 0
                            
                            start_time = start_date.replace(hour=hour, minute=minute)
                    except:
                        pass
                
                # Create end time
                end_time = start_time + timedelta(hours=1)
                
                event = {
                    'title': title,
                    'startDate': start_time.isoformat(),
                    'endDate': end_time.isoformat(),
                    'description': text[:200] + "..." if len(text) > 200 else text,
                    'location': 'Seniors Kingston',
                    'dateStr': date_str,
                    'timeStr': time_str
                }
                
                events.append(event)
                print(f"Scraped event: {title}")
                
            except Exception as e:
                print(f"Error parsing event element: {e}")
                continue
        
        events_data = events
        events_last_loaded = datetime.now()
        print(f"✅ Successfully scraped {len(events)} events")
        
    except Exception as e:
        print(f"❌ Error scraping events: {e}")
        # Keep existing events data if scraping fails
        if not events_data:
            events_data = []
            events_last_loaded = datetime.now()
    finally:
        if driver:
            driver.quit()

def load_cancellations():
    global cancellations_data, last_loaded
    print(f"🔍 Loading cancellations from: {EXCEL_PATH}")
    print(f"🔍 File exists: {os.path.exists(EXCEL_PATH)}")
    
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Excel file not found at: {EXCEL_PATH}")
        print(f"❌ Current working directory: {os.getcwd()}")
        print(f"❌ Directory contents: {os.listdir('.')}")
        cancellations_data = []
        last_loaded = datetime.now()
        return
    xl = pd.ExcelFile(EXCEL_PATH)
    all_rows = []
    total_rows = 0
    filtered_rows = 0
    print("Processing sheets:", xl.sheet_names)
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        cols = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df.columns = cols
        count_cancellations = 0
        sheet_rows = 0
        for _, row in df.iterrows():
            total_rows += 1
            row_dict = row.to_dict()
            program = get_col(row_dict, ['event', 'Event'])
            program_id = get_col(row_dict, ['course_id', 'Course ID'])
            date_range = get_col(row_dict, ['date', 'Date'])
            time = get_col(row_dict, ['time', 'Time'])
            location = get_col(row_dict, ['location', 'Location'])
            
            # Check actions for cancellation
            actions = str(get_col(row_dict, ['actions', 'Actions'])).strip().upper() == 'TRUE'
            program_status = "Cancelled" if actions else "Active"
            class_cancellation = get_col(row_dict, ['cancellation_date', 'cancellationdate', 'cancelled_date', 'cancel_date', 'Cancellation Date'])
            
            note = get_col(row_dict, ['note', 'Note'])
            
            # Skip rows with no program information - be less strict
            if not program and not program_id:
                continue
                
            filtered_rows += 1
            sheet_rows += 1
            all_rows.append({
                'sheet': safe_str(sheet),
                'program': safe_str(program),
                'program_id': safe_str(program_id),
                'date_range': safe_str(date_range),
                'time': safe_str(time),
                'location': safe_str(location),
                'class_room': safe_str(get_col(row_dict, ['facility', 'Facility'])),  # New: Class Room from Facility
                'instructor': safe_str(get_col(row_dict, ['instructor', 'Instructor'])),  # New: Instructor
                'program_status': safe_str(program_status),
                'class_cancellation': safe_str(class_cancellation),
                'note': safe_str(note),
            })
            if safe_str(class_cancellation).strip() != '':
                count_cancellations += 1
        print(f"Sheet '{sheet}': {count_cancellations} cancellations found, {sheet_rows} valid rows processed.")
    print(f"Total rows processed: {total_rows}, Valid rows after filtering: {filtered_rows}")
    print(f"Rows to be grouped: {len(all_rows)}")
    grouped = group_programs(all_rows)
    enriched_rows = []
    for (program_id, date_range), group in grouped.items():
        weekdays = set()
        for row in group:
            wd = weekday_from_sheet(row['sheet'])
            if wd is not None:
                weekdays.add(wd)
        start, end = parse_date_range(date_range)
        if not start or not end:
            classes_finished = 0
        else:
            class_dates = generate_class_dates(start, end, weekdays)
            cancel_dates = set()
            for row in group:
                cancel_dates |= parse_cancel_dates(row['class_cancellation'])
            finished_dates = [d for d in class_dates if d <= datetime.now().date() and d.strftime("%d/%m/%Y") not in cancel_dates]
            classes_finished = len(finished_dates)
        withdrawal = "No" if classes_finished >= 3 else "Yes"
        for row in group:
            # For cancelled programs, set withdrawal to empty
            if row['program_status'] == 'Cancelled':
                row['withdrawal'] = ""
            else:
                row['withdrawal'] = safe_str(withdrawal)
            enriched_rows.append(row)
    
    cancellations_data = enriched_rows
    last_loaded = datetime.now()
    print(f"✅ Successfully loaded {len(cancellations_data)} records")
    print(f"✅ Last loaded: {last_loaded}")

load_cancellations()
scrape_seniors_kingston_events()

scheduler = BackgroundScheduler()
scheduler.add_job(load_cancellations, 'interval', minutes=5)
scheduler.add_job(scrape_seniors_kingston_events, 'interval', minutes=30)  # Scrape events every 30 minutes
scheduler.start()

@app.get("/api/cancellations")
def get_cancellations(
    program: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    day: Optional[str] = Query(None),
    program_status: Optional[str] = Query(None),
    has_cancellation: Optional[bool] = Query(False),
):
    print(f"🌐 API call received from frontend")
    print(f"📊 Query params: {locals()}")
    print(f"📈 Total data available: {len(cancellations_data)} rows")
    
    results = []
    for row in cancellations_data:
        if program and program.lower() not in str(row['program']).lower():
            continue
        if program_id and program_id.lower() not in str(row['program_id']).lower():
            continue
        if day and day.lower() != str(row['sheet']).lower():
            continue
        if date:
            if date not in str(row['date_range']) and date != row['class_cancellation']:
                continue
        if program_status and program_status != row['program_status']:
            continue
        if has_cancellation and not row['class_cancellation']:
            continue
        results.append(row)
    
    print(f"Returning {len(results)} results")
    return {"data": results, "last_loaded": last_loaded}

@app.post("/api/refresh")
def manual_refresh():
    load_cancellations()
    return {"status": "refreshed", "last_loaded": last_loaded}

@app.get("/api/events")
def get_events():
    """Get scraped events from Seniors Kingston"""
    print(f"🌐 Events API call received")
    print(f"📈 Events available: {len(events_data)}")
    
    return {
        "events": events_data,
        "last_loaded": events_last_loaded.isoformat() if events_last_loaded else None,
        "count": len(events_data)
    }

@app.post("/api/refresh-events")
def manual_refresh_events():
    """Manually refresh events from Seniors Kingston"""
    scrape_seniors_kingston_events()
    return {
        "status": "events refreshed", 
        "last_loaded": events_last_loaded.isoformat() if events_last_loaded else None,
        "count": len(events_data)
    }

@app.get("/api/test")
def test_connection():
    """Test endpoint to verify CORS and connection"""
    return {
        "message": "Backend is working!",
        "timestamp": datetime.now().isoformat(),
        "data_count": len(cancellations_data),
        "cancellations_count": len([r for r in cancellations_data if r['class_cancellation']]),
        "events_count": len(events_data)
    }
