# FILES TO UPLOAD TO RENDER - Complete List

## 🚨 CRITICAL: Files That Must Be Uploaded to Render

### **FRONTEND FILES (Upload to Render Frontend):**
1. `frontend/src/AdminPanel.tsx` - **UPDATED** (added Quick Fix button)
2. `frontend/public/render_persistent_master.json` - **NEW** (persistent backup for admin panel)

### **BACKEND FILES (Upload to Render Backend):**
1. `backend_sqlite.py` - **MAY NEED UPDATE** (if we modified the backend logic)

### **BACKUP FILES (Keep Local - Don't Upload to Render):**
- `bulletproof_events_backup.json` - Keep local
- `render_persistent_master.json` - Keep local  
- `SIMPLE_FIX.py` - Keep local
- `EMERGENCY_FIX.py` - Keep local
- All other backup files - Keep local

## 📋 **STEP-BY-STEP UPLOAD INSTRUCTIONS:**

### **Step 1: Upload Frontend Files**
1. Go to your Render frontend dashboard
2. Upload these files:
   - `frontend/src/AdminPanel.tsx`
   - `frontend/public/render_persistent_master.json`

### **Step 2: Check Backend**
1. Go to your Render backend dashboard
2. Check if `backend_sqlite.py` needs updating
3. If backend was modified, upload it

### **Step 3: Deploy**
1. Deploy both frontend and backend
2. Test the Quick Fix button in admin panel

## ⚠️ **IMPORTANT NOTES:**

- **Backup files stay local** - Don't upload them to Render
- **Scripts stay local** - Don't upload Python scripts to Render
- **Only upload the actual app files** that Render needs to run

## 🎯 **WHAT EACH FILE DOES:**

- `AdminPanel.tsx` - Adds Quick Fix button to admin panel
- `render_persistent_master.json` - Provides backup data for Quick Fix button
- `backend_sqlite.py` - Backend logic (if modified)

## 📞 **AFTER UPLOADING:**

1. Test your app
2. Go to admin panel
3. Click "🚨 Quick Fix Events" button
4. Verify it restores 45 events
5. Check that banners are showing correctly

**These are the ONLY files you need to upload to Render!**
