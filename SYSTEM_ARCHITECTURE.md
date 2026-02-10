# System Architecture - Traffic Bottleneck Analysis

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                    React Frontend (Port 5173)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  DataUpload.jsx  │  │ Bottlenecks.jsx  │  │JamPrediction.jsx│ │
│  │                  │  │                  │  │                  │ │
│  │  • File Upload   │  │  • Leaflet Map   │  │  • Predictions   │ │
│  │  • Preprocessing │  │  • Color Markers │  │  • Risk Levels   │ │
│  │  • Run Model     │  │  • Rankings      │  │  • Time Series   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────┘
                                │ HTTP/REST API
                                │ (apiService.js)
┌───────────────────────────────▼───────────────────────────────────┐
│                        BACKEND SERVER                               │
│                   Flask Application (Port 5000)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    API ROUTES (Blueprints)                      │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │                                                                  │ │
│  │  /api/upload/*                /api/bottlenecks/*                │ │
│  │  ├─ create-session            ├─ run-model                      │ │
│  │  ├─ road-network              ├─ top-k                          │ │
│  │  ├─ gps-trajectories          ├─ calculate                      │ │
│  │  ├─ preprocess                ├─ what-if                        │ │
│  │  └─ session-status/:id        └─ learn-influence                │ │
│  │                                                                  │ │
│  └──────────────────────┬─────────────────────────────────────────┘ │
│                         │                                             │
│  ┌──────────────────────▼─────────────────────────────────────────┐ │
│  │                    SERVICES LAYER                                │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │                                                                  │ │
│  │  PreprocessingService     InfluenceModels    BottleneckFinder  │ │
│  │  ├─ load_road_network     ├─ LIM Model      ├─ Greedy Algo    │ │
│  │  ├─ build_road_graph      ├─ LTM Model      ├─ Benefit Calc   │ │
│  │  ├─ process_gps_data      ├─ SIR Model      ├─ What-If        │ │
│  │  └─ calc_congestion       └─ SIS Model      └─ Coordinates     │ │
│  │                                                                  │ │
│  └──────────────────────┬─────────────────────────────────────────┘ │
│                         │                                             │
└─────────────────────────┼─────────────────────────────────────────┘
                          │ psycopg3 (PostgreSQL Driver)
┌─────────────────────────▼─────────────────────────────────────────┐
│                   DATABASE LAYER                                    │
│              PostgreSQL with PostGIS Extension                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ upload_sessions  │  │   road_nodes     │  │  road_edges      │ │
│  │                  │  │                  │  │                  │ │
│  │ • session_id     │  │ • id             │  │ • from_node_id   │ │
│  │ • status         │  │ • road_id        │  │ • to_node_id     │ │
│  │ • filenames      │  │ • road_name      │  │ • distance       │ │
│  │ • counts         │  │ • geometry       │  │ • session_id     │ │
│  │ • timestamps     │  │ • session_id     │  │                  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │gps_trajectories  │  │congestion_states │  │influence_probs   │ │
│  │                  │  │                  │  │                  │ │
│  │ • vehicle_id     │  │ • road_node_id   │  │ • from_road_id   │ │
│  │ • timestamp      │  │ • timestamp      │  │ • to_road_id     │ │
│  │ • lat/lon        │  │ • speed_kmh      │  │ • probability    │ │
│  │ • speed          │  │ • congestion_idx │  │ • time_horizon   │ │
│  │ • matched_road   │  │ • state          │  │ • model_type     │ │
│  │ • session_id     │  │ • session_id     │  │ • session_id     │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                       │
│  ┌──────────────────┐                                                │
│  │bottleneck_ranks  │                                                │
│  │                  │                                                │
│  │ • road_node_id   │                                                │
│  │ • rank_position  │                                                │
│  │ • benefit_score  │                                                │
│  │ • affected_count │                                                │
│  │ • timestamp      │                                                │
│  │ • session_id     │                                                │
│  └──────────────────┘                                                │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Upload & Preprocessing Flow

```
┌──────────┐
│  USER    │
└────┬─────┘
     │ 1. Select Files
     │    (roads.geojson, gps.csv)
     ▼
┌─────────────────────────┐
│   DataUpload.jsx        │
│                         │
│  [Upload Files Button]  │
└────┬────────────────────┘
     │ 2. POST /upload/create-session
     ▼
┌─────────────────────────┐
│  data_upload.py         │
│                         │
│  create_session()       │
└────┬────────────────────┘
     │ 3. INSERT INTO upload_sessions
     │    RETURNING session_id
     ▼
┌─────────────────────────┐
│  Database               │
│  upload_sessions table  │
└────┬────────────────────┘
     │ 4. Return session_id
     ▼
┌─────────────────────────┐
│  Frontend               │
│  Stores session_id      │
└────┬────────────────────┘
     │ 5. POST /upload/road-network
     │    (multipart/form-data)
     ▼
┌─────────────────────────┐
│  data_upload.py         │
│  upload_road_network()  │
│                         │
│  • Validate file type   │
│  • Save to sessions/    │
│  • Update DB filename   │
└────┬────────────────────┘
     │ 6. POST /upload/gps-trajectories
     ▼
┌─────────────────────────┐
│  Similar upload flow    │
└────┬────────────────────┘
     │ 7. Click "Preprocess Data"
     │    POST /upload/preprocess
     ▼
┌─────────────────────────────────────────────┐
│  preprocessing_service.py                   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ load_road_network_from_geojson()    │   │
│  │                                     │   │
│  │ • Parse GeoJSON features            │   │
│  │ • Extract properties & geometry     │   │
│  │ • Build PostGIS LINESTRING          │   │
│  │ • INSERT INTO road_nodes            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ build_road_graph()                  │   │
│  │                                     │   │
│  │ • Find adjacent roads               │   │
│  │ • ST_DWithin spatial query (50m)    │   │
│  │ • INSERT INTO road_edges            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ process_gps_trajectories()          │   │
│  │                                     │   │
│  │ • Read CSV records                  │   │
│  │ • Map match to nearest road         │   │
│  │ • INSERT INTO gps_trajectories      │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ calculate_congestion_states()       │   │
│  │                                     │   │
│  │ • Aggregate by road & time window   │   │
│  │ • Calculate speed, flow, density    │   │
│  │ • Compute congestion index          │   │
│  │ • INSERT INTO congestion_states     │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
     │ 8. Update status = 'ready'
     ▼
┌─────────────────────────┐
│  Frontend polls status  │
│  Every 2 seconds        │
│                         │
│  Shows: Pending →       │
│         Preprocessing → │
│         Ready ✓         │
└─────────────────────────┘
```

---

### Bottleneck Analysis Flow

```
┌──────────┐
│  USER    │
└────┬─────┘
     │ 1. Set K=10, Horizon=30min
     │    Click "Run Model"
     ▼
┌─────────────────────────┐
│  DataUpload.jsx         │
│  runBottleneckModel()   │
└────┬────────────────────┘
     │ 2. POST /bottlenecks/run-model
     ▼
┌─────────────────────────────────────────────┐
│  bottlenecks.py                             │
│  run_model()                                │
│                                             │
│  • Validate session status = 'ready'        │
│  • Check if influence probs exist           │
│  • If not: trigger learning                 │
└────┬────────────────────────────────────────┘
     │ 3. Learn influence probabilities
     │    (first time only)
     ▼
┌─────────────────────────────────────────────┐
│  influence_models.py                        │
│  learn_influence_probabilities()            │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ For each road edge:                 │   │
│  │                                     │   │
│  │ • Query congestion_states           │   │
│  │ • Count: jam on A → jam on B        │   │
│  │ • Calculate probability             │   │
│  │ • INSERT influence_probabilities    │   │
│  └─────────────────────────────────────┘   │
└────┬────────────────────────────────────────┘
     │ 4. Find top-K bottlenecks
     ▼
┌─────────────────────────────────────────────┐
│  bottleneck_finder.py                       │
│  find_top_k_bottlenecks()                   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Greedy Algorithm:                   │   │
│  │                                     │   │
│  │ FOR rank = 1 to K:                  │   │
│  │   FOR each candidate road:          │   │
│  │     • Call predict_spread()         │   │
│  │     • Calculate benefit score       │   │
│  │   SELECT road with max benefit      │   │
│  │   ADD to bottlenecks list           │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ For each bottleneck:                │   │
│  │                                     │   │
│  │ • Extract coordinates (centroid)    │   │
│  │ • Count affected roads              │   │
│  │ • Calculate final benefit           │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  • INSERT INTO bottleneck_rankings          │
│  • Return results with coordinates          │
└────┬────────────────────────────────────────┘
     │ 5. Return bottlenecks JSON
     ▼
┌─────────────────────────┐
│  Frontend               │
│  navigate('/bottlenecks'│
│    ?sessionId=xxx       │
│    &k=10&horizon=30)    │
└────┬────────────────────┘
     │ 6. Load Bottlenecks.jsx
     ▼
┌─────────────────────────────────────────────┐
│  Bottlenecks.jsx                            │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Map Visualization:                  │   │
│  │                                     │   │
│  │ • Leaflet MapContainer              │   │
│  │ • For each bottleneck:              │   │
│  │   - CircleMarker at coordinates     │   │
│  │   - Color by rank (gradient)        │   │
│  │   - Radius by benefit score         │   │
│  │   - Popup with details              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Rankings Table:                     │   │
│  │                                     │   │
│  │ • Rank | Road | Score | Affected    │   │
│  │ • Color-coded rows                  │   │
│  │ • Checkbox selection                │   │
│  │ • "Show on Map" buttons             │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

### LIM Model Algorithm Flow

```
┌─────────────────────────────────────────────┐
│  predict_spread() - LIM Model               │
├─────────────────────────────────────────────┤
│                                             │
│  INPUT:                                     │
│  • session_id                               │
│  • seed_roads (currently jammed)            │
│  • time_horizon (5, 15, or 30 minutes)      │
│  • num_simulations (default: 100)           │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Initialize:                         │   │
│  │ • Get all roads from database       │   │
│  │ • Get influence probabilities       │   │
│  │ • jam_counts = {road_id: 0}         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Monte Carlo Simulations:            │   │
│  │                                     │   │
│  │ FOR sim = 1 to num_simulations:     │   │
│  │                                     │   │
│  │   jammed = seed_roads (copy)        │   │
│  │   active = seed_roads (copy)        │   │
│  │                                     │   │
│  │   WHILE active is not empty:        │   │
│  │                                     │   │
│  │     new_active = []                 │   │
│  │                                     │   │
│  │     FOR each from_road in active:   │   │
│  │       FOR each to_road connected:   │   │
│  │         IF to_road not in jammed:   │   │
│  │           prob = influence[from][to]│   │
│  │           random_val = random(0,1)  │   │
│  │                                     │   │
│  │           IF random_val < prob:     │   │
│  │             jammed.add(to_road)     │   │
│  │             new_active.add(to_road) │   │
│  │                                     │   │
│  │     active = new_active             │   │
│  │                                     │   │
│  │   FOR each road in jammed:          │   │
│  │     jam_counts[road] += 1           │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Calculate Probabilities:            │   │
│  │                                     │   │
│  │ FOR each road:                      │   │
│  │   probability = jam_counts[road] /  │   │
│  │                 num_simulations     │   │
│  │                                     │   │
│  │   risk_level = HIGH (>=0.7)         │   │
│  │              | MEDIUM (0.3-0.7)     │   │
│  │              | LOW (<0.3)           │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  OUTPUT:                                    │
│  • List of roads with jam probabilities    │
│  • Sorted by probability (descending)      │
└─────────────────────────────────────────────┘
```

---

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     FRONTEND COMPONENTS                         │
└────────────────────────────────────────────────────────────────┘
                               │
                               │ React Router
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐         ┌──────────┐        ┌──────────┐
    │ DataUpload│         │Bottlenecks│        │   Jam    │
    │   .jsx   │         │   .jsx   │        │Prediction│
    └────┬─────┘         └────┬─────┘        └────┬─────┘
         │                    │                    │
         │ ApiService         │ ApiService         │ ApiService
         │                    │                    │
┌────────┴────────────────────┴────────────────────┴────────────┐
│                       apiService.js                            │
│                                                                │
│  • createUploadSession()      • runBottleneckModel()          │
│  • uploadRoadNetwork()        • getTopBottlenecks()           │
│  • uploadGpsTrajectories()    • calculateBottlenecks()        │
│  • preprocessData()           • whatIfAnalysis()              │
│  • getSessionStatus()         • learnInfluenceProbabilities() │
└────────────────────────┬───────────────────────────────────────┘
                         │ HTTP/REST
                         │ (Fetch API)
┌────────────────────────▼───────────────────────────────────────┐
│                      Flask Application                          │
│                         app.py                                  │
└─────────┬──────────────────────────────────┬──────────────────┘
          │                                  │
          │ Blueprints                       │ Blueprints
          │                                  │
          ▼                                  ▼
┌──────────────────┐              ┌──────────────────┐
│ data_upload_bp   │              │ bottlenecks_bp   │
│ (/api/upload/*)  │              │(/api/bottlenecks)│
└────┬─────────────┘              └────┬─────────────┘
     │                                  │
     │ Uses Services                    │ Uses Services
     │                                  │
     ▼                                  ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Preprocessing    │    │ InfluenceModels  │    │ BottleneckFinder │
│    Service       │◄───┤    Service       │◄───┤    Service       │
└────┬─────────────┘    └──────────────────┘    └──────────────────┘
     │
     │ DatabaseConfig
     │ (psycopg3)
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                           │
│                      with PostGIS                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Color Gradient System

```
Bottleneck Severity Visualization
──────────────────────────────────

Rank 1-2:  ███████  #DC2626  Critical (Bright Red)
           Highest benefit score
           Fix these first!

Rank 3-4:  ███████  #EF4444  Severe (Red)
           High impact
           Priority targets

Rank 5-6:  ███████  #F97316  Major (Orange)
           Significant benefit
           Important to address

Rank 7-8:  ███████  #FACC15  Moderate (Yellow)
           Medium impact
           Secondary priority

Rank 9-10: ███████  #84CC16  Minor (Yellow-Green)
           Lower benefit
           Address if resources allow

Circle Size = Benefit Score
──────────────────────────────
Larger circles = Higher benefit when fixed
Radius: 10px (min) to 30px (max)
Formula: 10 + (score/max_score) * 20
```

---

## Session Lifecycle

```
┌────────────────────────────────────────────────────────────┐
│                   SESSION LIFECYCLE                         │
└────────────────────────────────────────────────────────────┘

1. CREATE
   ├─ User clicks "Upload Files"
   ├─ POST /api/upload/create-session
   ├─ Generate UUID (uuid_generate_v4())
   ├─ Set is_active = TRUE (deactivate others)
   └─ Status: 'pending'

2. UPLOAD
   ├─ Upload road_network.geojson
   │  └─ Save to sessions/{id}/roads.geojson
   ├─ Upload gps_trajectories.csv
   │  └─ Save to sessions/{id}/gps_trajectories.csv
   └─ Update filenames in database

3. PREPROCESS
   ├─ User clicks "Preprocess Data"
   ├─ Status → 'preprocessing'
   ├─ Load roads → road_nodes (with session_id)
   ├─ Build graph → road_edges
   ├─ Process GPS → gps_trajectories
   ├─ Calculate → congestion_states
   └─ Status → 'ready' (or 'failed' on error)

4. ANALYZE
   ├─ User clicks "Run Model"
   ├─ Learn influence_probabilities (if needed)
   ├─ Run LIM model (Monte Carlo)
   ├─ Calculate bottleneck_rankings
   └─ Cache results (1 hour validity)

5. VIEW
   ├─ Display on Bottlenecks.jsx
   ├─ Interactive map with markers
   ├─ Rankings table
   └─ What-if analysis

6. CLEANUP (Manual/Scheduled)
   ├─ Delete old sessions (>7 days)
   ├─ CASCADE deletes related data:
   │  ├─ road_nodes
   │  ├─ road_edges
   │  ├─ gps_trajectories
   │  ├─ congestion_states
   │  ├─ influence_probabilities
   │  └─ bottleneck_rankings
   └─ Clean up files in sessions/{id}/

Session States:
┌─────────┐  Upload   ┌──────────┐  Preprocess  ┌──────┐
│ pending ├──────────►│ uploaded ├─────────────►│ ready│
└─────────┘           └──────────┘              └───┬──┘
                                                    │
                                                    │ Run Model
                                                    ▼
                                               ┌─────────┐
                                               │analyzed │
                                               │(cached) │
                                               └─────────┘

Error State:
Any step ──Error──► ┌────────┐
                     │ failed │
                     └────────┘
```

---

## Technology Stack Details

```
┌──────────────────────────────────────────────────────────────┐
│                      TECHNOLOGY STACK                         │
└──────────────────────────────────────────────────────────────┘

FRONTEND
├─ React 18+
│  ├─ Hooks: useState, useEffect, useRef
│  ├─ React Router v6 (useNavigate, useSearchParams)
│  └─ Context API (AuthContext)
├─ Leaflet 1.9+
│  ├─ react-leaflet (MapContainer, TileLayer, CircleMarker)
│  └─ OpenStreetMap tiles
├─ Tailwind CSS
│  ├─ Utility-first styling
│  └─ Custom components (Card, Button, Toast)
└─ Build: Vite

BACKEND
├─ Flask 3.0+
│  ├─ Blueprint architecture
│  ├─ CORS enabled
│  └─ JSON API responses
├─ Python 3.8+
│  ├─ Type hints
│  ├─ f-strings
│  └─ List comprehensions
└─ Libraries:
   ├─ psycopg[binary] (PostgreSQL driver)
   ├─ werkzeug (file uploads)
   ├─ python-dotenv (env variables)
   └─ flask-cors

DATABASE
├─ PostgreSQL 12+
│  ├─ JSONB support
│  ├─ UUID type
│  └─ Window functions
├─ PostGIS 3.0+
│  ├─ ST_GeomFromText (WKT → geometry)
│  ├─ ST_Distance (proximity)
│  ├─ ST_DWithin (spatial queries)
│  ├─ ST_Centroid (marker positions)
│  ├─ ST_AsGeoJSON (export coords)
│  └─ GIST indexes
└─ Extensions:
   ├─ uuid-ossp (UUID generation)
   └─ postgis (spatial types)

ALGORITHMS
├─ LIM (Linear Independent Cascade)
│  ├─ Monte Carlo simulation
│  ├─ Probabilistic spread
│  └─ O(N × M × S) complexity
│      N = roads, M = edges, S = simulations
├─ Greedy Optimization
│  ├─ Marginal benefit calculation
│  ├─ Iterative selection
│  └─ O(K × N²) complexity
│      K = bottlenecks, N = roads
└─ Spatial Algorithms
   ├─ Map matching (nearest neighbor)
   ├─ Road graph building (R-tree)
   └─ Haversine distance
```

---

## Security & Performance

```
SECURITY MEASURES
├─ File Upload
│  ├─ Extension validation (.geojson, .csv only)
│  ├─ werkzeug.secure_filename()
│  ├─ Session-specific folders
│  └─ No executable files
├─ SQL Injection Prevention
│  ├─ Parameterized queries (%s placeholders)
│  ├─ No string concatenation
│  └─ psycopg3 automatic escaping
├─ Authentication
│  ├─ JWT tokens (existing auth system)
│  ├─ Role-based access (government only)
│  └─ Protected routes
└─ Input Validation
   ├─ File size limits
   ├─ Coordinate bounds checking
   └─ Data type validation

PERFORMANCE OPTIMIZATIONS
├─ Database
│  ├─ Indexes on foreign keys
│  ├─ GIST indexes on geometry
│  ├─ Partial indexes (session_id filtering)
│  └─ Query result limits
├─ Caching
│  ├─ Bottleneck rankings (1 hour TTL)
│  ├─ Influence probabilities (session-based)
│  └─ In-memory road graphs
├─ Algorithm
│  ├─ Reduced simulations for benefit calc (50 vs 100)
│  ├─ Early termination in greedy search
│  └─ Batch database operations
└─ Frontend
   ├─ React.memo for map components
   ├─ Debounced API calls
   ├─ Lazy loading (code splitting)
   └─ Efficient re-renders
```

---

This architecture provides a scalable, maintainable system for traffic bottleneck analysis with clear separation of concerns and efficient data processing.
