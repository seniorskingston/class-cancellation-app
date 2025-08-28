import os
import sys
import pytz
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the withdrawal function
from backend_sqlite import calculate_withdrawal

# Set timezone
KINGSTON_TZ = pytz.timezone('America/Toronto')

def test_withdrawal_calculation():
    """Test the withdrawal calculation with different date formats"""
    
    print("🧪 Testing Withdrawal Calculation Logic")
    print("=" * 50)
    
    # Test cases - including the user's actual Excel format
    test_cases = [
        # (date_range, class_cancellation, expected_result)
        ("Wed 03/09/2025 - Fri 14/11/2025", "", "Should calculate based on start date (Wed 03/09/2025) - Wed & Fri classes"),
        ("Tue 05/09/2025 - Thu 14/11/2025", "", "Should calculate based on start date (Tue 05/09/2025) - Tue & Thu classes"),
        ("Mon 02/09/2025 - Wed 13/11/2025", "", "Should calculate based on start date (Mon 02/09/2025) - Mon & Wed classes"),
        ("Mon 01/09/2025 - Fri 15/11/2025", "", "Should calculate based on start date (Mon 01/09/2025) - Mon through Fri classes"),
        ("Wed 03/09/2025 - Fri 14/11/2025", "Oct 3, 2025; Oct 10, 2025", "Should account for 2 cancelled classes"),
        ("Sep 9 - Dec 16, 2025", "", "Should calculate based on start date (fallback format)"),
        ("September 9 - December 16, 2025", "", "Should calculate based on start date (fallback format)"),
        ("2025-09-09 - 2025-12-16", "", "Should calculate based on start date (ISO format)"),
        ("09/09/2025 - 12/16/2025", "", "Should calculate based on start date (MM/DD/YYYY format)"),
        ("", "", "Should return Unknown (no date)"),
        ("Invalid Date Format", "", "Should return Unknown (can't parse)"),
    ]
    
    for i, (date_range, class_cancellation, description) in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {description}")
        print(f"   Date Range: '{date_range}'")
        print(f"   Cancellations: '{class_cancellation}'")
        print("-" * 40)
        
        try:
            result = calculate_withdrawal(date_range, class_cancellation)
            print(f"   ✅ Result: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("📅 Current Date (Kingston):", datetime.now(KINGSTON_TZ).date())
    print("🕐 Current Time (Kingston):", datetime.now(KINGSTON_TZ).strftime("%H:%M:%S"))

if __name__ == "__main__":
    test_withdrawal_calculation()
