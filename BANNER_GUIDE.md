# Event Banner Guide

## Current Status
- Events now have appropriate placeholder banners based on event types
- Banners are categorized by content (music, tech, legal, food, dance, education, health, art, social)
- All banners are accessible and display properly in floating boxes

## Banner Categories
- **Music**: Sound Escapes events, concerts, tributes
- **Tech**: Wearable tech, digital workshops, online events
- **Legal**: Legal advice, lawyer appointments
- **Food**: Fresh food markets, lunches, tea events
- **Dance**: Dance parties, movement events
- **Education**: Workshops, learning events, planning sessions
- **Health**: Medical clinics, health services
- **Art**: Artisan fairs, creative workshops, art events
- **Social**: Mixers, social events, community gatherings

## To Add Real Seniors Kingston Banners
1. Visit https://seniorskingston.ca/events
2. Right-click on each event banner and "Copy image address"
3. Update the banner_mapping in get_seniors_banners_manual.py
4. Run the script to update all events

## Current Banner URLs
All banners are currently using Unsplash images that are:
- High quality (600x200 pixels)
- Appropriate for each event type
- Accessible and fast-loading
- Professional looking

## Testing
Run `python test_banner_display.py` to verify banners are working correctly.
