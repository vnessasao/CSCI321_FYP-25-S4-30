import {
  mockRoadsGeoJSON,
  mockHotspots,
  mockIncidents,
  mockAlerts,
  mockUsers,
  mockFeedback,
  mockAlgorithms,
  mockRoles,
  mockSchedules,
  mockRegionData,
} from './mockData'

// Simulate API delay
const delay = (ms = 1000) => new Promise((resolve) => setTimeout(resolve, ms))

// Public API
export const getRoadsData = async (region = 'All') => {
  await delay(800)
  if (region === 'All') {
    return mockRoadsGeoJSON
  }
  return {
    ...mockRoadsGeoJSON,
    features: mockRoadsGeoJSON.features.filter(
      (f) => f.properties.region === region
    ),
  }
}

export const getHotspots = async (region = 'All') => {
  await delay(600)
  if (region === 'All') {
    return mockHotspots
  }
  return mockHotspots.filter((h) => h.region === region)
}

export const getRouteStatus = async (source, destination) => {
  await delay(1200)
  // Mock route data
  const segments = [
    { roadName: 'Road A', congestion: 'free', delay: 2 },
    { roadName: 'Road B', congestion: 'moderate', delay: 5 },
    { roadName: 'Road C', congestion: 'heavy', delay: 10 },
  ]
  return {
    distance: 12.5,
    estimatedTime: 25,
    segments,
    route: [
      [103.8419, 1.3048],
      [103.8425, 1.3055],
      [103.8430, 1.3062],
      [103.8435, 1.3068],
    ],
  }
}

export const submitIncident = async (incidentData) => {
  await delay(1000)
  return { success: true, id: `inc-${Date.now()}` }
}

export const submitFeedback = async (feedbackData) => {
  await delay(800)
  return { success: true, id: `fb-${Date.now()}` }
}

// Government API
export const getRegionData = async () => {
  await delay(1000)
  return mockRegionData
}

export const getIncidents = async () => {
  await delay(800)
  return mockIncidents
}

export const updateIncidentStatus = async (incidentId, status) => {
  await delay(600)
  return { success: true }
}

export const getAlerts = async () => {
  await delay(700)
  return mockAlerts
}

export const acknowledgeAlert = async (alertId) => {
  await delay(500)
  return { success: true }
}

export const createRoadwork = async (roadworkData) => {
  await delay(1000)
  return { success: true, id: `rw-${Date.now()}` }
}

// Developer API
export const getAlgorithms = async () => {
  await delay(800)
  return mockAlgorithms
}

export const updateAlgorithmStatus = async (algorithmId, status) => {
  await delay(600)
  return { success: true }
}

export const getPerformanceMetrics = async () => {
  await delay(1000)
  return {
    avgApiResponseTime: 245,
    dbQueryTime: 120,
    jobsQueued: 5,
    jobsRunning: 2,
    trends: [
      { time: '00:00', value: 200 },
      { time: '04:00', value: 180 },
      { time: '08:00', value: 250 },
      { time: '12:00', value: 300 },
      { time: '16:00', value: 280 },
      { time: '20:00', value: 220 },
    ],
  }
}

export const getRoles = async () => {
  await delay(700)
  return mockRoles
}

export const getAllFeedback = async () => {
  await delay(800)
  return mockFeedback
}

export const getUsers = async () => {
  await delay(700)
  return mockUsers
}

// Analyst API
export const runPreprocessing = async (datasetId) => {
  await delay(2000)
  return {
    success: true,
    logs: [
      'Loading dataset...',
      'Validating data format...',
      'Checking for missing values...',
      'Normalizing coordinates...',
      'Preprocessing complete!',
    ],
  }
}

export const runTrafficModel = async (modelConfig) => {
  await delay(1500)
  return {
    jobId: `job-${Date.now()}`,
    status: 'pending',
  }
}

export const getJobStatus = async (jobId) => {
  await delay(500)
  // Mock job progression
  return {
    jobId,
    status: 'completed',
    progress: 100,
    result: {
      model: 'Traffic Flow Prediction',
      accuracy: 0.92,
      predictions: 1500,
    },
  }
}

export const getHistoricalTrends = async (timescale, region) => {
  await delay(1000)
  return {
    congestionIndex: [
      { date: '2024-01-01', value: 0.5 },
      { date: '2024-01-02', value: 0.6 },
      { date: '2024-01-03', value: 0.4 },
      { date: '2024-01-04', value: 0.7 },
      { date: '2024-01-05', value: 0.5 },
    ],
    incidents: [
      { date: '2024-01-01', count: 10 },
      { date: '2024-01-02', count: 15 },
      { date: '2024-01-03', count: 8 },
      { date: '2024-01-04', count: 20 },
      { date: '2024-01-05', count: 12 },
    ],
  }
}

export const getSchedules = async () => {
  await delay(600)
  return mockSchedules
}

export const createSchedule = async (scheduleData) => {
  await delay(800)
  return { success: true, id: `sched-${Date.now()}` }
}

