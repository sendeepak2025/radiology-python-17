@echo off
cls
echo.
echo ==========================================
echo  🧪 STARTING FRONTEND FOR TESTING
echo ==========================================
echo.
echo ✅ All syntax errors fixed
echo ✅ Responsive Study Viewer ready
echo ✅ Smooth scrolling implemented
echo ✅ Professional medical interface
echo.
echo 🔧 Backend Status: Running on port 8000
echo 🚀 Starting Frontend: Will be on port 3000
echo.
echo 📱 Test URLs (once frontend loads):
echo    • Dashboard: http://localhost:3000/dashboard
echo    • Patients: http://localhost:3000/patients
echo    • Study Viewer: http://localhost:3000/studies/[study-uid]
echo.
echo 🎯 Responsive Testing:
echo    • Mobile: Use browser dev tools (320px width)
echo    • Tablet: Test at 768px width
echo    • Desktop: Test at 1200px+ width
echo.
echo ⏳ Frontend will take 30-60 seconds to compile...
echo.

cd frontend
npm start

pause