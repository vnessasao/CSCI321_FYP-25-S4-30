# Traffic Bottleneck Analysis System Guide

## Table of Contents

1. [Project Overview](#project-overview)
2. [Getting Started](#getting-started)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Complete Installation & Configuration](#complete-installation--configuration)
5. [Running the Application](#running-the-application)
6. [Using the System](#using-the-system)
7. [User Roles & Features](#user-roles--features)
8. [Implementation Status](#implementation-status)
9. [Workflow & Architecture](#workflow--architecture)
10. [API Documentation](#api-documentation)
11. [Sample Data Files](#sample-data-files)
12. [Troubleshooting](#troubleshooting)
13. [Performance & Optimization](#performance--optimization)
14. [Technical Stack](#technical-stack)

---

## Project Overview

### Flow Radar - Traffic Analytics & Monitoring Platform

A comprehensive React-based frontend and Flask-based backend application for traffic analytics, bottleneck analysis, and monitoring with multiple user roles.

**Key Highlights:**
- 🚦 Real-time traffic congestion monitoring
- 📊 Advanced bottleneck analysis using LIM model
- 🗺️ Interactive map visualization with color-coded severity levels
- 📈 Historical trend analysis and predictions
- 👥 Role-based access control (4 user types)
- 🔧 Session-based data management for isolated analysis
- 📱 Responsive design with Tailwind CSS

### System Architecture

```
Frontend (React 18 + Vite)
    ↓
API Gateway (Flask)
    ↓
PostgreSQL + PostGIS (Spatial Database)
    ↓
Processing Services (LIM Model, Preprocessing, Analysis)
```

---

## Getting Started

### Prerequisites Check

Verify you have the required tools installed:

```bash
# Check PostgreSQL (required: 12+)
psql --version
# Expected: psql (PostgreSQL) 12.x or higher

# Check Python (required: 3.8+)
python --version
# Expected: Python 3.8 or higher

# Check Node.js (required: 16+)
node --version
# Expected: v16.x or higher

# Check npm
npm --version
# Expected: npm 7+
```

### System Requirements

**Backend**
- Python 3.8+
- PostgreSQL 12+ with PostGIS extension
- Minimum 2GB RAM for processing large datasets

**Frontend**
- Node.js 16+
- npm or yarn
- Modern browser (Chrome, Firefox, Safari, Edge)

---

## Quick Start (5 Minutes)

### Step 1: Enable PostgreSQL Extensions

```bash
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### Step 2: Run Database Migration

**Windows:**
```bash
run_migration.bat
```

**Linux/Mac:**
```bash
chmod +x run_migration.sh
./run_migration.sh
```

**Or manually:**
```bash
cd backend
python migrations/005_create_upload_sessions.py
```

### Step 3: Start Backend

```bash
cd backend
python app.py
```

**Expected output:**
```
 Database connection verified
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### Step 4: Start Frontend

**In a new terminal:**
```bash
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Step 5: Access the Application

1. Open browser: `http://localhost:5173`
2. Login with:
   - **Email:** `admin@trafficsg.gov`
   - **Password:** `SuperAdmin@2024`
   - **Role:** Government
3. Navigate to **"Upload & Analyze"** in the sidebar
4. Upload sample files and run analysis!

### What You'll See

**Upload & Analyze Page:**
- File upload section for Road Network (GeoJSON)
- File upload section for GPS Trajectories (CSV)
- Preprocess button with real-time status updates
- Model run controls with parameter sliders

**Bottlenecks Page:**
- Interactive Leaflet map with color-coded markers
- 🔴 Red = Critical bottlenecks
- 🟠 Orange = Major bottlenecks
- 🟡 Yellow = Moderate bottlenecks
- 🟢 Green = Minor bottlenecks
- Rankings table with benefit scores
- What-if analysis interface

---

## Complete Installation & Configuration

### Step 1: Database Setup

**Verify PostgreSQL is running:**
```bash
psql -U postgres -c "SELECT version();"
```

**Create database:**
```bash
createdb -U postgres traffic_analysis
```

**Enable required extensions:**
```bash
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Verify
psql -U postgres -d traffic_analysis -c "SELECT PostGIS_version();"
```

### Step 2: Backend Setup

**Navigate to backend:**
```bash
cd backend
```

**Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Configure environment variables:**

Create `backend/.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=traffic_analysis
DB_USER=postgres
DB_PASSWORD=your_password_here
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

**Run database migrations (in order):**
```bash
cd backend/migrations

# Previous migrations (if not already done)
python 001_initial_schema.py
python 002_add_incidents_table.py
python 003_add_users_table.py
python 004_create_traffic_analysis_tables.py

# New upload sessions migration
python 005_create_upload_sessions.py
```

**Verify database setup:**
```bash
psql -U postgres -d traffic_analysis -c "\dt"
# Should show all tables including upload_sessions
```

### Step 3: Frontend Setup

**Navigate to project root:**
```bash
cd ../..
```

**Install Node dependencies:**
```bash
npm install
```

**Verify installation:**
```bash
npm list react react-router-dom leaflet
```

---

## Running the Application

### Method 1: Start Both Services (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

Wait for: `✅ Database connection verified` and `Running on http://0.0.0.0:5000`

**Terminal 2 - Frontend:**
```bash
npm run dev
```

Wait for: `Ready in xxx ms`

**Access:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5000`

### Method 2: Development Mode with Hot Reload

```bash
# Backend (with auto-reload)
cd backend
FLASK_ENV=development python -m flask run --reload

# Frontend (Vite has built-in hot reload)
npm run dev
```

### Method 3: Production Build

```bash
# Build frontend
npm run build
# Output: dist/ folder

# Build backend
cd backend
python -m pip install -r requirements.txt
# Then run with production server
```

---

## Using the System

### Complete Workflow: Step-by-Step

#### Step 1: Login

1. Go to `http://localhost:5173`
2. Click "Login" button
3. Select role: **Government**
4. Enter credentials:
   - Email: `admin@trafficsg.gov`
   - Password: `SuperAdmin@2024`
5. Click "Sign In"

#### Step 2: Navigate to Upload & Analyze

1. From dashboard, click **"Upload & Analyze"** in sidebar
2. Or navigate directly to `/gov/data-upload`

#### Step 3: Upload Files

1. Click **"Select File"** button for Road Network
2. Choose: `sample_data/sample_roads.geojson`
3. Click **"Select File"** button for GPS Trajectories
4. Choose: `sample_data/sample_gps.csv`
5. Click **"Upload Files"** button
6. Wait for upload confirmation (shows file details)

#### Step 4: Preprocess Data

1. Click **"Preprocess Data"** button
2. Watch status bar:
   - `⏳ Pending` → `🔄 Preprocessing` → `✅ Ready`
3. Status updates every 2 seconds automatically
4. When complete, see summary:
   ```
   Roads loaded: 15
   GPS points processed: 900
   Processing time: 12.5 seconds
   ```

#### Step 5: Configure & Run Model

1. Once status is **Ready**, adjust parameters:
   - **K (Bottlenecks):** Slider 5-20 (default: 10)
   - **Time Horizon:** Dropdown 5/15/30 minutes (default: 30)
   
2. Click **"Run Model"** button

3. System processes:
   - Learns influence probabilities
   - Runs LIM Monte Carlo simulations (100 runs)
   - Greedy algorithm for top-K selection
   - Caches results

4. Auto-redirects to **Bottlenecks** page

#### Step 6: View & Analyze Results

**Map View:**
- See Singapore map with 10 bottleneck markers
- Red to green gradient = Critical to Minor
- Circle size = Benefit score (larger = higher impact)
- Hover for road name, click for details

**Rankings Table:**
- Rank, Road Name, Benefit Score, Affected Roads
- Color-coded rows (red → green)
- Each row is clickable

**Navigation:**
- "Show on Map" button centers on specific road
- Scroll through all ranked bottlenecks
- Zoom/pan map with mouse

#### Step 7: What-If Analysis (Optional)

1. **Select bottlenecks** using checkboxes in table
2. Example: Select top 3 bottlenecks
3. Click **"What-If Analysis (3 selected)"** button
4. See comparison:
   - **Baseline:** 87 jams (current state)
   - **If Fixed:** 23 jams (after fixes)
   - **Reduction:** 73% improvement

---

## User Roles & Features

### 1. Public User

**Access Level:** Public information only

**Features:**
- Live Congestion Map (`/public/map`)
  - Real-time traffic status
  - Color-coded congestion levels
- Route Traffic Status (`/public/route-status`)
  - Check specific route conditions
  - Travel time estimates
- Daily Top Hotspots (`/public/hotspots`)
  - Most congested areas today
  - Hourly trends
- Report Incident (`/public/report-incident`)
  - Report traffic accidents/hazards
  - Incident tracking
- Feedback (`/public/feedback`)
  - Submit feedback and suggestions

**Example Login:**
- Email: Any email
- Password: Any password
- Select "Continue as Guest" option

### 2. Government User

**Access Level:** Full analysis and planning capabilities

**Features:**
- Congestion Heatmap (`/gov/heatmap`)
  - Time-based heatmaps
  - Identify peak hours
- Input Roadwork Event (`/gov/roadwork`)
  - Plan infrastructure projects
  - Track roadwork progress
- EMAS Incident Status (`/gov/emas`)
  - Emergency incident monitoring
  - Response coordination
- Critical Alerts (`/gov/alerts`)
  - System-wide alerts
  - Priority incidents
- Time-based Reports (`/gov/reports`)
  - Generate custom reports
  - Data exports
- Event Simulation (`/gov/simulation`)
  - Test scenarios
  - Impact analysis
- Weather Overlay (`/gov/weather`)
  - Real-time weather data
  - Rainfall, temperature monitoring
- Public Transport Overlay (`/gov/transport`)
  - MRT/Bus stop locations
  - Transit alerts
- Manage User Accounts (`/gov/manage-users`)
  - Create/edit/suspend users
  - Role management
- **Upload & Analyze (`/gov/data-upload`)**
  - Upload road networks
  - GPS trajectory analysis
  - Bottleneck detection
- **Bottlenecks (`/gov/bottlenecks`)**
  - View analysis results
  - What-if analysis

**Credentials:**
```
Email: admin@trafficsg.gov
Password: SuperAdmin@2024
Role: Government
```

### 3. Traffic Analyst User

**Access Level:** Data analysis and modeling

**Features:**
- Data Preprocessing (`/analyst/preprocess`)
  - Clean and prepare data
  - Format validation
- Run Traffic Flow Model (`/analyst/run-model`)
  - Execute LIM/LTM/SIR/SIS models
  - Parameter tuning
- View Historical Trends (`/analyst/trends`)
  - Time series analysis
  - Seasonal patterns
- Schedule Automated Runs (`/analyst/schedule`)
  - Cron-based scheduling
  - Automated reports
- Monitor Anomalies (`/analyst/anomalies`)
  - Detect unusual patterns
  - Alert on anomalies

### 4. System Developer (Admin)

**Access Level:** System administration and development

**Features:**
- Algorithm Modules (`/dev/algorithms`)
  - Manage algorithms (LIM, LTM, SIR, SIS, GREEDY)
  - Enable/disable algorithms
- System Performance (`/dev/performance`)
  - Monitor server metrics
  - Database performance
- Access Roles (`/dev/access-roles`)
  - Permission management
  - Role configuration
- Feedback Management (`/dev/feedback`)
  - User feedback tracking
  - Response management
- Maintenance & Logs (`/dev/logs`)
  - System logs viewer
  - Error tracking
- Visualization Modules (`/dev/visualization`)
  - Map customization
  - Chart configuration
- Backup & Restore (`/dev/backup`)
  - Database backups
  - Data recovery
- API Integrations (`/dev/integrations`)
  - External API management
  - TomTom, data.gov.sg configuration
- Deployments (`/dev/deployments`)
  - Version management
  - Rollout tracking

---

## Implementation Status

**Backend APIs:**
- `backend/routes/trends.py` - Historical trends analysis
- `backend/routes/users.py` - User management (CRUD)
- `backend/routes/algorithms.py` - Algorithm management
- `backend/routes/traffic.py` - Live traffic data with region filtering

**Frontend Components:**
- `src/pages/analyst/Trends.jsx` - Historical trends visualization
- `src/pages/gov/ManageUsers.jsx` - User management interface
- `src/pages/dev/Algorithms.jsx` - Algorithm configuration
- `src/pages/publicPages/TrafficMap.jsx` - Live traffic map

**Database Tables:**
- `algorithms` - Algorithm registry (LIM, LTM, SIR, SIS, GREEDY)
- `permissions` - System permissions
- `role_permissions` - Role-permission mapping
- `model_schedules` - Scheduled model runs
- `system_logs` - System logging
- `detected_anomalies` - Anomaly detection
- `feedback` - User feedback
- `backups` - Backup history

**APIs:**
- `backend/routes/weather.py` - Weather data from data.gov.sg
- `backend/routes/transport.py` - MRT/Bus data from LTA DataMall
- `backend/routes/schedules.py` - APScheduler integration
- `backend/routes/anomalies.py` - Z-score based detection
- `backend/routes/logs.py` - System logging and monitoring
- `backend/routes/permissions.py` - Permission management
- `backend/routes/feedback.py` - Feedback broadcast system
- `backend/routes/backups.py` - Database backup/restore


**Backend (11 files):**
1. `backend/migrations/005_create_upload_sessions.py` - Session table
2. `backend/routes/data_upload.py` - Upload endpoints
3. `backend/routes/bottlenecks.py` - Bottleneck analysis
4. `backend/services/preprocessing_service.py` - Data preprocessing
5. `backend/services/influence_models.py` - LIM model implementation
6. `backend/services/bottleneck_finder.py` - Greedy algorithm
7. `backend/app.py` - Blueprint registration

**Frontend (5 files):**
8. `src/pages/gov/DataUpload.jsx` - Upload workflow
9. `src/pages/gov/Bottlenecks.jsx` - Results visualization
10. `src/api/apiService.js` - API methods (11 new)
11. `src/router/AppRouter.jsx` - Route configuration
12. `src/layouts/DashboardLayout.jsx` - Menu integration


---

## Workflow & Architecture

### Complete User Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER WORKFLOW                            │
└─────────────────────────────────────────────────────────────┘

Step 1: Upload Files
   ├─ Road Network (GeoJSON) → Saved to sessions/{id}/roads.geojson
   └─ GPS Trajectories (CSV) → Saved to sessions/{id}/gps_trajectories.csv
                ↓
Step 2: Preprocess Data (Manual trigger)
   ├─ Load roads → road_nodes table (with PostGIS geometry)
   ├─ Build graph → road_edges table (spatial proximity)
   ├─ Process GPS → gps_trajectories table (with map matching)
   └─ Calculate congestion → congestion_states table
                ↓
Step 3: Run Model (LIM with parameters K, time_horizon)
   ├─ Learn influence probabilities (Monte Carlo, 100 sims)
   ├─ Get current jammed roads (from congestion_states)
   ├─ Simulate jam spread (probabilistic)
   ├─ Greedy algorithm for top-K bottlenecks
   └─ Cache results → bottleneck_rankings table
                ↓
Step 4: View Results
   ├─ Interactive map with color-coded markers
   ├─ Rankings table with benefit scores
   └─ What-if analysis for scenario testing
```

### Data Flow Architecture

```
Frontend (React)
    ↓
API Service (Axios/Fetch)
    ↓
Flask Backend (REST API)
    ↓
┌─────────────────────────────────────────────┐
│          Core Processing Services            │
├─────────────────────────────────────────────┤
│ • preprocessing_service.py (GeoJSON loader) │
│ • influence_models.py (LIM Monte Carlo)     │
│ • bottleneck_finder.py (Greedy algorithm)   │
└─────────────────────────────────────────────┘
    ↓
PostgreSQL + PostGIS
    ├─ road_nodes (spatial)
    ├─ road_edges (connections)
    ├─ gps_trajectories (trajectories)
    ├─ congestion_states (calculated)
    └─ bottleneck_rankings (results)
```

### Session Management

```
Each Upload Creates:
├─ Unique UUID (session_id)
├─ Directory: sessions/{session_id}/
│  ├─ roads.geojson
│  ├─ gps_trajectories.csv
│  └─ metadata.json
├─ Database entries:
│  ├─ upload_sessions row
│  ├─ road_nodes (with session_id FK)
│  ├─ gps_trajectories (with session_id FK)
│  ├─ road_edges (with session_id FK)
│  ├─ congestion_states (with session_id FK)
│  └─ bottleneck_rankings (with session_id FK)
└─ Status tracking:
   ├─ pending
   ├─ preprocessing (in progress)
   ├─ ready (completed)
   └─ failed (error occurred)
```

---

## API Documentation

### Upload & Session Management

**Create Upload Session**
```
POST /api/upload/create-session
Response: { session_id: "uuid" }
```

**Upload Road Network**
```
POST /api/upload/road-network
Body: FormData with file (GeoJSON)
Response: { status: "success", roads_loaded: 15 }
```

**Upload GPS Trajectories**
```
POST /api/upload/gps-trajectories
Body: FormData with file (CSV)
Response: { status: "success", points_loaded: 900 }
```

**Start Preprocessing**
```
POST /api/upload/preprocess
Body: { session_id: "uuid" }
Response: { status: "preprocessing" }
```

**Get Session Status**
```
GET /api/upload/session-status/:sessionId
Response: {
  status: "ready" | "preprocessing" | "pending" | "failed",
  road_count: 15,
  gps_point_count: 900,
  preprocessing_time: "12.5s",
  error_message: null
}
```

### Bottleneck Analysis

**Run Bottleneck Model**
```
POST /api/bottlenecks/run-model
Body: {
  session_id: "uuid",
  k: 10,
  time_horizon: 30,
  model_type: "LIM"
}
Response: { status: "success", bottlenecks_found: 10 }
```

**Get Top K Bottlenecks**
```
GET /api/bottlenecks/top-k?k=10&time_horizon=30
Response: [
  {
    rank: 1,
    road_id: "orchard_rd_001",
    road_name: "Orchard Road",
    benefit_score: 45.7,
    affected_roads: 5,
    coordinates: [[lon, lat], [lon, lat]]
  },
  ...
]
```

**What-If Analysis**
```
POST /api/bottlenecks/what-if
Body: {
  session_id: "uuid",
  bottleneck_ids: ["orchard_rd_001", "scotts_rd_001"]
}
Response: {
  baseline_jams: 87,
  fixed_jams: 23,
  reduction_percentage: 73
}
```

---

## Sample Data Files

### Sample 1: Road Network (GeoJSON)

**File:** `sample_data/sample_roads.geojson`

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "road_id": "orchard_rd_001",
        "road_name": "Orchard Road",
        "highway": "primary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8281, 1.3048],
          [103.8320, 1.3055],
          [103.8360, 1.3062]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "scotts_rd_001",
        "road_name": "Scotts Road",
        "highway": "secondary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8320, 1.3055],
          [103.8310, 1.3080],
          [103.8305, 1.3100]
        ]
      }
    }
  ]
}
```

**Format Requirements:**
- Must be valid GeoJSON
- Features must be LineString geometries
- Must include: `road_id`, `road_name`, `highway`
- Coordinates: [longitude, latitude]
- Ensure Singapore coordinates

### Sample 2: GPS Trajectories (CSV)

**File:** `sample_data/sample_gps.csv`

```csv
vehicle_id,timestamp,latitude,longitude,speed,heading
V001,2025-01-15T08:00:00Z,1.3048,103.8281,45.5,90
V001,2025-01-15T08:01:00Z,1.3050,103.8290,42.3,88
V001,2025-01-15T08:02:00Z,1.3052,103.8300,40.1,87
V002,2025-01-15T08:00:00Z,1.3055,103.8320,5.2,180
V002,2025-01-15T08:01:00Z,1.3056,103.8330,3.8,175
V002,2025-01-15T08:02:00Z,1.3057,103.8340,2.1,170
```

**Format Requirements:**
- CSV with headers
- Required columns: `vehicle_id`, `timestamp`, `latitude`, `longitude`, `speed`, `heading`
- Timestamp: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD HH:MM:SS)
- Latitude/Longitude: Decimal degrees
- Speed: km/h
- Heading: Degrees 0-360

**Data Characteristics (Sample):**
- 30 vehicles (V001-V030)
- Time period: 44 minutes (08:00-08:44)
- Congestion patterns:
  - Fast traffic: 40-55 km/h (free flow)
  - Moderate traffic: 15-30 km/h (congested)
  - Jammed traffic: 0.1-5 km/h (severely congested)

---

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'flask'`
```bash
# Solution: Install dependencies
pip install -r backend/requirements.txt

# Verify flask is installed
python -c "import flask; print(flask.__version__)"
```

**Problem:** `psycopg3.OperationalError: could not connect to the database`
```bash
# Solution 1: Check connection details
psql -U postgres -d traffic_analysis -c "SELECT version();"

# Solution 2: Update .env file with correct credentials
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<your_actual_password>

# Solution 3: Verify PostgreSQL is running
# Windows: Check Services
# Linux/Mac: brew services list postgres
```

**Problem:** `ERROR: PostGIS extension not found`
```bash
# Solution: Create and enable extensions
psql -U postgres -d traffic_analysis

-- Inside psql:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify
SELECT PostGIS_version();
\dx  -- List extensions
```

**Problem:** `ERROR: Relation "upload_sessions" does not exist`
```bash
# Solution: Run migration
cd backend/migrations
python 005_create_upload_sessions.py

# Verify
psql -U postgres -d traffic_analysis -c "\dt upload_sessions;"
```

**Problem:** Backend stops with `Port 5000 already in use`
```bash
# Solution: Kill existing process
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :5000
kill -9 <PID>

# Or use different port:
python app.py --port 5001
```

### Frontend Issues

**Problem:** `npm ERR! command not found: vite`
```bash
# Solution: Reinstall dependencies
npm install

# Clear cache
npm cache clean --force

# Reinstall
npm install
```

**Problem:** Module not found errors
```bash
# Solution 1: Clean install
rm -rf node_modules package-lock.json
npm install

# Solution 2: Clear cache
npm cache clean --force
npm install
```

**Problem:** Map not loading on Bottlenecks page
```bash
# Solution 1: Check backend is running
curl http://localhost:5000/health

# Solution 2: Check console errors
# Open F12 → Console tab
# Check for JavaScript errors

# Solution 3: Verify Leaflet CSS is imported
# File: src/pages/gov/Bottlenecks.jsx
// Should have: import 'leaflet/dist/leaflet.css'

# Solution 4: Clear browser cache
# Ctrl+Shift+Delete → Clear cache
```

**Problem:** CORS errors when calling backend
```bash
# Solution 1: Verify backend is running on :5000
curl http://localhost:5000

# Solution 2: Check API endpoint in code
# src/api/apiService.js
// Should have: const BASE_URL = 'http://localhost:5000'

# Solution 3: Restart both servers
# Backend: python app.py
# Frontend: npm run dev
```

### Data Processing Issues

**Problem:** Preprocessing status stuck at "Preprocessing"
```bash
# Solution 1: Check backend logs
# Terminal where backend is running - look for errors

# Solution 2: Verify file formats
# GeoJSON: Use online JSON validator
# CSV: Open in text editor, check headers

# Solution 3: Check database
psql -U postgres -d traffic_analysis -c "SELECT * FROM upload_sessions;"

# Solution 4: Restart backend and try again
```

**Problem:** Validation error during upload
```bash
# Solution 1: Check GeoJSON structure
# Must be FeatureCollection with LineString features
# Use: https://geojsonlint.com/

# Solution 2: Check CSV headers
# Required: vehicle_id,timestamp,latitude,longitude,speed,heading
# Recommended: Use CSV validator online

# Solution 3: Check coordinates
# Should be Singapore: lat 1.2-1.5, lon 103.6-104.0
```

**Problem:** Zero bottlenecks found after model run
```bash
# Solution 1: Ensure GPS has congestion
# CSV should have mix of fast and slow speeds
# Too uniform speeds won't show bottlenecks

# Solution 2: Check data was loaded
psql -U postgres -d traffic_analysis -c "SELECT COUNT(*) FROM gps_trajectories;"

# Solution 3: Reduce K (number of bottlenecks)
# Try K=5 instead of K=10

# Solution 4: Increase time horizon
# Try 30 minutes instead of 5 minutes
```

**Problem:** Preprocessing takes too long
```bash
# Solution 1: Optimize GPS data
# Reduce number of vehicles or time period
# Keep density: at least 1 point per road segment

# Solution 2: Check database indexes
psql -U postgres -d traffic_analysis -c "\di"

# Solution 3: Increase RAM
# Stop other applications
# Monitor: top (Linux) or Task Manager (Windows)

# Solution 4: Process smaller batches
# Split large datasets into sessions
```

**Problem:** Model run completes but no results
```bash
# Solution 1: Check Monte Carlo ran
# Edit backend/services/influence_models.py
# Verify: num_simulations = 100

# Solution 2: Check influence probabilities
psql -U postgres -d traffic_analysis -c \
  "SELECT COUNT(*) FROM influence_probabilities WHERE session_id='<session_id>';"

# Solution 3: Verify congestion states exist
psql -U postgres -d traffic_analysis -c \
  "SELECT COUNT(*) FROM congestion_states WHERE session_id='<session_id>';"

# Solution 4: Reduce time_horizon
# Try 5 minutes instead of 30
```

---

## Performance & Optimization

### For Large Datasets

**1. Reduce Simulation Count (Faster but less accurate)**
```python
# File: backend/services/influence_models.py
# Line ~200:
num_simulations = 50  # Changed from 100
```

**2. Sample GPS Data**
```bash
# Use fewer vehicles or shorter time period
# Example: 100 vehicles for 1 hour instead of 1000 for 8 hours
# Keep density high enough to detect congestion
```

**3. Optimize Database**
```sql
-- Add helpful indexes
CREATE INDEX idx_gps_timestamp ON gps_trajectories(timestamp);
CREATE INDEX idx_gps_vehicle ON gps_trajectories(vehicle_id);
CREATE INDEX idx_road_session ON road_nodes(session_id);
CREATE INDEX idx_congestion_session ON congestion_states(session_id);

-- Verify indexes
\di
```

**4. Process Data in Sessions**
```
Upload smaller datasets at a time
Example: 50 vehicles at a time instead of 500
Allows analysis of specific time periods
```

**5. Monitor Performance**
```bash
# Backend performance
# Terminal: python app.py
# Watch: CPU usage, memory, response times

# Database performance
psql -U postgres -d traffic_analysis -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Frontend performance
# Browser F12 → Performance tab
```

### Database Optimization

```sql
-- Analyze table statistics
ANALYZE upload_sessions;
ANALYZE gps_trajectories;
ANALYZE congestion_states;

-- Vacuum for maintenance
VACUUM ANALYZE upload_sessions;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Technical Stack

### Frontend
- **Framework:** React 18 with Vite
- **Router:** React Router v6
- **Styling:** Tailwind CSS
- **Maps:** Leaflet with react-leaflet
- **Charts:** Recharts
- **Icons:** React Icons
- **State:** React Hooks (useState, useEffect, useContext)
- **HTTP:** Fetch API

### Backend
- **Framework:** Flask with Blueprint architecture
- **Database:** PostgreSQL 12+ with PostGIS
- **ORM:** Direct SQL with psycopg3
- **Spatial:** PostGIS (ST_Distance, ST_GeomFromText, etc.)
- **Scheduling:** APScheduler
- **Task Queue:** Celery (optional)

### Data Processing
- **Languages:** Python 3.8+
- **Libraries:** NumPy, Pandas, Scipy
- **Spatial:** PostGIS, Shapely (optional)
- **Models:** LIM, LTM, SIR, SIS, GREEDY

### Infrastructure
- **Server:** Flask development server (production: Gunicorn/uWSGI)
- **Frontend Build:** Vite
- **Version Control:** Git
- **Deployment:** Docker-ready (optional)

---

## Key Features Summary

 **Core Analytics**
- Real-time traffic monitoring
- Historical trend analysis
- Traffic prediction models

 **Bottleneck Analysis**
- LIM model with Monte Carlo simulation
- Greedy algorithm for top-K identification
- What-if scenario analysis

 **Data Management**
- GeoJSON road network import
- CSV GPS trajectory import
- Session-based data isolation
- Preprocessing pipeline

 **Visualization**
- Interactive Leaflet maps
- Color-gradient severity levels
- Real-time status updates
- Heatmaps and trend charts

 **User Management**
- 4 user roles with different permissions
- Role-based dashboards
- User account management
- Permission control

 **System Features**
- Automated scheduling
- Anomaly detection
- System logging and monitoring
- Backup and restore
- Weather and transport overlays
- Feedback management

 **Performance**
- Database caching (1-hour TTL)
- Spatial indexing
- Session-based processing
- Optimized algorithms

---
