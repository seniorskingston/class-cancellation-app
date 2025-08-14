# 🌐 Deploy Your Class Cancellation App to the Public

## 🎯 **Quick Overview**
This guide will help you deploy your app so anyone on the internet can access it. We'll use:
- **Render** (for backend) - Free hosting
- **Vercel** (for frontend) - Free hosting

## 📋 **Prerequisites**
Before starting, make sure you have:
1. **GitHub account** - [github.com](https://github.com)
2. **Your app code** uploaded to GitHub
3. **Excel file** (`Class Cancellation App.xlsx`) ready

---

## 🚀 **Step 1: Prepare Your Code for GitHub**

### 1.1 Create a GitHub Repository
1. Go to [github.com](https://github.com)
2. Click "New repository"
3. Name it: `class-cancellation-app`
4. Make it **Public** (for free hosting)
5. Click "Create repository"

### 1.2 Upload Your Code
1. **Open Command Prompt/PowerShell** in your project folder
2. **Initialize Git and upload:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/class-cancellation-app.git
   git push -u origin main
   ```
   (Replace `YOUR_USERNAME` with your actual GitHub username)

---

## 🔧 **Step 2: Deploy Backend to Render**

### 2.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started"
3. Sign in with your **GitHub account**

### 2.2 Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Click **"Connect"** next to your GitHub repository
3. Select your `class-cancellation-app` repository

### 2.3 Configure Backend Settings
Fill in these details:

**Basic Settings:**
- **Name:** `class-cancellation-backend`
- **Environment:** `Python 3`
- **Region:** Choose closest to your users
- **Branch:** `main`
- **Root Directory:** Leave empty (use root)

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **"Free"** plan

### 2.4 Set Environment Variables
1. Click **"Environment"** tab
2. Add these variables:
   - **Key:** `EXCEL_PATH`
   - **Value:** `./Class Cancellation App.xlsx`

### 2.5 Upload Excel File
1. Click **"Files"** tab
2. Click **"Upload Files"**
3. Upload your `Class Cancellation App.xlsx` file
4. Make sure it's named exactly: `Class Cancellation App.xlsx`

### 2.6 Deploy Backend
1. Click **"Create Web Service"**
2. Wait for deployment (usually 2-5 minutes)
3. **Copy your backend URL** (e.g., `https://class-cancellation-backend.onrender.com`)

---

## 🎨 **Step 3: Deploy Frontend to Vercel**

### 3.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Click **"Continue with GitHub"**
3. Authorize Vercel to access your GitHub

### 3.2 Import Project
1. Click **"New Project"**
2. Find and select your `class-cancellation-app` repository
3. Click **"Import"**

### 3.3 Configure Frontend Settings
Fill in these details:

**Project Settings:**
- **Framework Preset:** `Create React App`
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `build`
- **Install Command:** `npm install`

### 3.4 Set Environment Variables
1. Click **"Environment Variables"**
2. Add this variable:
   - **Name:** `REACT_APP_API_URL`
   - **Value:** `https://YOUR_BACKEND_URL.onrender.com/api`
   - **Environment:** Production, Preview, Development
   
   (Replace `YOUR_BACKEND_URL` with your actual Render backend URL)

### 3.5 Deploy Frontend
1. Click **"Deploy"**
2. Wait for deployment (usually 1-3 minutes)
3. **Copy your frontend URL** (e.g., `https://class-cancellation-app.vercel.app`)

---

## ✅ **Step 4: Test Your Deployed App**

### 4.1 Test Backend
1. Visit your backend URL + `/docs`
   - Example: `https://class-cancellation-backend.onrender.com/docs`
2. You should see the FastAPI documentation page

### 4.2 Test Frontend
1. Visit your frontend URL
   - Example: `https://class-cancellation-app.vercel.app`
2. Your app should load and work normally

### 4.3 Test API Connection
1. In your frontend app, try searching for classes
2. If it works, your backend and frontend are connected properly

---

## 🔄 **Step 5: Update Your Excel File**

### 5.1 Automatic Updates
- **Render:** Upload new Excel file through the dashboard
- **Vercel:** Push code changes to GitHub (automatic deployment)

### 5.2 Manual Process
1. **Update Excel file** on your computer
2. **Upload to Render:**
   - Go to your Render dashboard
   - Click on your backend service
   - Go to "Files" tab
   - Upload the new Excel file
3. **Redeploy backend** (usually automatic)

---

## 🌍 **Step 6: Share Your App**

### 6.1 Share the Frontend URL
- Share: `https://your-app-name.vercel.app`
- Anyone with this link can access your app

### 6.2 Custom Domain (Optional)
1. **In Vercel:** Go to your project → Settings → Domains
2. **Add your domain** (if you have one)
3. **Configure DNS** as instructed

---

## 🔧 **Troubleshooting**

### Common Issues:

**Backend not working:**
- Check Render logs for errors
- Verify Excel file is uploaded correctly
- Check environment variables

**Frontend not connecting to backend:**
- Verify `REACT_APP_API_URL` is correct
- Check if backend URL is accessible
- Look for CORS errors in browser console

**App not loading:**
- Check Vercel deployment logs
- Verify all environment variables are set
- Make sure GitHub repository is public

### Getting Help:
- **Render Support:** [render.com/docs](https://render.com/docs)
- **Vercel Support:** [vercel.com/docs](https://vercel.com/docs)
- **Check deployment logs** in both platforms

---

## 💰 **Costs**
- **Render:** Free tier (750 hours/month)
- **Vercel:** Free tier (unlimited)
- **Total cost:** $0/month

---

## 🎉 **You're Done!**
Your Class Cancellation App is now live on the internet! Anyone can access it using your frontend URL.

**Your app URLs:**
- **Frontend:** `https://your-app-name.vercel.app`
- **Backend:** `https://your-backend-name.onrender.com`
- **API Docs:** `https://your-backend-name.onrender.com/docs`

**Next steps:**
1. Test everything works
2. Share the frontend URL with your users
3. Update the Excel file as needed through Render dashboard 