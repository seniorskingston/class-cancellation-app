#!/usr/bin/env python3
"""
Simple script to import Excel data into SQLite database
"""
import pandas as pd
import sqlite3
import os

# Database file path
DB_PATH = "class_cancellations.db"

def import_excel_to_sqlite():
    """Import Excel data to SQLite database"""
    excel_file = "Class Cancellation App.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return False
    
    try:
        # Read Excel file with all sheets
        print(f"📖 Reading Excel file: {excel_file}")
        excel_file_obj = pd.ExcelFile(excel_file)
        
        print(f"📋 Excel sheets found: {excel_file_obj.sheet_names}")
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM programs")
        print("🗑️ Cleared existing database data")
        
        # Process each sheet
        imported_count = 0
        for sheet_name in excel_file_obj.sheet_names:
            print(f"📊 Processing sheet: {sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(f"   📈 Rows in {sheet_name}: {len(df)}")
            print(f"   📋 Columns in {sheet_name}: {list(df.columns)}")
            
            # Process each row in this sheet
            for index, row in df.iterrows():
                try:
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
                    program_status = "Cancelled" if actions.strip().upper() == 'TRUE' else "Active"
                    
                    class_cancellation = safe_str(row.get('Cancellation Date', row.get('cancellation_date', '')))
                    note = safe_str(row.get('Note', row.get('note', '')))
                    withdrawal = ""  # Will be calculated later
                    
                    # Insert into database
                    cursor.execute('''
                        INSERT INTO programs (sheet, program, program_id, date_range, time, location, 
                                           class_room, instructor, program_status, class_cancellation, note, withdrawal)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (sheet_name, program, program_id, date_range, time, location, 
                          class_room, instructor, program_status, class_cancellation, note, withdrawal))
                    
                    imported_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing row {index}: {e}")
                    continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully imported {imported_count} records to database")
        return True
        
    except Exception as e:
        print(f"❌ Error importing Excel data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Excel to SQLite import...")
    success = import_excel_to_sqlite()
    
    if success:
        print("🎉 Import completed successfully!")
        print("📋 Next steps:")
        print("1. Test the API: http://localhost:8000/api/test")
        print("2. Check data count in the response")
        print("3. Test frontend connection")
    else:
        print("❌ Import failed. Check the error messages above.")
