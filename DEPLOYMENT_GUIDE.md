# 🚀 Deployment Guide: Making Your Class Cancellation App Available Online

## **Option 1: Deploy to Render (Backend) + Vercel (Frontend) - RECOMMENDED**

### **Step 1: Deploy Backend to Render**

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Sign in with your GitHub account

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure the Service:**
   - **Name:** `class-cancellation-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

4. **Set Environment Variables:**
   - Click "Environment" tab
   - Add variable: `EXCEL_PATH` = `./Class Cancellation App.xlsx`

5. **Upload Excel File:**
   - In the "Files" section, upload your Excel file
   - Make sure it's named exactly: `Class Cancellation App.xlsx`

6. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Copy your service URL (e.g., `https://your-app-name.onrender.com`)

### **Step 2: Deploy Frontend to Vercel**

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

3. **Create environment file:**
   ```bash
   echo REACT_APP_API_URL=https://your-backend-url.onrender.com/api > .env.local
   ```
   (Replace `your-backend-url` with your actual Render backend URL)

4. **Deploy to Vercel:**
   ```bash
   vercel
   ```

### **Step 3: Configure Environment Variables**

**In Render Dashboard:**
- `PORT`: 8000 (automatic)
- `EXCEL_PATH`: `./Class Cancellation App.xlsx`

**In Vercel Dashboard:**
- `REACT_APP_API_URL`: Your Render backend URL

## **Option 2: Deploy Both to Render**

### **Step 1: Deploy Backend**
Follow the Render instructions above.

### **Step 2: Deploy Frontend to Render**

1. **Create New Static Site:**
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Select your repository

2. **Configure the Service:**
   - **Name:** `class-cancellation-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/build`
   - **Plan:** Free

3. **Set Environment Variables:**
   - Add variable: `REACT_APP_API_URL` = `https://your-backend-url.onrender.com/api`

## **Option 3: Deploy to Heroku**

### **Step 1: Prepare for Heroku**

1. **Install Heroku CLI:**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku:**
   ```bash
   heroku login
   ```

### **Step 2: Deploy Backend**

1. **Create Heroku app:**
   ```bash
   heroku create your-app-name-backend
   ```

2. **Add Python buildpack:**
   ```bash
   heroku buildpacks:set heroku/python
   ```

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy backend"
   git push heroku main
   ```

### **Step 3: Deploy Frontend**

1. **Create another Heroku app:**
   ```bash
   heroku create your-app-name-frontend
   ```

2. **Add Node.js buildpack:**
   ```bash
   heroku buildpacks:set heroku/nodejs
   ```

3. **Set environment variable:**
   ```bash
   heroku config:set REACT_APP_API_URL=https://your-backend-url.herokuapp.com/api
   ```

4. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy frontend"
   git push heroku main
   ```

## **Option 4: Deploy to DigitalOcean App Platform**

### **Step 1: Prepare Repository**

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git push -u origin main
   ```

### **Step 2: Deploy on DigitalOcean**

1. **Go to DigitalOcean App Platform**
2. **Create new app from GitHub repository**
3. **Configure build settings:**
   - Backend: Python app
   - Frontend: Static site (React)

## **Important Notes:**

### **Excel File Handling**
Since your app reads from an Excel file, you have several options:

1. **Upload to Render (Recommended):**
   - Upload Excel file directly to Render dashboard
   - Set `EXCEL_PATH` to `./Class Cancellation App.xlsx`

2. **Use cloud storage:**
   - Upload Excel file to Google Drive, Dropbox, or AWS S3
   - Update `EXCEL_PATH` in backend to use the cloud URL

3. **Use database instead:**
   - Convert Excel data to SQLite or PostgreSQL
   - Update backend to read from database

### **Environment Variables to Set:**

**Backend (Render):**
- `PORT`: 8000 (automatic)
- `EXCEL_PATH`: Path to your Excel file
- `CORS_ORIGINS`: Your frontend URL

**Frontend (Vercel):**
- `REACT_APP_API_URL`: Your backend API URL

### **Security Considerations:**

1. **Add authentication** if needed
2. **Use HTTPS** (automatic with most platforms)
3. **Set up proper CORS** origins
4. **Add rate limiting** for API endpoints

### **Monitoring and Maintenance:**

1. **Set up logging** to monitor app performance
2. **Configure alerts** for downtime
3. **Set up automatic backups** of your data
4. **Monitor API usage** and costs

## **Quick Start (Recommended):**

1. **Deploy backend to Render**
2. **Deploy frontend to Vercel**
3. **Upload Excel file to Render**
4. **Share the frontend URL with users**

This will give you a fully functional online app that others can access!