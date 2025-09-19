#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend import scrape_seniors_kingston_events

if __name__ == "__main__":
    print("🧪 Testing Selenium scraping...")
    scrape_seniors_kingston_events()
