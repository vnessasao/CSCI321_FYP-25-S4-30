// Mock GeoJSON data for Singapore roads
export const mockRoadsGeoJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'road-1',
        name: 'Orchard Road',
        region: 'Central',
        congestion: 'moderate',
        delay: 5,
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [103.8419, 1.3048],
          [103.8425, 1.3055],
          [103.8430, 1.3062],
        ],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'road-2',
        name: 'Marina Bay',
        region: 'Central',
        congestion: 'heavy',
        delay: 15,
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [103.8580, 1.2814],
          [103.8585, 1.2820],
          [103.8590, 1.2825],
        ],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'road-3',
        name: 'Jurong East',
        region: 'West',
        congestion: 'free',
        delay: 0,
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [103.7414, 1.3329],
          [103.7420, 1.3335],
          [103.7425, 1.3340],
        ],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'road-4',
        name: 'Tampines Avenue',
        region: 'East',
        congestion: 'moderate',
        delay: 8,
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [103.9448, 1.3526],
          [103.9455, 1.3532],
          [103.9460, 1.3538],
        ],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'road-5',
        name: 'Woodlands Road',
        region: 'North',
        congestion: 'free',
        delay: 2,
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [103.7880, 1.4360],
          [103.7885, 1.4365],
          [103.7890, 1.4370],
        ],
      },
    },
  ],
}

// Mock hotspots data
export const mockHotspots = [
  { id: 1, roadName: 'Orchard Road', region: 'Central', avgDelay: 15, severity: 'heavy' },
  { id: 2, roadName: 'Marina Bay', region: 'Central', avgDelay: 12, severity: 'heavy' },
  { id: 3, roadName: 'Tampines Avenue', region: 'East', avgDelay: 8, severity: 'moderate' },
  { id: 4, roadName: 'Jurong East', region: 'West', avgDelay: 3, severity: 'free' },
  { id: 5, roadName: 'Woodlands Road', region: 'North', avgDelay: 2, severity: 'free' },
]

// Mock incidents
export const mockIncidents = [
  {
    id: 'inc-1',
    type: 'Accident',
    location: 'Orchard Road',
    time: new Date().toISOString(),
    status: 'In Progress',
    region: 'Central',
  },
  {
    id: 'inc-2',
    type: 'Roadworks',
    location: 'Marina Bay',
    time: new Date(Date.now() - 3600000).toISOString(),
    status: 'In Progress',
    region: 'Central',
  },
]

// Mock alerts
export const mockAlerts = [
  {
    id: 'alert-1',
    message: 'Heavy congestion detected on Orchard Road',
    roadId: 'road-1',
    region: 'Central',
    timestamp: new Date().toISOString(),
    acknowledged: false,
  },
  {
    id: 'alert-2',
    message: 'Accident reported on Marina Bay',
    roadId: 'road-2',
    region: 'Central',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    acknowledged: false,
  },
]

// Mock users
export const mockUsers = [
  { id: 1, name: 'John Doe', email: 'john@example.com', role: 'government', status: 'Active' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'analyst', status: 'Active' },
  { id: 3, name: 'Bob Wilson', email: 'bob@example.com', role: 'public', status: 'Active' },
]

// Mock feedback
export const mockFeedback = [
  {
    id: 1,
    category: 'Feature Request',
    message: 'Would like to see real-time updates more frequently',
    date: new Date().toISOString(),
    source: 'public',
  },
  {
    id: 2,
    category: 'Bug',
    message: 'Map sometimes doesn\'t load on mobile devices',
    date: new Date(Date.now() - 86400000).toISOString(),
    source: 'public',
  },
]

// Mock algorithms
export const mockAlgorithms = [
  {
    id: 1,
    name: 'Traffic Flow Prediction',
    version: '2.1.0',
    status: 'Active',
    lastUpdated: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 2,
    name: 'Congestion Detection',
    version: '1.5.2',
    status: 'Active',
    lastUpdated: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: 3,
    name: 'Route Optimization',
    version: '3.0.1',
    status: 'Suspended',
    lastUpdated: new Date(Date.now() - 259200000).toISOString(),
  },
]

// Mock roles
export const mockRoles = [
  {
    id: 1,
    name: 'Government Admin',
    description: 'Full access to government features',
    permissions: ['view_dashboard', 'manage_incidents', 'view_reports', 'manage_users'],
    status: 'Active',
  },
  {
    id: 2,
    name: 'Traffic Analyst',
    description: 'Access to analysis tools',
    permissions: ['view_dashboard', 'run_models', 'view_trends'],
    status: 'Active',
  },
]

// Mock schedules
export const mockSchedules = [
  {
    id: 1,
    model: 'Traffic Flow Prediction',
    frequency: 'daily',
    lastRun: new Date(Date.now() - 3600000).toISOString(),
    nextRun: new Date(Date.now() + 82800000).toISOString(),
  },
  {
    id: 2,
    model: 'Congestion Detection',
    frequency: 'hourly',
    lastRun: new Date(Date.now() - 1800000).toISOString(),
    nextRun: new Date(Date.now() + 1800000).toISOString(),
  },
]

// Mock region data
export const mockRegionData = {
  North: { congestionIndex: 0.3, alerts: 2, lastUpdated: new Date(Date.now() - 120000) },
  South: { congestionIndex: 0.5, alerts: 1, lastUpdated: new Date(Date.now() - 180000) },
  East: { congestionIndex: 0.4, alerts: 3, lastUpdated: new Date(Date.now() - 90000) },
  West: { congestionIndex: 0.2, alerts: 0, lastUpdated: new Date(Date.now() - 60000) },
  Central: { congestionIndex: 0.8, alerts: 5, lastUpdated: new Date(Date.now() - 30000) },
}

