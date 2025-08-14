import os
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from datetime import datetime, timedelta
import re

# Use environment variable for port, default to 8000 (Render uses PORT env var)
PORT = int(os.environ.get("PORT", 8000))

# Use environment variable for Excel path, fallback to local path
EXCEL_PATH = os.environ.get("EXCEL_PATH", r'S:\Rebecca\Class Cancellation app\Class Cancellation App.xlsx')

app = FastAPI(title="Program Schedule Update API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cancellations_data = []
last_loaded = None

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

def load_cancellations():
    global cancellations_data, last_loaded
    if not os.path.exists(EXCEL_PATH):
        cancellations_data = []
        last_loaded = datetime.now()
        return
    xl = pd.ExcelFile(EXCEL_PATH)
    all_rows = []
    print("Processing sheets:", xl.sheet_names)
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        cols = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df.columns = cols
        count_cancellations = 0
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            program = get_col(row_dict, ['event'])
            program_id = get_col(row_dict, ['course_id'])
            date_range = get_col(row_dict, ['date'])
            time = get_col(row_dict, ['time'])
            location = get_col(row_dict, ['location'])
            actions = str(get_col(row_dict, ['actions'])).strip().upper() == 'TRUE'
            program_status = "Cancelled" if actions else "Active"
            class_cancellation = get_col(row_dict, ['cancellation_date', 'cancellationdate', 'cancelled_date', 'cancel_date'])
            note = get_col(row_dict, ['note'])
            
            # Skip rows with no program information
            if not program and not program_id and not date_range:
                continue
                
            all_rows.append({
                'sheet': safe_str(sheet),
                'program': safe_str(program),
                'program_id': safe_str(program_id),
                'date_range': safe_str(date_range),
                'time': safe_str(time),
                'location': safe_str(location),
                'program_status': safe_str(program_status),
                'class_cancellation': safe_str(class_cancellation),
                'note': safe_str(note),
            })
            if safe_str(class_cancellation).strip() != '':
                count_cancellations += 1
        print(f"Sheet '{sheet}': {count_cancellations} cancellations found.")
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
            # For cancelled programs, set classes_finished and withdrawal to empty
            if row['program_status'] == 'Cancelled':
                row['classes_finished'] = ""
                row['withdrawal'] = ""
            else:
                row['classes_finished'] = safe_str(classes_finished)
                row['withdrawal'] = safe_str(withdrawal)
            enriched_rows.append(row)
    cancellations_data = enriched_rows
    last_loaded = datetime.now()

load_cancellations()

scheduler = BackgroundScheduler()
scheduler.add_job(load_cancellations, 'interval', minutes=5)
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
    return {"data": results, "last_loaded": last_loaded}

@app.post("/api/refresh")
def manual_refresh():
    load_cancellations()
    return {"status": "refreshed", "last_loaded": last_loaded}