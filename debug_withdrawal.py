import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the withdrawal function
from backend_sqlite import calculate_withdrawal

def debug_withdrawal():
    """Debug the withdrawal calculation step by step"""
    
    print("🔍 Debugging Withdrawal Calculation")
    print("=" * 50)
    
    # Test with your actual Excel data
    test_cases = [
        ("Wed 03/09/2025 - Fri 14/11/2025", ""),
        ("Mon 08/09/2025 - Mon 10/11/2025", ""),
        ("Wed 03/09/2025 - Wed 12/11/2025", ""),
    ]
    
    for i, (date_range, class_cancellation) in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"   Date Range: '{date_range}'")
        print(f"   Cancellations: '{class_cancellation}'")
        print("-" * 40)
        
        try:
            result = calculate_withdrawal(date_range, class_cancellation)
            print(f"   ✅ Result: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_withdrawal()

