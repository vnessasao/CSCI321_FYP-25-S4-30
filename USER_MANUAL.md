# Flow Radar - Comprehensive User Manual
## Traffic Analytics & Monitoring Platform

**Version:** 1.0  
**Last Updated:** February 3, 2026  
**Document Purpose:** Complete user guide for all user roles

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Getting Started](#2-getting-started)
3. [Public User Guide](#3-public-user-guide)
4. [Government User Guide](#4-government-user-guide)
5. [Traffic Analyst Guide](#5-traffic-analyst-guide)
6. [System Developer Guide](#6-system-developer-guide)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. System Overview

### 1.1 What is Flow Radar?

Flow Radar is a comprehensive traffic analytics and monitoring platform designed to provide real-time traffic intelligence, bottleneck analysis, and predictive insights for Singapore's road network. The system serves four distinct user types, each with specialized features tailored to their needs.

### 1.2 Key Features

- **Real-time Traffic Monitoring**: Live congestion data from LTA
- **Bottleneck Analysis**: Identify critical traffic bottlenecks
- **Interactive Maps**: Leaflet-based maps with weather and transport overlays
- **Incident Reporting**: Report road incidents and submit feedback
- **Role-Based Access**: Customized interfaces for each user type

### 1.3 User Roles

| Role | Primary Purpose | Access Level |
|------|----------------|--------------|
| **Public User** | View traffic conditions, report incidents, plan routes | Basic - Read-only with feedback submission |
| **Government User** | Manage roadwork, analyze bottlenecks, oversee system | Advanced - Full analytical and management tools |
| **Traffic Analyst** | Run predictive models, analyze trends, schedule tasks | Expert - Data processing and model execution |
| **System Developer** | System administration, maintenance, user management | Full - Complete system access and configuration |

### 1.4 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│                  http://localhost:5173                   │
├─────────────────────────────────────────────────────────┤
│           Backend API (Flask + PostgreSQL)               │
│                  http://localhost:5000                   │
├─────────────────────────────────────────────────────────┤
│              External Data Sources                       │
│  • LTA DataMall (Traffic, Transport)                    │
│  • Data.gov.sg (Weather)                                │
│  • TomTom API (Optional - Traffic Stats)                │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Getting Started

### 2.1 System Requirements

- **Web Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Internet Connection**: Stable connection for real-time data
- **For Setup**: Python 3.8+, Node.js 16+, PostgreSQL 12+ with PostGIS

### 2.2 Accessing the System

#### Web Access
1. Open your web browser
2. Navigate to: `http://localhost:5173` (development) or your production URL
3. You'll see the landing page with login options

#### Login Options
- **For Public Users**: Click "Continue as Guest" for immediate access (limited features)
- **For Registered Users**: Select your role and enter credentials

### 2.3 First-Time Login

#### Step 1: Select Role
Choose your role from the four options:
- Public
- Government
- Developer
- Analyst

#### Step 2: Enter Credentials
- **Email**: Your registered email address
- **Password**: Your secure password (minimum 6 characters)
- **2FA Token** (Government users only): Optional two-factor authentication code

#### Step 3: Access Dashboard
After successful login, you'll be redirected to your role-specific dashboard.

### 2.4 Navigation

- **Sidebar**: Left side menu with features for your role
- **Top Bar**: Logo (home), user profile, logout button

---

## 3. Public User Guide

### 3.1 Overview

**Purpose**: Public users can view real-time traffic conditions, plan routes, report road incidents, and submit feedback to improve the system.

**Access Level**: Read-only with incident reporting and feedback submission capabilities.

### 3.2 Dashboard (`/dashboard`)

Your central hub for traffic information overview.

#### Features:
- **Traffic Summary Cards**: Quick stats on congestion levels
- **Recent Hotspots**: List of current traffic bottlenecks
- **Quick Actions**: Shortcuts to commonly used features
- **System Announcements**: Important updates from administrators

#### How to Use:
Traffic overview with summary cards, recent hotspots, and quick action buttons.
  - 🔴 Red: Heavy congestion (<20 km/h)
- **Mode Toggle**: Switch between Live and Prediction modes
- **Auto-Refresh**: Updates every 60 seconds
- **Interactive Tooltips**: Hover over roads for speed details

#### How to Use:
traffic visualization with color-coded roads:
- 🟢 **Green**: Normal flow (>40 km/h)
- 🟡 **Yellow**: Moderate congestion (20-40 km/h)
- 🔴 **Red**: Heavy congestion (<20 km/h)

**Controls**: Zoom (+/-), pan (drag), hover for details, toggle Live/Prediction mode

##### Finding Route Status:
1. Navigate to "Route Traffic Status"
2. Enter your **Starting Point** (address or landmark)
3. Enter your **Destination**
4. Click "Find Routes"

##### Understanding Results:
- **Route Options**: Displayed as Route A, B, C
- **Distance**: Total journey length in km
- **Duration**: Estimated travel time
- **Congestion Level**: Overall route congestion indicator
- **Segment Details**: Breakdown by road sections

##### Saving Routes:
Enter start and end points to view route options with distance, duration, and congestion levels. Bookmark frequently used routes.ed

##### Using Historical Data:
1. Select date range using date picker
2. Click "Load Historical Data"
3. Compare patterns across different days
View top 10 congested locations ranked by severity, with peak times and location details. Use date picker for historical comparisons.re

Optional Fields:
├── Upload Photo: Max 5MB
├── Lane Affected: Specify lane number
└── Contact Info: Phone/email for follow-up
```

##### Step 3: Submit Report
1. Review all entered information
2. Click "Submit Report"
3. Receive confirmation with tracking number
4. Get notifications on report status updates

#### After Submission:
- **Tracking**: Use incident ID to check status
- **Updates**: Receive notifications when authorities respond
- **History**: View all your submitted reports in "My Reports"

### 3.7 Submit Feedback (`/feedback`)

Submit feature requests, bug reports, data issues, or questions. Select category, enter subject and message, optionally attach files.

**Status tracking**: Submitted → Under Review → In Progress → Resolved/Broadcast

### 3.8 My Feedback (`/my-feedback`)

View all your feedback submissions, filter by category/status/date, and see developer responses.

##### Road Network (GeoJSON):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[103.8, 1.3], [103.81, 1.31]]
      },
      "properties": {
        "road_id": "unique_id",
        "road_name": "Marina Coastal Expressway",
        "speed_limit": 90
      }
    }
  ]
}
```

##### GPS Trajectories (CSV):
```csv
vehicle_id,timestamp,latitude,longitude,speed,heading
V001,2026-02-03 08:00:00,1.2897,103.8501,45.5,90
V001,2026-02-03 08:00:30,1.2900,103.8505,42.0,92
```

#### Upload Process:

##### Step 1: Create Upload Session
1. Navigate to "Upload & Analyze"
2. Click "New Upload Session"
3. Enter session name (e.g., "Morning Peak - Feb 3")

##### Step 2: Upload Road Network
1. Click "Upload Road Network"
2. Select GeoJSON file (max 50MB)
3. Wait for validation
4. Review uploaded road count

##### Step 3: Upload GPS Trajectories
1. Click "Upload GPS Trajectories"
2. Select CSV file (max 100MB)
3. Wait for validation
4. Review trajectory count

##### Step 4: Preprocess Data
1. Click "Preprocess Data" button
2. System performs:
   - Road network graph building
   - GPS trajectory map-matching
   - Congestion state calculation
   - Speed profile generation
3. Monitor status: **Pending** → **Preprocessing** → **Ready**
4. Wait time: 10-30 seconds (depending on data size)
Overview showing real-time statistics, bottleneck map, active incidents, and data quality metrics.t to Bottlenecks page upon completion

#### Sample Data Location:
- Road Network: `sample_data/sample_roads.geojson`
- GPS Trajectories: `sample_data/sample_gps.csv`

### 4.4 Bottlenecks Analysis (`/gov/bottlenecks`)

View and analyze identified traffic bottlenecks with interactive visualization.

#### Map Visualization:

##### Color Coding:
- 🔴 **Red Circles**: Critical bottlenecks (rank 1-3)
- 🟠 **Orange Circles**: Major bottlenecks (rank 4-7)
- 🟡 **Yellow Circles**: Moderate bottlenecks (rank 8-12)
- 🟢 **Green Circles**: Minor bottlenecks (rank 13+)

##### Circle Size:
- Larger circles = Higher benefit score
- Benefit score = Expected improvement if fixed

#### Bottleneck Rankings Table:

| Column | Description |
|--------|-------------|
| **Rank** | Position in severity ranking (1 = worst) |
| **Road Name** | Name of bottleneck road |
| **Benefit Score** | Impact reduction if bottleneck is fixed (0-100) |
| **Affected Roads** | Number of roads impacted by this bottleneck |
| **Congestion Level** | Current traffic state (Heavy/Moderate/Light) |
| **Actions** | Show on Map, View Details |

#### How to Use:

##### Viewing Bottlenecks:
1. Navigate to "Bottlenecks" after model run
2. Map displays all identified bottlenecks
3. Table lists bottlenecks with details
4. Click "Show on Map" to center on specific bottleneck

##### Understanding Benefit Scores:
- **Score 80-100**: Critical - Fix immediately
- **Score 60-79**: High priority - Schedule repair
- **Score 40-59**: Moderate - Plan maintenance
- **Score <40**: Low priority - Monitor

##### What-If Analysis:
1. Select bottlenecks using checkboxes (max 5)
2. Click "What-If Analysis" button
3. System simulates fixing selected roads
4. View:
   - **Before Scenario**: Current congestion
   - **After Scenario**: Expected improvement
   - **Impact Metrics**: Reduction in congestion %
   - LTM (Linear Threshold Model)**: Threshold-based propagation
- **SIR (Susceptible-Infected-Recovered)**: Epidemic model
- **SIS  Fields:
├── Road Name: Select from dropdown or enter
├── Location: Specific area or coordinates
├── Start Date & Time: When work begins
├── End Date & Time: Expected completion
└── Description: Work details
```

##### Step 2: Specify Impact
```
Impact Details:
├── Lanes Affected: Number and position
├── Traffic Diversion: Alternative routes
├── Expected Delay: Estimated wait time
└── Severity: Minor, Moderate, Major
```

##### Step 3: Publish Event
1. Review all details
2. Click "Publish Roadwork"
3. Event appears on public map
4. Notifications sent to affected users

#### Managing Roadwork:
- **View All**: List of active and scheduled roadwork
- **Edit**: Update details or extend duration
- **Cancel**: Remove if work is cancelled
- **Complete**: Mark as finished when done

### 4.8 EMAS Incident Status (`/gov/emas`)

Monitor and manage incidents from Expressway Monitoring & Advisory System.

#### Features:
- **Live Incident Feed**: Real-time EMAS updates
- **Incident Map**: Geographic visualization
- **Status Management**: Update incident states
- **Link to Roadwork**: Associate incidents with planned work

#### Incident Types:
- 🚗 Accident
- 🚧 Obstruction
- 🔧 Vehicle Breakdown
- 🌊 Heavy Rain/Flood
- 🔥 Vehicle Fire
- ⚠️ Other Emergency

#### How to Use:

##### Viewing Incidents:
1. Navigate to "EMAS Incident Status"
2. View list of active incidents
3. Filter by: Type, Severity, Location, Time
4. Click incident for full details

##### Managing Incidents:
1. Select incident from list
2. Click "Update Status"
3. Choose new status: Active, Cleared, False Alarm
4. Add notes (optional)
5. Click "Save"

##### Creating Incident:
1. Click "Report New Incident"
2. Fill form (similar to roadwork)
3. Submit
4. Auto-link to nearest roadwork if applicable

### 4.9 Time-Based Reports (`/gov/reports`)

Generate comprehensive analytical reports.

#### Report Types:

##### 1. Congestion Summary Report
- Peak hours analysis
- Average congestion by road
- Trend comparisons
- Export as PDF

##### 2. Bottleneck Impact Report
- Top bottlenecks over period
- Benefit scores ranking
- Cost-benefit analysis
- Recommended actions

##### 6. Incident Report
- All incidents in date range
- Resolution times
- Frequent locations
- Response metrics

##### 4. Custom Report
- User-defined parameters
- Multiple metrics
- Flexible date ranges
- Custom visualizations

#### How to Generate:

##### Step 1: Select Report Type
1. Navigate to "Time-based Reports"
2. Choose report type from dropdown

##### Step 2: Configure Parameters
```
Parameters:
├── Date Range: Start and end dates
├── Roads/Areas: Specific or all
├── Metrics: Select relevant KPIs
├── Format: PDF, Excel, or CSV
└── Recipients: Email addresses (optional)
```

##### Step 3: Generate and Download
1. Click "Generate Report"
2. Wait for processing (10-60 seconds)
3. Preview in browser
4. Click "Download" or "Email"
7 View Historical Trends (`/gov/trends`)

Analyze traffic patterns over time with date range selection, metric filtering, and data export options.

### 4.8t status (Normal/Delayed)
- Nearby bus stops

##### Bus Stop Details:
- Stop name and code
- Serving bus routes
- Next bus arrival times (live)
- Walking distance to MRT

### 4.12 Manage User Accounts (`/gov/manage-users`)

**Note**: Only available to Government Super Admins and Developers.

#### Features:
- **Create Users**: Add new accounts
- **Edit Users**: Modify details and roles
- **Suspend/Activate**: Temporarily disable access
- **View Activity**: User login history
- **Role Management**: Assign Public, Government, Analyst, or Developer

#### User Table:
9
| Column | Information |
|--------|-------------|
| ID | Unique user identifier |
| Name | Full name (optional) |
| Email | Login email |
| Role | User type badge |
| Status | Active/Suspended/Inactive |
| Last Login | Most recent access time |
| Actions | Edit, Suspend, Delete buttons |

#### How to Create User:

##### Step 1: Open Create Modal
1. Navigate to "Manage User Accounts"
2. Click "Create User" button

##### Step 2: Fill User Details
```
User Form:
├── Name: Full name (optional)
├── Email: Must be unique
├── Password: Min 6 characters
├── Role: Select from dropdown
│   ├── Public: Basic access
│   ├── Government: Advanced access
│   ├── Analyst: Data analysis access
│   └── Developer: Full system access
└── Status: Active (default) or Inactive
```

##### Step 3: Save User
1. Click "Create"
2. Confirmation message appears
3. New user receives welcome email (if configured)
4. User can now login
0
#### How to Suspend User:

##### Temporary Suspension:
1. Click "Suspend" button next to user
2. Enter suspension reason
3. Optionally set end date
4. Click "Confirm Suspension"
5. User cannot login until reactivated

##### Reactivating:
1. Find suspended user in list
2. Click "Activate" button
3. User can login immediately

#### Super Admin Protection:
- Super admins cannot be suspended or deleted
- Only developers can modify super admin accounts
- Identified by 🛡️ shield icon

---

## 5. Traffic Analyst Guide

### 5.1 Overview

**Purpose**: Traffic analysts handle data preprocessing, run predictive models, analyze historical trends, detect anomalies, and schedule automated analysis runs.

**Access Level**: Expert - Full data processing and analytical capabilities.

### 5.2 Upload & Analyze (`/analyst/data-upload`)

Upload road network (GeoJSON) and GPS trajectories (CSV), preprocess data, and configure model parameters.

### 5.3 Bottleneck Finder (`/analyst/bottlenecks`)

View identified bottlenecks with rankings, benefit scores, and what-if analysis capabilities.

### 5.4 Jam Spread Prediction (`/analyst/jam-prediction`)

Execute advanced traffic prediction and bottleneck analysis models.

#### Available Models:

##### 1. LIM (Linear Independent Cascade)
- **Purpose**: Predict jam propagation using cascade theory
- **Use Case**: High-volume expressways
- **Parameters**: Influence probability threshold
- **Runtime**: ~60 seconds

##### 2. LTM (Linear Threshold Model)
- **Purpose**: Threshold-based congestion spread
- **Use Case**: Interconnected urban roads
- **Parameters**: Activation threshold
- **Runtime**: ~45 seconds

##### 3. SIR (Susceptible-Infected-Recovered)
- **Purpose**: Epidemic model for temporary jams
- **Use Case**: Event-driven congestion
- **Parameters**: Infection rate, recovery rate
- **Runtime**: ~90 seconds

##### 4. SIS (Susceptible-Infected-Susceptible)
- **Purpose**: Recurring congestion patterns
- **Use Case**: Daily peak hours
- **Parameters**: Infection rate
- **Runtime**: ~75 seconds

##### 5. Greedy Bottleneck Algorithm
- **Purpose**: Identify top-K critical bottlenecks
- **Use Case**: Infrastructure planning
- **Parameters**: K value (5-50)
- **Runtime**: ~30 seconds
Run LIM, LTM, SIR, SIS, or Greedy algorithm models with configurable parameters. View predictions on map with probability indicators.
##### Step 1: Select Analysis Type
1. Navigate to "View Historical Trends"
2. Choose analysis type from tabs

##### Step 2: Set Parameters
```
Parameters:
├── Date Range: Start and end dates (max 1 year)
├── Roads/Areas: Specific or all
├── Aggregation: Hourly, Daily, Weekly, Monthly
├── Metrics: Speed, Volume, Congestion Index
└── Comparison: Single period or multiple
```

##### Step 3: Generate Visualizations
1. Click "Analyze"
2. Wait for data processing (5-30 seconds)
3. View charts and graphs

##### Chart Types:
- **Line Charts**: Trends over time
- **Bar Charts**: Comparisons across categories
- **Heatmaps**: Time-based patterns
- **Box Plots**: Distribution analysis
- **Scatter Plots**: Correlation studies

##### Step 4: Export Data
1. Click "Export" button
2. Choose format: Excel, CSV, or PNG
3. Download for offline analysis or reporting

#### Sample Insights:

##### Example 1: Morning Peak Pattern
```
Road: PIE (Pan Island Expressway)
Time: 7:30 AM - 9:00 AM (Mon-Fri)
Pattern: Consistent heavy congestion
Average Speed: 25 km/h (vs 80 km/h normal)
Recommendation: Implement dynamic lane management
```

##### Example 2: Weekend Anomaly
```
Location: Orchard Road
Time: Saturday 2:00 PM - 6:00 PM
Pattern: Recurring moderate congestion
Cause: Shopping district traffic
Recommendation: Enhanced public transport messaging
```

### 5.6 Schedule Automated Runs (`/analyst/schedule`)

Set up recurring model executions for continuous monitoring.

#### Schedule Types:

##### 1. Recurring Analysis
- Daily: Run every day at specified time
- Weekly: Run on specific days
- Monthly: Run on specific date
- Custom: User-defined cron expression

##### 2. Event-Triggered
- New data uploaded
- Congestion threshold exceeded
- Weather conditions met
- Incident reported

#### How to Create Schedule:

##### Step 1: Open Schedule Creator
1. Navigate to "Schedule Automated Runs"
2. Click "Create Schedule"

##### Step 2: Configure Schedule
```
Schedule Configuration:
├── Name: Descriptive name
├── Model: Select model type
├── Session: Choose data session or "Latest"
├── Frequency: Daily/Weekly/Monthly/Custom
├── Time: Execution time (24-hour format)
├── Parameters: Model-specific settings
└── Notifications: Email on completion (optional)
```

##### Step 3: Save and Activate
1. Review configuration
2. Clicktime series patterns, hotspot frequency, regional comparisons, and incident impact. Set date ranges, select metrics, and export charts as Excel/CSV/PNG.6. System Developer Guide

### 6.1 Overview

**Purpose**: System developers have complete administrative access to manage algorithms, monitor performance, handle user feedback, configure roles and permissions, perform backups, and maintain the system.

**Access Level**: Full - Complete system access and configuration.

### 6.2 Developer Dashboard

Comprehensive system overview:
- **System Health**: Server status, database connections
- **API Metrics**: Request rates, error rates, latency
- **User Statistics**: Active users, new signups
- **Data Quality**: Upload success rates, processing errors
- **Recent Logs**: Critical system events

### 6.3 Algorithm Modules (`/dev/algorithms`)

Manage and monitor all traffic analysis algorithms.

#### Available Algorithms:

| ID | Name | Type | Status | Description |
|----|------|------|--------|-------------|
| LIM | Linear Independent Cascade | Propagation | Active | Cascade-based jam spread |
| LTM | Linear Threshold Model | Propagation | Active | Threshold activation model |
| SIR | Susceptible-Infected-Recovered | Epidemic | Active | Temporary jam model |
| SIS | Susceptible-Infected-Susceptible | Epidemic | Active | Recurring jam model |
| GREEDY | Greedy Bottleneck Finder | Optimization | Active | Top-K bottleneck identification |

#### Features:
- **View Details**: Algorithm parameters and description
- **Suspend/Activate**: Temporarily disable algorithms
- **Edit Parameters**: Modify default settings
- **View Usage**: Execution history and performance

#### How to Manage:

##### Viewing Algorithms:
1. Navigate to "Algorithm Modules"
2. See table of all algorithms
3. Click algorithm name for full details

##### Suspending Algorithm:
1. Click "Suspend" button
2. Enter reason for suspension
3. Confirm action
4. Algorithm unavailable until reactivated

Set up recurring model executions (daily/weekly/monthly) or event-triggered runs. Configure model, time, parameters, and email notifications.

### 5.7 Anomaly Detection (`/analyst/anomalies`)

Detect unusual traffic patterns using statistical analysis. View anomalies by severity, investigate causes, and mark as true/false positives.

---

## 6. System Developer Guide

### 6.1 Overview

**Purpose**: Complete administrative access to manage algorithms, handle feedback, configure roles/permissions, and perform backups.

**Access Level**: Full system access and configuration.

### 6.2 Algorithm Modules (`/dev/algorithms`)

View all traffic analysis algorithms (LIM, LTM, SIR, SIS, GREEDY). Suspend/activate algorithms, edit default parameters, and view usage statistics.

### 6.3 Access Roles & Permissions (`/dev/access-roles`)

Configure role-based access control (RBAC).

#### Default Role Permissions:

**Public**: view_traffic_map, report_incidents, submit_feedback  
**Government**: All Public + upload_data, run_models, manage_users  
**Analyst**: view_predictions, preprocess_data, manage_schedules  
**Developer**: All permissions (automatic bypass)

Create custom roles, assign permissions, and manage system access.

### 6.4 Feedback Management (`/dev/feedback`)

Review user feedback, update status, and respond.

#### Update & Broadcast (SD-19):
1. Click "Edit" on feedback
2. Update the message
3. Check "Broadcast as System Alert"
4. Message sent to all users as pop-up

Use for common issues affecting many users.

### 6.5 Backup & Restore (`/dev/backup`)

Create full or partial database backups with compression and encryption options.

#### Backup Types:
- **Full**: Complete database snapshot
- **Partial**: Selected tables only
- **Incremental**: Changes since last backup

#### Restore:
1. Select backup file
2. Review impact warning
3. Confirm to restore (overwrites current data)

**Schedule**: Set automated daily/weekly backups during off-peak hours.

---

## 7. Troubleshooting
5. Users see "Algorithm temporarily unavailable" message

##### Editing Parameters:
1. Click "Edit" button
2. Modify default values:
   ```
   LIM Parameters:
   ├── Influence Probability: 0.1-0.9 (default: 0.3)
   ├── Decay Factor: 0.1-1.0 (default: 0.8)
   └── Max Propagation Steps: 1-10 (default: 5)
   ```
3. Click "Save"
4. New defaults apply to future runs

##### Viewing Algorithm Performance:
1. Click "Performance" tab
2. See metrics:
   - Total executions
   - Average runtime
   - Success rate
   - User ratings

### 6.4 System Performance (`/dev/performance`)

Monitor system health and performance metrics.

#### Monitoring Sections:

##### 1. Server Metrics
- **CPU Usage**: Real-time percentage
- **Memory Usage**: RAM consumption
- **Disk I/O**: Read/write operations
- **Network Traffic**: Inbound/outbound bandwidth

##### 2. Database Metrics
- **Connection Pool**: Active/idle connections
- **Query Performance**: Slow query log
- **Table Sizes**: Storage usage
- **Cache Hit Rate**: Query cache efficiency

##### 3. API Metrics
- **Request Rate**: Requests per second
- **Response Times**: P50, P95, P99 percentiles
- **Error Rate**: 4xx and 5xx errors
- **Endpoint Usage**: Most called APIs

##### 4. Frontend Metrics
- **Page Load Times**: Average load duration
- **User Sessions**: Active concurrent users
- **Error Logs**: JavaScript errors
- **Browser Distribution**: User agent stats

#### How to Use:

##### Real-Time Monitoring:
1. Navigate to "System Performance"
2. View live dashboards
3. Auto-refresh every 30 seconds

##### Setting Alerts:
1. Click "Configure Alerts"
2. Set thresholds:
   ```
   Alert Thresholds:
   ├── CPU > 80%: Warning
   ├── Memory > 90%: Critical
   ├── API Error Rate > 5%: Warning
   ├── Response Time > 3s: Warning
   └── Database Connections > 90%: Critical
   ```
3. Configure notifications (email, SMS)
4. Click "Save Alerts"

##### Historical Analysis:
1. Select date range
2. Choose metrics to compare
3. Generate performance report
4. Identify trends and bottlenecks

### 6.5 Maintenance & Logs (`/dev/logs`)

Access system logs for debugging and auditing.

#### Log Types:

##### 1. Application Logs
- Flask backend logs
- React frontend errors
- Unhandled exceptions
- Stack traces

##### 2. Access Logs
- User login attempts
- API requests
- Failed authentications
- IP addresses

##### 3. Database Logs
- Query execution logs
- Transaction logs
- Deadlocks and conflicts
- Slow queries

##### 4. System Logs
- Server startup/shutdown
- Scheduled task executions
- Backup operations
- Configuration changes

#### How to Use:

##### Viewing Logs:
1. Navigate to "Maintenance & Logs"
2. Select log type
3. Set filters:
   - Date range
   - Severity (Info, Warning, Error, Critical)
   - Component (Backend, Frontend, Database)
   - Search term

##### Example Log Entry:
```
[2026-02-03 14:32:15] ERROR backend.routes.bottlenecks
User ID: 42 | Session: abc123 | IP: 192.168.1.100
Error: Unable to calculate benefit scores
Traceback: [Full stack trace...]
```

##### Downloading Logs:
1. Apply desired filters
2. Click "Export Logs"
3. Choose format: TXT, JSON, or CSV
4. Download for offline analysis

##### Real-Time Log Monitoring:
1. Click "Live Logs" tab
2. See logs as they occur
3. Filter by severity
4. Pause/resume stream

### 6.6 Access Roles & Permissions (`/dev/access-roles`)

Configure role-based access control (RBAC).

#### Permission Categories:

##### Traffic & Analytics:
- view_traffic_map
- view_analytics
- view_predictions
- view_bottlenecks

##### Data Management:
- upload_data
- preprocess_data
- run_models
- delete_data

##### User Management:
- manage_users
- view_users
- manage_roles
- manage_permissions

##### Incidents & Feedback:
- report_incidents
- manage_incidents
- submit_feedback
- manage_feedback

##### System Administration:
- view_logs
- manage_algorithms
- perform_backups
- view_performance

#### Default Role Permissions:

##### Public:
- view_traffic_map
- view_analytics
- report_incidents
- submit_feedback
- save_bookmarks

##### Government:
- All Public permissions
- upload_data
- preprocess_data
- run_models
- manage_users (if super admin)
- manage_incidents
- view_weather
- view_transport

##### Analyst:
- view_traffic_map
- view_analytics
- view_predictions
- view_bottlenecks
- upload_data
- preprocess_data
- run_models
- view_historical
- manage_schedules

##### Developer:
- **All Permissions** (automatic bypass)

#### How to Manage:

##### Viewing Roles:
1. Navigate to "Access Roles"
2. See table of all roles
3. View assigned permissions for each

##### Creating Custom Role:
1. Click "Create Role"
2. Enter role name (e.g., "City Planner")
3. Enter description
4. Select permissions from checklist
5. Click "Create"

##### Editing Role Permissions:
1. Click "Edit" on role
2. Check/uncheck permissions
3. Click "Update"
4. Changes apply immediately to all users with that role

##### Creating Custom Permission:
1. Click "Permissions" tab
2. Click "Add Permission"
3. Enter details:
   ```
   Permission Form:
   ├── Name: machine_readable (e.g., export_reports)
   ├── Display Name: Human-readable (e.g., Export Reports)
   ├── Category: Group (e.g., Reports)
   └── Description: What it allows
   ```
4. Click "Create"
5. Assign to roles as needed

### 6.7 Feedback Management (`/dev/feedback`)

Review and respond to user feedback system-wide.

#### Feedback Dashboard:
- **Pending**: Awaiting review
- **Under Review**: Being evaluated
- **In Progress**: Being implemented
- **Resolved**: Completed
- **Broadcast**: Sent as announcement

#### Features:
- **View All Feedback**: Complete list with filters
- **Update Status**: Change feedback state
- **Respond**: Reply to users
- **Broadcast**: Send as system-wide alert
- **Statistics**: Feedback metrics

#### How to Use:

##### Viewing Feedback:
1. Navigate to "Feedback Management"
2. See all submitted feedback
3. Filter by:
   - Category (Bug, Feature Request, etc.)
   - Status (Pending, Resolved, etc.)
   - Date range
   - User

##### Responding to Feedback:

###### Method 1: Direct Reply (Traditional)
1. Click "View" on feedback item
2. Read user's message
3. Click "Reply"
4. Compose response
5. Click "Send Reply"
6. User receives email notification

###### Method 2: Update & Broadcast (SD-19 Feature)
1. Click "Edit" button on feedback
2. Update the feedback message itself
3. Check "Broadcast as System Alert"
4. Click "Update Feedback"
5. **Result**: Updated message sent to ALL users as pop-up alert

**Use Case**: When feedback represents a common issue affecting many users (e.g., "Map loading is slow") - update it with solution ("We've optimized map loading. Please clear cache.") and broadcast to everyone.

##### Changing Status:
1. Select feedback item
2. Click "Change Status" dropdown
3. Choose new status:
   - **Under Review**: Assigned for evaluation
   - **In Progress**: Being worked on
   - **Resolved**: Issue fixed or question answered
   - **Broadcast**: Sent as announcement (auto-set when broadcasting)
4. Add status notes (optional)
5. Click "Update"

##### Viewing Broadcast History:
1. Click "Broadcasts" tab
2. See all sent broadcasts
3. View recipient count
4. Check acknowledgment rate

### 6.8 Backup & Restore (`/dev/backup`)

Manage database backups and disaster recovery.

#### Backup Types:

##### 1. Full Backup
- Complete database snapshot
- All tables and data
- Size: 100MB - 5GB (depending on data)
- Duration: 2-10 minutes

##### 2. Partial Backup
- Specific tables only
- User-selected data
- Size: 10MB - 1GB
- Duration: 30 seconds - 3 minutes

##### 3. Incremental Backup
- Only changes since last backup
- Space-efficient
- Size: 1MB - 100MB
- Duration: 10-60 seconds

#### How to Create Backup:

##### Step 1: Initiate Backup
1. Navigate to "Backup & Restore"
2. Click "Create Backup"

##### Step 2: Configure Backup
```
Backup Configuration:
├── Type: Full, Partial, or Incremental
├── Tables: Select if Partial
│   ├── users (always included)
│   ├── upload_sessions
│   ├── road_nodes
│   ├── gps_trajectories
│   ├── bottleneck_ranks
│   └── ... (other tables)
├── Compression: Enable for smaller file size
└── Encryption: Enable for sensitive data
```

##### Step 3: Execute Backup
1. Click "Start Backup"
2. Monitor progress bar
3. Wait for completion
4. Download backup file or store on server

#### Backup Storage:
- **Local**: Stored in `backend/backups/` directory
- **Format**: `.sql` (plain SQL) or `.dump` (pg_dump format)
- **Naming**: `backup_[type]_[timestamp].sql`
- **Retention**: Configurable (default: 30 days)

#### How to Restore:

##### Step 1: Select Backup
1. Navigate to "Backup & Restore"
2. Click "Restore" tab
3. Choose backup file from list or upload

##### Step 2: Review Restore Impact
```
Restore Preview:
├── Backup Date: When backup was created
├── Database Size: Amount of data
├── Tables Included: List of tables
├── Warning: Current data will be overwritten!
└── Estimated Time: Restore duration
```

##### Step 3: Confirm and Restore
1. Check "I understand this will overwrite current data"
2. Click "Restore Database"
3. System stops accepting new requests (brief downtime)
4. Restoration executes
5. System restarts
6. Verify data integrity

**Warning**: Restoration is destructive! Current data will be lost unless backed up first.

#### Automated Backups:

##### Setting Up Scheduled Backups:
1. Click "Schedule" tab
2. Configure:
   ```
   Schedule Settings:
   ├── Frequency: Daily, Weekly, or Monthly
   ├── Time: Preferred backup time (e.g., 2:00 AM)
   ├── Type: Full or Incremental
   ├── Retention: How long to keep (days)
   └── Notifications: Email on completion/failure
   ```
3. Click "Save Schedule"
4. Backups run automatically

##### Best Practices:
- Schedule during low-usage hours (midnight - 4 AM)
- Keep at least 7 daily backups
- Monthly full backup for long-term storage
- Test restore process quarterly

### 6.9 Visualization Modules (`/dev/visualization`)

Configure and customize data visualization components.

#### Customizable Visualizations:
- Map color schemes
- Chart types and styles
- Dashboard layouts
- Data refresh intervals

#### How to Use:
1. Navigate to "Visualization Modules"
2. Select component to customize
3. Modify settings (colors, thresholds, etc.)
4. Preview changes
5. Click "Apply" to save

### 6.10 API Integrations (`/dev/integrations`)

Manage external API connections and credentials.

#### Integrated APIs:

##### 1. LTA DataMall
- **Purpose**: Singapore traffic, transport data
- **Endpoints**: Traffic speeds, MRT alerts, bus arrivals
- **Status**: ✅ Active
- **Configuration**: API key required

##### 2. Data.gov.sg
- **Purpose**: Weather forecasts, rainfall, temperature
- **Endpoints**: 2-hour forecast, 4-day forecast, air quality
- **Status**: ✅ Active
- **Configuration**: No API key required

##### 3. TomTom Traffic API (Optional)
- **Purpose**: Alternative traffic data source
- **Endpoints**: Traffic flow, incidents
- **Status**: ⏳ Pending API key
- **Configuration**: Requires paid subscription

#### How to Configure:

##### Adding API Key:
1. Navigate to "API Integrations"
2. Find API service
3. Click "Configure"
4. Enter API key
5. Click "Test Connection"
6. If successful, click "Save"

##### Testing Integration:
1. Click "Test" button next to API
2. System makes sample request
3. View response and status code
4. Troubleshoot errors if any

##### Monitoring API Usage:
1. View API usage statistics
2. Check rate limits
3. Monitor request quotas
4. Set usage alerts

### 6.11 Deployments (`/dev/deployments`)

Manage system deployments and updates.

#### Features:
- **Version Control**: Track deployed versions
- **Rollback**: Revert to previous version if issues occur
- **Health Checks**: Post-deployment verification
- **Deployment History**: Log of all deployments

#### How to Deploy:

##### Step 1: Prepare Deployment
1. Navigate to "Deployments"
2. Click "New Deployment"
3. Select version/branch to deploy

##### Step 2: Pre-Deployment Checks
- Run automated tests
- Check database migrations
- Verify dependencies
- Review changelog

##### Step 3: Execute Deployment
1. Click "Deploy"
2. Monitor deployment progress
3. System performs:
   - Code update
   - Database migrations
   - Service restart
   - Health checks

##### Step 4: Post-Deployment
1. Verify system health
2. Check logs for errors
3. Test critical features
4. Monitor user feedback

##### Rollback (if needed):
1. Click "Rollback" on deployment
2. Select previous stable version
3. Confirm rollback
4. System reverts to previous state

---

## 7. Common Features

### 7.1 Authentication & Security

#### Password Requirements:
- Minimum 6 characters
- Recommended: Mix of uppercase, lowercase, numbers, special characters
- No password expiry (change if compromised)

#### Two-Factor Authentication (2FA):
- Optional for Government users
- Required for Developers (recommended)
- TOTP-based (Google Authenticator, Authy)

#### Session Management:
- Sessions expire after 24 hours of inactivity
- Auto-logout on browser close (configurable)
- Single session per user (concurrent login detection)

### 7.2 Bookmarks & Favorites

#### Saving Routes:
1. Search for route in Route Status page
2. Click "Bookmark" icon
3. Enter nickname
4. Access from "My Bookmarks" sidebar item

#### Saving Locations:
1. Click location on map
2. Click "Save Location"
3. Add to favorites

### 7.3 Notifications

#### Notification Types:
- 🔔 System Announcements
- ⚠️ Critical Alerts (major incidents)
- 📢 Broadcast Messages (from developers)
- 💬 Feedback Responses
- ✅ Task Completions (for analysts)

#### Managing Notifications:
1. Click bell icon in top bar
2. View unread notifications
3. Click to view details
4. Mark as read or delete

#### Notification Preferences:
1. Go to User Profile
2. Click "Notifications"
3. Enable/disable by type
4. Choose delivery method: In-app, Email, SMS

### 7.4 Exporting Data

#### Available Formats:
- **PDF**: Reports, visualizations
- **Excel**: Tabular data with formatting
- **CSV**: Raw data for analysis
- **PNG/JPG**: Charts and maps
- **GeoJSON**: Geographic data

#### How to Export:
1. Navigate to page with data to export
2. Click "Export" button
3. Select format
4. Choose fields to include (optional)
5. Click "Download"

### 7.5 Help & Support

#### In-App Help:
- **Tooltips**: Hover over ? icons for quick help
- **Guided Tours**: First-time user walkthroughs
- **Contextual Help**: Help relevant to current page

#### Documentation:
- User Manual (this document)
- API Documentation (for developers)
- Video Tutorials (YouTube channel)
- FAQ Section

#### Contact Support:
1. Click "Help" in user menu
2. Select issue category
3. Fill contact form or use:
   - Email: support@flowradar.sg
   - Phone: +65 6xxx xxxx (Mon-Fri, 9 AM - 6 PM)
   - Live Chat: Available during business hours

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Issue 1: Cannot Login
**Symptoms**: "Invalid credentials" error

**Solutions**:
1. Verify email address is correct
2. Check password (case-sensitive)
3. Ensure correct role is selected
4. Try "Forgot Password" link
5. Contact admin if account is suspended

#### Issue 2: Map Not Loading
**Symptoms**: Blank map or "Loading..." indefinitely

**Solutions**:
1. Check internet connection
2. Refresh browser (Ctrl+F5 / Cmd+Shift+R)
3. Clear browser cache
4. Try different browser
5. Disable browser extensions (AdBlock, etc.)
6. Check if LTA API is down (Status page)

#### Issue 3: Data Upload Fails
**Symptoms**: Error during file upload

**Solutions**:
1. Verify file format:
   - Road Network: `.geojson`
   - GPS Trajectories: `.csv`
2. Check file size limits:
   - Road Network: Max 50MB
   - GPS: Max 100MB
3. Validate file structure matches required format
4. Try smaller file (split data if necessary)
5. Check for special characters in filenames

#### Issue 4: Preprocessing Stuck
**Symptoms**: Status remains "Preprocessing" for >5 minutes

**Solutions**:
1. Wait 10 minutes (large files take time)
2. Check backend logs (developers only)
3. Refresh page to update status
4. Contact analyst/developer to check server
5. If stuck >30 minutes, reprocess session

#### Issue 5: Model Run Fails
**Symptoms**: Error message during model execution

**Solutions**:
1. Ensure data is preprocessed (status = "Ready")
2. Check K value is reasonable (5-50)
3. Verify time horizon is set
4. Check algorithm is not suspended
5. Review logs for specific error
6. Contact analyst if issue persists

#### Issue 6: Slow Performance
**Symptoms**: Pages load slowly, maps lag

**Solutions**:
1. Close unnecessary browser tabs
2. Clear browser cache
3. Check internet speed (>5 Mbps recommended)
4. Use modern browser version
5. Reduce map data density (zoom in)
6. Contact developers during peak usage

### 8.2 Error Messages

#### "Session Expired - Please Login Again"
- **Cause**: Session timed out (24 hours)
- **Action**: Login again with credentials

#### "Insufficient Permissions"
- **Cause**: Attempting to access restricted feature
- **Action**: Contact admin to verify role and permissions

#### "API Rate Limit Exceeded"
- **Cause**: Too many requests in short time
- **Action**: Wait 60 seconds and try again

#### "Database Connection Error"
- **Cause**: Backend database unavailable
- **Action**: Retry in 5 minutes; contact IT if persists

#### "Invalid File Format"
- **Cause**: Uploaded file doesn't match expected format
- **Action**: Review format requirements and re-upload

### 8.3 Browser Compatibility

#### Recommended Browsers:
- ✅ Google Chrome 90+
- ✅ Mozilla Firefox 88+
- ✅ Microsoft Edge 90+
- ✅ Safari 14+

#### Known Issues:
- In7.1 Common Issues

**Cannot Login**: Verify email, password, role selection. Try password reset or contact admin.

**Map Not Loading**: Refresh browser (Ctrl+F5), clear cache, check internet connection, or try different browser.

**Data Upload Fails**: Check file format (`.geojson` for roads, `.csv` for GPS), file size (max 50MB/100MB), and file structure.

**Preprocessing Stuck**: Wait 10 minutes for large files. If stuck >30 minutes, reprocess session.

**Model Run Fails**: Ensure data status is "Ready", check K value (5-50), verify algorithm is active.

**Slow Performance**: Close unnecessary tabs, clear cache, check internet speed (>5 Mbps), zoom in on map.

### 7.2 Error Messages

- **"Session Expired"**: Login again after 24-hour timeout
- **"Insufficient Permissions"**: Contact admin to verify role
- **"API Rate Limit Exceeded"**: Wait 60 seconds
- **"Database Connection Error"**: Retry in 5 minutes
- **"Invalid File Format"**: Review format requirements

### 7.3 Browser Compatibility

**Recommended**: Chrome 90+, Firefox 88+, Edge 90+, Safari 14+  
**Not Supported**: Internet Explorer 11

**Required**: JavaScript enabled, cookies enabled, popups allowed

---

## Appendix Aback | `/feedback` | Share suggestions |

### Government User - Essential Features
| Feature | Location | Purpose |
|---------|----------|---------|
| Upload Data | `/gov/upload` | Upload road/GPS data |
| Bottlenecks | `/gov/bottlenecks` | View analysis results |
| Manage Users | `/gov/manage-users` | User administration |
| Roadwork | `/gov/roadwork` | Schedule road work |

### Analyst - Essential Features
| Feature | Location | Purpose |
|---------|----------|---------|
| Run Model | `/analyst/run-model` | Execute traffic models |
| Trends | `/analyst/trends` | Analyze patterns |
| Schedule | `/analyst/schedule` | Automate runs |
| Anomalies | `/analyst/anomalies` | Detect unusual traffic |

### Developer - Essential Features
| Feature | Location | Purpose |
|---------|----------|---------|
| Algorithms | `/dev/algorithms` | Manage algorithms |
| Logs | `/dev/logs` | View system logs |
| Backup | `/dev/backup` | Database backups |
| Feedback | `/dev/feedback` | Manage user feedback |

---

**End of User Manual** | © 2026 Flow Radar
 vehicle_id, timestamp (YYYY-MM-DD HH:MM:SS), latitude, longitude, speed (km/h, optional), heading (0-360°, optional)

---

## Appendix BC: Quick Reference**Public**: Live Map (`/map`), Route Status, Report Incident, Submit Feedback

**Government**: Upload Data (`/gov/data-upload`), Bottlenecks, Manage Users, Roadwork, Weather/Transport Overlays

**Analyst**: Upload & Analyze (`/analyst/data-upload`), Bottleneck Finder, Jam Prediction, Trends, Schedule, Anomalies

**Developer**: Algorithms (`/dev/algorithms`), Access Roles, Feedback Management, Backup & Restore