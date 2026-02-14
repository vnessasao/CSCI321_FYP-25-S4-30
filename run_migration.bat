@echo off
echo ========================================
echo Traffic Bottleneck Analysis - Database Migration
echo ========================================
echo.

cd backend

echo Step 1: Running migration 005 (Upload Sessions)...
python migrations\005_create_upload_sessions.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Migration completed successfully!
    echo.
    echo Next steps:
    echo 1. Start backend: cd backend ^&^& python app.py
    echo 2. Start frontend: npm run dev
    echo 3. Navigate to "Upload & Analyze" in the government menu
    echo 4. Upload sample files from sample_data folder:
    echo    - sample_roads.geojson
    echo    - sample_gps.csv
    echo.
) else (
    echo.
    echo ❌ Migration failed! Please check the error above.
    echo.
    echo Common fixes:
    echo - Ensure PostgreSQL is running
    echo - Check backend/.env has correct database credentials
    echo - Run: psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
    echo - Run: psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    echo.
)

cd ..
pause
