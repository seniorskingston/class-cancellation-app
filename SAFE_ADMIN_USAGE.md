# SAFE ADMIN PANEL USAGE

## 🚨 CRITICAL: How to Use Admin Panel Safely

### ✅ SAFE ACTIONS:
1. **View Events**: Always safe
2. **Edit Events**: Safe (changes saved locally)
3. **Quick Fix Button**: Safe (restores 45 events)

### ⚠️ RISKY ACTIONS:
1. **Excel Upload**: Can cause data loss
2. **Sync with Website**: Can cause data loss
3. **Load New Events**: Can cause data loss

### 🛡️ BEFORE ANY RISKY ACTION:
1. Run: `python SIMPLE_FIX.py` (ensures 45 events)
2. Make your changes
3. Run: `python SIMPLE_FIX.py` (restore if needed)

### 🚨 IF DATA GETS LOST:
1. Run: `python SIMPLE_FIX.py`
2. Check your app
3. If still wrong, run: `python EMERGENCY_FIX.py`

### 📋 SAFE WORKFLOW:
1. Always start with 45 events
2. Make changes through admin panel
3. Use Quick Fix button if events drop
4. Never upload Excel files directly

## ⚠️ IMPORTANT:
- Excel uploads can cause data loss
- Always verify you have 45 events before making changes
- Use Quick Fix button frequently
- Keep backup scripts ready
