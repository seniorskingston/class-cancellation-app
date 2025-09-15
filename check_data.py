import sqlite3

conn = sqlite3.connect('class_cancellations.db')
cursor = conn.cursor()

# Check program 27679
cursor.execute('SELECT program, program_id, class_cancellation FROM programs WHERE program_id = ?', ('27679',))
result = cursor.fetchone()

if result:
    print(f"Program 27679: {result[0]} (ID: {result[1]})")
    print(f"Cancellation: '{result[2]}'")
    print(f"Length: {len(result[2])}")
    print(f"Characters: {[ord(c) for c in result[2]]}")
else:
    print("Program 27679 not found")

# Check all Aquafit programs
print("\nAll Aquafit programs:")
cursor.execute('SELECT program, program_id, class_cancellation FROM programs WHERE program = ?', ('Aquafit',))
aquafit_programs = cursor.fetchall()

for prog in aquafit_programs:
    print(f"ID: {prog[1]} - Cancellation: '{prog[2]}'")

conn.close()
