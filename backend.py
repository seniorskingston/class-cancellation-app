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
    """Scrape events from Seniors Kingston events page"""
    global events_data, events_last_loaded
    
    print("🔍 Scraping Seniors Kingston events...")
    
    try:
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Try to fetch the events page
        response = requests.get('https://www.seniorskingston.ca/events', headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Look for common event container patterns
        event_selectors = [
            '.event-item',
            '.event',
            '.calendar-event',
            '.event-card',
            '[class*="event"]',
            '.post',
            '.entry',
            'article'
        ]
        
        event_elements = []
        for selector in event_selectors:
            elements = soup.select(selector)
            if elements:
                event_elements = elements
                print(f"Found {len(elements)} events using selector: {selector}")
                break
        
        if not event_elements:
            # Fallback: look for any elements that might contain event info
            event_elements = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'event|post|entry|card', re.I))
            print(f"Fallback: Found {len(event_elements)} potential event elements")
        
        for element in event_elements:
            try:
                # Extract event title
                title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.event-title', 'a']
                title = ""
                for selector in title_selectors:
                    title_elem = element.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                if not title:
                    continue
                
                # Extract date
                date_selectors = ['.date', '.event-date', '.start-date', 'time', '[class*="date"]']
                date_str = ""
                for selector in date_selectors:
                    date_elem = element.select_one(selector)
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)
                        break
                
                # Extract time
                time_selectors = ['.time', '.event-time', '.start-time', '[class*="time"]']
                time_str = ""
                for selector in time_selectors:
                    time_elem = element.select_one(selector)
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)
                        break
                
                # Extract location
                location_selectors = ['.location', '.venue', '.place', '[class*="location"]', '[class*="venue"]']
                location = ""
                for selector in location_selectors:
                    location_elem = element.select_one(selector)
                    if location_elem:
                        location = location_elem.get_text(strip=True)
                        break
                
                # Extract description
                desc_selectors = ['.description', '.content', '.excerpt', '.summary', 'p']
                description = ""
                for selector in desc_selectors:
                    desc_elem = element.select_one(selector)
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                        break
                
                # Parse date
                start_date = parse_event_date(date_str)
                if not start_date:
                    # If no date found, skip this event
                    continue
                
                # Parse time if available
                start_time = start_date
                if time_str:
                    try:
                        # Try to parse time and add to date
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
                
                # Create end time (assume 1 hour duration if not specified)
                end_time = start_time + timedelta(hours=1)
                
                event = {
                    'title': title,
                    'startDate': start_time.isoformat(),
                    'endDate': end_time.isoformat(),
                    'description': description,
                    'location': location,
                    'dateStr': date_str,
                    'timeStr': time_str
                }
                
                events.append(event)
                print(f"Scraped event: {title} on {date_str}")
                
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
