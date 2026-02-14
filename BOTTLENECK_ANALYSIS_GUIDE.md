# Traffic Jam Prediction & Bottleneck Analysis - User Guide

## Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation & Setup](#installation--setup)
4. [Running the Application](#running-the-application)
5. [Using the System](#using-the-system)
6. [Sample Data Files](#sample-data-files)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This system implements traffic jam prediction and bottleneck analysis using:
- **LIM Model** (Linear Independent Cascade) - Monte Carlo simulation for jam spread prediction
- **Greedy Algorithm** - Identifies top-K traffic bottlenecks
- **Session-based Data Management** - Isolated analysis for each upload
- **Interactive Visualization** - Color-gradient map showing bottleneck severity

### Key Features
✅ Upload road network (GeoJSON) and GPS trajectories (CSV)
✅ Manual preprocessing with real-time status updates
✅ Bottleneck identification with benefit scores
✅ Color-coded map visualization (Red → Yellow → Green)
✅ What-if analysis for testing fixes

---

## System Requirements

### Backend
- Python 3.8+
- PostgreSQL 12+ with PostGIS extension
- Required Python packages (see `backend/requirements.txt`)

### Frontend
- Node.js 16+
- npm or yarn

### Database
- PostgreSQL with PostGIS enabled
- Minimum 2GB RAM for processing large datasets

---

## Installation & Setup

### Step 1: Database Setup

1. **Ensure PostgreSQL with PostGIS is installed**:
```bash
# Check PostgreSQL version
psql --version

# Check if PostGIS is available
psql -U postgres -c "SELECT PostGIS_version();"
```

2. **Create database** (if not exists):
```bash
createdb -U postgres traffic_analysis
```

3. **Enable PostGIS extension**:
```bash
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS uuid-ossp;"
```

### Step 2: Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment** (optional but recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:

Edit `backend/.env` file (already exists):
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=traffic_analysis
DB_USER=postgres
DB_PASSWORD=your_password_here
SECRET_KEY=your_secret_key_here
```

5. **Run database migrations**:

```bash
# Run previous migrations first (if not already done)
python migrations/001_initial_schema.py
python migrations/002_add_incidents_table.py
python migrations/003_add_users_table.py
python migrations/004_create_traffic_analysis_tables.py

# Run the new upload sessions migration
python migrations/005_create_upload_sessions.py
```

You should see:
```
Running migration 005: Create upload_sessions table...
✅ Created upload_sessions table
✅ Created indexes on upload_sessions table
✅ Added session_id column to road_nodes table
✅ Added session_id column to gps_trajectories table
✅ Added session_id column to congestion_states table
✅ Added session_id column to bottleneck_rankings table
✅ Added session_id column to influence_probabilities table
✅ Added session_id column to road_edges table
Migration 005 completed successfully
```

### Step 3: Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd ..  # Go back to root
npm install
```

2. **Ensure Leaflet CSS is available**:

The frontend uses `react-leaflet` for maps. Dependencies are already in `package.json`.

If you need to install manually:
```bash
npm install leaflet react-leaflet
```

---

## Running the Application

### Start Backend Server

```bash
cd backend
python app.py
```

You should see:
```
✅ Database connection verified
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### Start Frontend Server

In a **new terminal**:

```bash
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Access the Application

1. Open browser: `http://localhost:5173`
2. Login with government role credentials
3. Navigate to **"Upload & Analyze"** in the sidebar

---

## Using the System

### Complete Workflow

#### Step 1: Upload Files

1. Go to **Government Dashboard** → **Upload & Analyze**
2. Click **"Select File"** for Road Network (GeoJSON)
3. Click **"Select File"** for GPS Trajectories (CSV)
4. Click **"Upload Files"** button

Wait for upload confirmation.

#### Step 2: Preprocess Data

1. Once files are uploaded, the **"Preprocess Data"** button becomes enabled
2. Click **"Preprocess Data"**
3. Watch the status change: `Pending` → `Preprocessing` → `Ready`
4. Status polling happens automatically every 2 seconds
5. When complete, you'll see a summary:
   - Roads loaded: X
   - GPS points processed: Y
   - Processing time: Z seconds

#### Step 3: Run Bottleneck Analysis

1. Once status is `Ready`, configure parameters:
   - **K (Number of Bottlenecks)**: Slider from 5-20 (default: 10)
   - **Time Horizon**: Dropdown - 5, 15, or 30 minutes (default: 30)

2. Click **"Run Model"** button

3. System will:
   - Learn influence probabilities (first time only)
   - Run LIM model simulations
   - Calculate top-K bottlenecks using greedy algorithm
   - Redirect to Bottlenecks page automatically

#### Step 4: View Results

On the **Bottlenecks** page, you'll see:

**Map View:**
- Color-coded circular markers on Singapore map
- **Red circles** = Critical bottlenecks (Rank 1-3)
- **Orange circles** = Major bottlenecks (Rank 4-5)
- **Yellow circles** = Moderate bottlenecks (Rank 6-7)
- **Green circles** = Minor bottlenecks (Rank 8-10)
- Circle size proportional to benefit score
- Click markers for details popup

**Legend (Top-right corner):**
- Shows color gradient and severity levels
- Note: Circle size indicates benefit score

**Bottleneck Rankings Table:**
- Rank, Road Name, Benefit Score, Affected Roads Count
- Color-coded row backgrounds
- Checkbox for selecting roads for what-if analysis
- "Show on Map" button centers map on that bottleneck

#### Step 5: What-If Analysis (Optional)

1. Select bottlenecks using checkboxes in the table
2. Click **"What-If Analysis (N selected)"** button
3. View results showing:
   - Baseline jam count vs. Fixed jam count
   - Expected reduction in traffic jams

---

## Sample Data Files

### Sample 1: Road Network GeoJSON

Create a file named `sample_roads.geojson`:

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
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "somerset_rd_001",
        "road_name": "Somerset Road",
        "highway": "secondary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8360, 1.3062],
          [103.8380, 1.3070],
          [103.8400, 1.3075]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "tanglin_rd_001",
        "road_name": "Tanglin Road",
        "highway": "primary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8240, 1.3040],
          [103.8260, 1.3044],
          [103.8281, 1.3048]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "paterson_rd_001",
        "road_name": "Paterson Road",
        "highway": "tertiary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8305, 1.3100],
          [103.8315, 1.3120],
          [103.8325, 1.3140]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "penang_rd_001",
        "road_name": "Penang Road",
        "highway": "secondary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8400, 1.3075],
          [103.8420, 1.3080],
          [103.8440, 1.3082]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "cairnhill_rd_001",
        "road_name": "Cairnhill Road",
        "highway": "tertiary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8325, 1.3140],
          [103.8340, 1.3150],
          [103.8355, 1.3155]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "newton_rd_001",
        "road_name": "Newton Road",
        "highway": "secondary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8355, 1.3155],
          [103.8370, 1.3165],
          [103.8385, 1.3172]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "bukit_timah_rd_001",
        "road_name": "Bukit Timah Road",
        "highway": "primary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8200, 1.3200],
          [103.8220, 1.3210],
          [103.8240, 1.3220]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "road_id": "stevens_rd_001",
        "road_name": "Stevens Road",
        "highway": "secondary"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [103.8260, 1.3180],
          [103.8280, 1.3185],
          [103.8300, 1.3188]
        ]
      }
    }
  ]
}
```

### Sample 2: GPS Trajectories CSV

Create a file named `sample_gps.csv`:

```csv
vehicle_id,timestamp,latitude,longitude,speed,heading
V001,2025-01-15T08:00:00Z,1.3048,103.8281,45.5,90
V001,2025-01-15T08:01:00Z,1.3055,103.8320,42.0,90
V001,2025-01-15T08:02:00Z,1.3062,103.8360,38.5,90
V002,2025-01-15T08:00:00Z,1.3040,103.8240,50.0,85
V002,2025-01-15T08:01:00Z,1.3044,103.8260,48.0,85
V002,2025-01-15T08:02:00Z,1.3048,103.8281,45.0,85
V003,2025-01-15T08:00:00Z,1.3055,103.8320,15.0,180
V003,2025-01-15T08:01:00Z,1.3080,103.8310,12.5,180
V003,2025-01-15T08:02:00Z,1.3100,103.8305,10.0,180
V004,2025-01-15T08:00:00Z,1.3062,103.8360,55.0,90
V004,2025-01-15T08:01:00Z,1.3070,103.8380,52.0,90
V004,2025-01-15T08:02:00Z,1.3075,103.8400,50.0,90
V005,2025-01-15T08:03:00Z,1.3048,103.8281,20.0,90
V005,2025-01-15T08:04:00Z,1.3055,103.8320,18.5,90
V005,2025-01-15T08:05:00Z,1.3062,103.8360,15.0,90
V006,2025-01-15T08:03:00Z,1.3100,103.8305,8.0,0
V006,2025-01-15T08:04:00Z,1.3120,103.8315,7.5,0
V006,2025-01-15T08:05:00Z,1.3140,103.8325,6.0,0
V007,2025-01-15T08:06:00Z,1.3048,103.8281,10.0,90
V007,2025-01-15T08:07:00Z,1.3055,103.8320,8.5,90
V007,2025-01-15T08:08:00Z,1.3062,103.8360,5.0,90
V008,2025-01-15T08:06:00Z,1.3140,103.8325,45.0,45
V008,2025-01-15T08:07:00Z,1.3150,103.8340,43.0,45
V008,2025-01-15T08:08:00Z,1.3155,103.8355,40.0,45
V009,2025-01-15T08:09:00Z,1.3048,103.8281,5.0,90
V009,2025-01-15T08:10:00Z,1.3055,103.8320,4.5,90
V009,2025-01-15T08:11:00Z,1.3062,103.8360,3.0,90
V010,2025-01-15T08:09:00Z,1.3155,103.8355,50.0,45
V010,2025-01-15T08:10:00Z,1.3165,103.8370,48.0,45
V010,2025-01-15T08:11:00Z,1.3172,103.8385,45.0,45
V011,2025-01-15T08:12:00Z,1.3200,103.8200,35.0,90
V011,2025-01-15T08:13:00Z,1.3210,103.8220,32.0,90
V011,2025-01-15T08:14:00Z,1.3220,103.8240,30.0,90
V012,2025-01-15T08:12:00Z,1.3180,103.8260,40.0,90
V012,2025-01-15T08:13:00Z,1.3185,103.8280,38.0,90
V012,2025-01-15T08:14:00Z,1.3188,103.8300,35.0,90
V013,2025-01-15T08:15:00Z,1.3048,103.8281,2.0,90
V013,2025-01-15T08:16:00Z,1.3055,103.8320,1.5,90
V013,2025-01-15T08:17:00Z,1.3062,103.8360,1.0,90
V014,2025-01-15T08:15:00Z,1.3075,103.8400,45.0,90
V014,2025-01-15T08:16:00Z,1.3080,103.8420,42.0,90
V014,2025-01-15T08:17:00Z,1.3082,103.8440,40.0,90
V015,2025-01-15T08:18:00Z,1.3048,103.8281,0.5,90
V015,2025-01-15T08:19:00Z,1.3055,103.8320,0.5,90
V015,2025-01-15T08:20:00Z,1.3062,103.8360,0.5,90
```

### Important Notes About Sample Data:

1. **Road Network Requirements**:
   - Must be valid GeoJSON with FeatureCollection
   - Each feature needs:
     - `road_id`: Unique identifier
     - `road_name`: Human-readable name
     - `highway`: Road type (primary, secondary, tertiary, etc.)
     - `geometry`: LineString with at least 2 coordinate pairs
   - Coordinates format: `[longitude, latitude]` (note: lon first!)

2. **GPS Trajectories Requirements**:
   - CSV with headers: `vehicle_id`, `timestamp`, `latitude`, `longitude`, `speed`, `heading`
   - Timestamp format: ISO 8601 (e.g., `2025-01-15T08:00:00Z`)
   - Speed in km/h
   - Heading in degrees (0-360)
   - Multiple readings per vehicle to show movement patterns

3. **Data Patterns for Testing**:
   - Sample includes vehicles with varying speeds:
     - V003, V006: Slow speeds (6-15 km/h) → Creates jams
     - V005, V007, V009: Medium-slow (5-20 km/h) → Congestion
     - V013, V015: Very slow (0.5-2 km/h) → Severe jams
   - Multiple vehicles on same roads → Creates congestion states
   - Time-series data → Enables influence learning

---

## Troubleshooting

### Issue: Migration fails with "uuid-ossp extension not found"

**Solution**:
```bash
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### Issue: Backend error "No module named 'psycopg'"

**Solution**:
```bash
pip install psycopg[binary]
# or
pip install psycopg3
```

### Issue: Frontend can't find Leaflet CSS

**Solution**:
```bash
npm install leaflet react-leaflet
```

Make sure `import 'leaflet/dist/leaflet.css'` is in Bottlenecks.jsx (already added).

### Issue: Preprocessing status stuck on "Preprocessing"

**Check backend logs** for errors. Common issues:
- Invalid GeoJSON format
- CSV missing required columns
- PostGIS functions not available

**Fix**:
```bash
# Check backend terminal for errors
# Ensure PostGIS is enabled:
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Issue: Map doesn't show bottlenecks

**Possible causes**:
1. No coordinates in database (check road geometry)
2. Invalid coordinate format
3. Bottlenecks calculation returned empty

**Debug**:
- Check browser console for JavaScript errors
- Verify API response in Network tab
- Check that roads have valid geometries:
```sql
SELECT road_id, road_name, ST_AsText(geometry)
FROM road_nodes
WHERE session_id = 'your-session-id';
```

### Issue: "Session not found" error

**Solution**:
- Upload files creates a new session automatically
- Make sure you click "Upload Files" first
- Check that both files uploaded successfully

### Issue: Very slow preprocessing

**Optimization tips**:
- Reduce GPS trajectory file size (use sampling)
- Use fewer road segments initially
- Increase database resources
- Consider adding indexes:
```sql
CREATE INDEX IF NOT EXISTS idx_gps_timestamp ON gps_trajectories(timestamp);
CREATE INDEX IF NOT EXISTS idx_gps_vehicle ON gps_trajectories(vehicle_id);
```

---

## Advanced Configuration

### Adjust Model Parameters

Edit `backend/services/influence_models.py`:

```python
# Line ~200: Adjust simulation count for faster/slower but more/less accurate results
num_simulations=100  # Default, try 50 for faster, 200 for more accurate
```

### Change Map Tile Provider

Edit `src/pages/gov/Bottlenecks.jsx`:

```javascript
// Line ~195: Change map tiles
url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
// Alternative providers:
// CartoDB: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
// Stamen: "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png"
```

### Customize Color Gradient

Edit `src/pages/gov/Bottlenecks.jsx`:

```javascript
// Line ~105: Modify colors array
const colors = ['#DC2626', '#EF4444', '#F97316', '#FACC15', '#84CC16']
// Change to your preferred gradient
```

---

## API Endpoints Reference

### Upload & Session Management
- `POST /api/upload/create-session` - Create new session
- `POST /api/upload/road-network` - Upload GeoJSON
- `POST /api/upload/gps-trajectories` - Upload CSV
- `POST /api/upload/preprocess` - Start preprocessing
- `GET /api/upload/session-status/:id` - Get status

### Bottleneck Analysis
- `POST /api/bottlenecks/run-model` - Run analysis
- `GET /api/bottlenecks/top-k` - Get results
- `POST /api/bottlenecks/what-if` - What-if analysis
- `POST /api/bottlenecks/learn-influence` - Learn probabilities

---

## Support & Feedback

For issues or questions:
1. Check logs in backend terminal
2. Check browser console (F12)
3. Review database for data integrity
4. Verify file formats match requirements

---

**Congratulations!** You're now ready to analyze traffic bottlenecks and predict jam spread using the LIM model. 🚗📊
