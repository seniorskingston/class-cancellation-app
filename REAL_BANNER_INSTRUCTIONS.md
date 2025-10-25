# How to Get Real Seniors Kingston Event Banners

## The Problem
The current banners are random photos, not the actual event banners from the Seniors Kingston website.

## The Solution
You need to manually get the real banner URLs from the website.

## Step-by-Step Instructions

### Step 1: Visit the Website
1. Go to https://seniorskingston.ca/events
2. Wait for the page to fully load
3. You should see event boxes with banners at the top

### Step 2: Get Banner URLs
For each event:
1. Right-click on the event banner image
2. Select "Copy image address" or "Copy image URL"
3. Note the event title

### Step 3: Update the System
1. Open the file `real_banner_mapping.json`
2. Replace the placeholder URLs with the real banner URLs
3. Save the file

### Step 4: Apply the Real Banners
Run: `python apply_real_banners.py`

## Example Format
```json
{
  "Sound Escapes: Kenny & Dolly": "https://seniorskingston.ca/images/kenny-dolly-banner.jpg",
  "Wearable Tech": "https://seniorskingston.ca/images/tech-banner.jpg",
  "Legal Advice": "https://seniorskingston.ca/images/legal-banner.jpg"
}
```

## Current Events That Need Real Banners:
1. Sound Escapes: Kenny & Dolly
2. Wearable Tech
3. Legal Advice
4. Fresh Food Market
5. 18th Century Astronomy
6. Caroles Dance Party
7. Daylight Savings Ends  November 2, 8:00 am
8. Online Registration Begins
9. Assistive Listening Solutions
10. In-Person Registration for Session 2 Begins
11. Fresh Food Market
12. Fraud Awareness
13. Cut. Fold. Glue. Stars.
14. Learn about Tarot
15. Hearing Clinic
16. Coffee with a Cop
17. Cut. Fold. Glue. Trees
18. Shopping & Buying Online
19. Legal Advice
20. Fresh Food Market
21. Service Canada Clinic
22. Coast to Coast: A Canoe Odyssey
23. Birthday Lunch
24. Sound Escapes: Georgette Fry
25. Program Break Week
26. Speed Friending
27. Advanced Care Planning
28. Fresh Food Market
29. Expressive Mark Making
30. Cafe Franglish
31. Tuesday at Tom’s
32. Learn Resilience
33. Vision Workshop
34. New Member Mixer
35. Time for Tea
36. Book & Puzzle EXCHANGE
37. Annual General Meeting
38. December Vista Available for Pickup
39. Holiday Artisan Fair
40. Simplify Your Digital Life
41. Legal Advice
42. Fresh Food Market
43. Holiday Lunch
44. Domino Theatre Dress Rehearsal: Miss Bennet: Christmas at Pemberley
45. Anxiety Unlocked
