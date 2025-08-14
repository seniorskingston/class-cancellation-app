# Deployment Script for Class Cancellation App
# Run this script to prepare your app for deployment

Write-Host "🚀 Preparing Class Cancellation App for Deployment..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "backend.py")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Install Vercel CLI if not already installed
Write-Host "📦 Installing Vercel CLI..." -ForegroundColor Yellow
try {
    npm install -g vercel
    Write-Host "✅ Vercel CLI installed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Vercel CLI installation failed. You may need to install it manually." -ForegroundColor Yellow
}

# Create .env file for frontend
Write-Host "📝 Creating environment files..." -ForegroundColor Yellow
$envContent = @"
# Frontend Environment Variables
# Update this URL after deploying your backend to Render
REACT_APP_API_URL=https://your-backend-url.onrender.com/api
"@

$envContent | Out-File -FilePath "frontend\.env.local" -Encoding UTF8
Write-Host "✅ Created frontend\.env.local" -ForegroundColor Green

# Instructions
Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://dashboard.render.com" -ForegroundColor White
Write-Host "2. Create new Web Service for backend" -ForegroundColor White
Write-Host "3. Upload Excel file to Render" -ForegroundColor White
Write-Host "4. Get your backend URL from Render" -ForegroundColor White
Write-Host "5. Update frontend\.env.local with your backend URL" -ForegroundColor White
Write-Host "6. Deploy frontend: cd frontend && vercel" -ForegroundColor White
Write-Host "`n📖 See DEPLOYMENT_GUIDE.md for detailed instructions" -ForegroundColor Cyan

Write-Host "`n🎉 Setup complete! Your app is ready for deployment." -ForegroundColor Green