# Quick Start Guide - Traffic Bottleneck Analysis

## Prerequisites Check

```bash
# 1. Check PostgreSQL
psql --version
# Should show: psql (PostgreSQL) 12.x or higher

# 2. Check Python
python --version
# Should show: Python 3.8 or higher

# 3. Check Node.js
node --version
# Should show: v16.x or higher
```

## 5-Minute Setup

### 1. Enable PostgreSQL Extensions

```bash
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### 2. Run Database Migration

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

### 3. Start Backend

```bash
cd backend
python app.py
```

Wait for: `✅ Database connection verified` and `Running on http://0.0.0.0:5000`

### 4. Start Frontend

**New terminal:**
```bash
npm run dev
```

Open: `http://localhost:5173`

---

## Using the System

### Step-by-Step Workflow

1. **Login** as government user
2. **Navigate** to "Upload & Analyze" in sidebar
3. **Upload Files**:
   - Road Network: `sample_data/sample_roads.geojson`
   - GPS Trajectories: `sample_data/sample_gps.csv`
4. **Preprocess** - Click "Preprocess Data" button
5. **Wait** - Status changes: Pending → Preprocessing → Ready (~10-30 seconds)
6. **Run Model** - Adjust K (default: 10), Time Horizon (default: 30 min)
7. **View Results** - Auto-redirects to Bottlenecks page

### What You'll See

**Map Visualization:**
- 🔴 Red circles = Critical bottlenecks (worst)
- 🟠 Orange circles = Major bottlenecks
- 🟡 Yellow circles = Moderate bottlenecks
- 🟢 Green circles = Minor bottlenecks

**Bottleneck Table:**
- Rankings with benefit scores
- Roads affected by each bottleneck
- Click "Show on Map" to center on specific road

**What-If Analysis:**
- Select bottlenecks using checkboxes
- Click "What-If Analysis" button
- See impact of fixing selected roads

---

## Sample Data Included

### `sample_data/sample_roads.geojson`
- 15 roads in Singapore (Orchard Road area)
- Valid GeoJSON format with LineString geometries
- Properties: road_id, road_name, highway type

### `sample_data/sample_gps.csv`
- 30 vehicles (V001-V030)
- Time period: 08:00-08:44 (44 minutes)
- Includes congestion patterns:
  - Fast traffic: 40-55 km/h
  - Moderate: 15-30 km/h
  - Jammed: 0.1-5 km/h

---

## Troubleshooting Quick Fixes

### Backend won't start
```bash
pip install -r backend/requirements.txt
```

### Migration fails
```bash
# Check database connection
psql -U postgres -d traffic_analysis -c "SELECT version();"

# Enable extensions
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION postgis;"
psql -U postgres -d traffic_analysis -c "CREATE EXTENSION \"uuid-ossp\";"
```

### Frontend won't start
```bash
npm install
npm run dev
```

### Preprocessing stuck
- Check backend terminal for errors
- Verify file formats match requirements
- Ensure PostGIS is enabled

### Map shows no bottlenecks
- F12 → Console to check for JavaScript errors
- Verify files uploaded successfully
- Check backend logs for calculation errors

---

## API Endpoints (for testing)

```bash
# Health check
curl http://localhost:5000/health

# Create session
curl -X POST http://localhost:5000/api/upload/create-session

# Get session status
curl http://localhost:5000/api/upload/session-status/{session_id}

# Get bottlenecks
curl http://localhost:5000/api/bottlenecks/top-k?k=10&time_horizon=30&model_type=LIM
```

---

## File Format Requirements

### Road Network (GeoJSON)
```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "road_id": "unique_id",
      "road_name": "Road Name",
      "highway": "primary|secondary|tertiary"
    },
    "geometry": {
      "type": "LineString",
      "coordinates": [[lon1, lat1], [lon2, lat2]]
    }
  }]
}
```

### GPS Trajectories (CSV)
```csv
vehicle_id,timestamp,latitude,longitude,speed,heading
V001,2025-01-15T08:00:00Z,1.3048,103.8281,45.5,90
```

**Required columns:**
- `vehicle_id`: Any unique identifier
- `timestamp`: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- `latitude`: Decimal degrees
- `longitude`: Decimal degrees
- `speed`: km/h
- `heading`: Degrees (0-360)

---

## Performance Tips

### For Large Datasets

1. **Reduce simulation count** (faster but less accurate):
   - Edit `backend/services/influence_models.py`
   - Line ~200: Change `num_simulations=100` to `num_simulations=50`

2. **Sample GPS data**:
   - Use fewer vehicles or time periods
   - Keep density high enough to detect congestion

3. **Optimize database**:
```sql
-- Add helpful indexes
CREATE INDEX idx_gps_timestamp ON gps_trajectories(timestamp);
CREATE INDEX idx_gps_vehicle ON gps_trajectories(vehicle_id);
```

---

## Next Steps

After testing with sample data:

1. **Use Real Data**:
   - Export road network from OpenStreetMap
   - Collect GPS trajectories from fleet tracking
   - Ensure Singapore coordinates (lat: 1.2-1.5, lon: 103.6-104.0)

2. **Customize Visualization**:
   - Edit color gradient in `src/pages/gov/Bottlenecks.jsx`
   - Change map tiles (OpenStreetMap, CartoDB, etc.)
   - Adjust circle sizes

3. **Tune Model Parameters**:
   - Experiment with different time horizons (5, 15, 30 min)
   - Adjust K (number of bottlenecks)
   - Try different simulation counts

4. **Export Results**:
   - Add CSV/PDF export functionality
   - Integrate with reporting systems
   - Schedule automated analysis

---

## Support

📖 Full documentation: [BOTTLENECK_ANALYSIS_GUIDE.md](BOTTLENECK_ANALYSIS_GUIDE.md)

🚀 **You're ready to go!** Run the migration and start the servers.
