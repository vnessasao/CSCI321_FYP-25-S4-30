/**
 * API service for Traffic Analysis authentication
 * Handles all API calls to the Flask backend
 */

// Use environment variable or default to production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://trafficanalysis.onrender.com/api'

class ApiService {
  /**
   * Make HTTP request to API endpoint
   */
  static async makeRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    }

    const config = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`)
      }

      return data
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  /**
   * Generic GET request
   */
  static async get(endpoint) {
    return this.makeRequest(endpoint, {
      method: 'GET'
    })
  }

  /**
   * Generic POST request
   */
  static async post(endpoint, data = {}) {
    return this.makeRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }
  
  /**
   * User signup
   */
  static async signup(userData) {
    return this.makeRequest('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        email: userData.email,
        password: userData.password,
        role: userData.role
      })
    })
  }
  
  /**
   * User login
   */
  static async login(credentials) {
    return this.makeRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
        role: credentials.role
      })
    })
  }
  
  /**
   * Verify JWT token
   */
  static async verifyToken(token) {
    return this.makeRequest('/auth/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token })
    })
  }
  
  /**
   * Make authenticated request with token
   */
  static async authenticatedRequest(endpoint, token, options = {}) {
    return this.makeRequest(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    })
  }

  /**
   * Submit incident report
   */
  static async submitIncident(incidentData, token) {
    return this.authenticatedRequest('/incidents', token, {
      method: 'POST',
      body: JSON.stringify(incidentData)
    })
  }

  /**
   * Get user's incidents
   */
  static async getUserIncidents(token) {
    return this.authenticatedRequest('/incidents', token, {
      method: 'GET'
    })
  }

  /**
   * Get specific incident by ID
   */
  static async getIncident(incidentId, token) {
    return this.authenticatedRequest(`/incidents/${incidentId}`, token, {
      method: 'GET'
    })
  }

  /**
   * Search for locations in Singapore (for autocomplete)
   */
  static async searchLocations(query) {
    return this.makeRequest(`/traffic/search?query=${encodeURIComponent(query)}`, {
      method: 'GET'
    })
  }

  /**
   * Get route with real-time traffic data
   */
  static async getRouteTraffic(start, end) {
    return this.makeRequest('/traffic/route', {
      method: 'POST',
      body: JSON.stringify({ start, end })
    })
  }

  /**
   * Get current traffic speed bands (for debugging/testing)
   */
  static async getSpeedBands() {
    return this.makeRequest('/traffic/speed-bands', {
      method: 'GET'
    })
  }

  // ========== Upload Session Management ==========

  /**
   * Create a new upload session
   */
  static async createUploadSession() {
    const token = localStorage.getItem('auth_token')
    return this.authenticatedRequest('/upload/create-session', token, {
      method: 'POST'
    })
  }

  /**
   * Upload road network GeoJSON file
   */
  static async uploadRoadNetwork(sessionId, file) {
    const token = localStorage.getItem('auth_token')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)

    return fetch(`${API_BASE_URL}/upload/road-network`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }).then(response => response.json())
  }

  /**
   * Upload GPS trajectories CSV file
   */
  static async uploadGpsTrajectories(sessionId, file) {
    const token = localStorage.getItem('auth_token')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)

    return fetch(`${API_BASE_URL}/upload/gps-trajectories`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }).then(response => response.json())
  }

  /**
   * Trigger data preprocessing
   */
  static async preprocessData(sessionId) {
    const token = localStorage.getItem('auth_token')
    return this.authenticatedRequest('/upload/preprocess', token, {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId })
    })
  }

  /**
   * Get session status
   */
  static async getSessionStatus(sessionId) {
    return this.makeRequest(`/upload/session-status/${sessionId}`, {
      method: 'GET'
    })
  }

  /**
   * Get active session information
   */
  static async getActiveSessionInfo() {
    return this.makeRequest('/upload/active-session-info', {
      method: 'GET'
    })
  }

  /**
   * Restore pre-inserted (sample) data session
   */
  static async restorePreinsertedData() {
    const token = localStorage.getItem('auth_token')
    return this.authenticatedRequest('/upload/restore-preinserted', token, {
      method: 'POST'
    })
  }

  /**
   * Get upload status (legacy)
   */
  static async getUploadStatus() {
    return this.makeRequest('/upload/status', {
      method: 'GET'
    })
  }

  // ========== Bottleneck Analysis ==========

  /**
   * Run bottleneck analysis model
   */
  static async runBottleneckModel(sessionId, k, timeHorizon, modelType = 'LIM') {
    return this.makeRequest('/bottlenecks/run-model', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        k: k,
        time_horizon: timeHorizon,
        model_type: modelType
      })
    })
  }

  /**
   * Get top K bottlenecks (cached or calculate)
   */
  static async getTopBottlenecks(k = 10, timeHorizon = 30, modelType = 'LIM', forceRecalculate = false) {
    return this.makeRequest(
      `/bottlenecks/top-k?k=${k}&time_horizon=${timeHorizon}&model_type=${modelType}&force=${forceRecalculate}`,
      { method: 'GET' }
    )
  }

  /**
   * Calculate bottlenecks
   */
  static async calculateBottlenecks(k = 10, timeHorizon = 30, modelType = 'LIM') {
    return this.makeRequest('/bottlenecks/calculate', {
      method: 'POST',
      body: JSON.stringify({
        k: k,
        time_horizon: timeHorizon,
        model_type: modelType
      })
    })
  }

  /**
   * Perform what-if analysis
   */
  static async whatIfAnalysis(fixedRoads, timeHorizon = 30, modelType = 'LIM') {
    return this.makeRequest('/bottlenecks/what-if', {
      method: 'POST',
      body: JSON.stringify({
        fixed_roads: fixedRoads,
        time_horizon: timeHorizon,
        model_type: modelType
      })
    })
  }

  /**
   * Learn influence probabilities
   */
  static async learnInfluenceProbabilities(timeHorizons = [5, 15, 30], modelType = 'LIM') {
    return this.makeRequest('/bottlenecks/learn-influence', {
      method: 'POST',
      body: JSON.stringify({
        time_horizons: timeHorizons,
        model_type: modelType
      })
    })
  }

  /**
   * Get influence flows for visualization (animated lines showing how congestion spreads)
   */
  static async getInfluenceFlows(timeHorizon = 30, minProbability = 0.3) {
    return this.makeRequest(
      `/bottlenecks/influence-flows?time_horizon=${timeHorizon}&min_probability=${minProbability}`,
      { method: 'GET' }
    )
  }

  /**
   * Get bottleneck impacts (which roads are affected by each bottleneck)
   */
  static async getBottleneckImpacts(timeHorizon = 30, bottleneckId = null) {
    const params = `time_horizon=${timeHorizon}${bottleneckId ? `&bottleneck_id=${bottleneckId}` : ''}`
    return this.makeRequest(
      `/bottlenecks/bottleneck-impacts?${params}`,
      { method: 'GET' }
    )
  }

  // ========== Bookmarks ==========

  /**
   * Get all bookmarks for the authenticated user
   */
  static async getBookmarks(token) {
    return this.authenticatedRequest('/bookmarks', token, {
      method: 'GET'
    })
  }

  /**
   * Add a new bookmark
   */
  static async addBookmark(bookmarkData, token) {
    return this.authenticatedRequest('/bookmarks', token, {
      method: 'POST',
      body: JSON.stringify({
        name: bookmarkData.name,
        latitude: bookmarkData.latitude,
        longitude: bookmarkData.longitude,
        address: bookmarkData.address || '',
        notes: bookmarkData.notes || ''
      })
    })
  }

  /**
   * Delete a bookmark by ID
   */
  static async deleteBookmark(bookmarkId, token) {
    return this.authenticatedRequest(`/bookmarks/${bookmarkId}`, token, {
      method: 'DELETE'
    })
  }

  /**
   * Check if a location is already bookmarked
   */
  static async checkBookmark(latitude, longitude, token) {
    return this.authenticatedRequest('/bookmarks/check', token, {
      method: 'POST',
      body: JSON.stringify({ latitude, longitude })
    })
  }

  // ========== Route Bookmarks ==========

  /**
   * Get all route bookmarks for the authenticated user
   */
  static async getRouteBookmarks(token) {
    return this.authenticatedRequest('/route-bookmarks', token, {
      method: 'GET'
    })
  }

  /**
   * Add a new route bookmark
   */
  static async addRouteBookmark(routeData, token) {
    return this.authenticatedRequest('/route-bookmarks', token, {
      method: 'POST',
      body: JSON.stringify({
        name: routeData.name,
        start: routeData.start,
        end: routeData.end,
        notes: routeData.notes || '',
        is_favorite: routeData.is_favorite || false
      })
    })
  }

  /**
   * Delete a route bookmark by ID
   */
  static async deleteRouteBookmark(routeId, token) {
    return this.authenticatedRequest(`/route-bookmarks/${routeId}`, token, {
      method: 'DELETE'
    })
  }

  /**
   * Toggle favorite status of a route bookmark
   */
  static async toggleRouteFavorite(routeId, token) {
    return this.authenticatedRequest(`/route-bookmarks/${routeId}/favorite`, token, {
      method: 'PATCH'
    })
  }

  // ========== Historical Trends ==========

  /**
   * Get historical traffic trends
   * @param {Object} params - { timescale, date_from, date_to, region, session_id }
   */
  static async getHistoricalTrends(params = {}) {
    const queryParams = new URLSearchParams()
    if (params.timescale) queryParams.append('timescale', params.timescale)
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.region) queryParams.append('region', params.region)
    if (params.session_id) queryParams.append('session_id', params.session_id)

    return this.makeRequest(`/trends/historical?${queryParams.toString()}`, {
      method: 'GET'
    })
  }

  /**
   * Get traffic hotspots
   */
  static async getHotspots(params = {}) {
    const queryParams = new URLSearchParams()
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.region) queryParams.append('region', params.region)

    return this.makeRequest(`/trends/hotspots?${queryParams.toString()}`, {
      method: 'GET'
    })
  }

  /**
   * Get available regions
   */
  static async getRegions() {
    return this.makeRequest('/trends/regions', { method: 'GET' })
  }

  /**
   * Get road details with history
   */
  static async getRoadDetails(roadId, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.timescale) queryParams.append('timescale', params.timescale)

    return this.makeRequest(`/trends/road-details/${roadId}?${queryParams.toString()}`, {
      method: 'GET'
    })
  }

  /**
   * Get traffic summary
   */
  static async getTrafficSummary() {
    return this.makeRequest('/trends/summary', { method: 'GET' })
  }

  // ========== User Management (Admin) ==========

  /**
   * List all users (admin only)
   */
  static async getUsers(token, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.role) queryParams.append('role', params.role)
    if (params.status) queryParams.append('status', params.status)
    if (params.page) queryParams.append('page', params.page)
    if (params.limit) queryParams.append('limit', params.limit)

    return this.authenticatedRequest(`/users/?${queryParams.toString()}`, token, {
      method: 'GET'
    })
  }

  /**
   * Get a specific user
   */
  static async getUser(userId, token) {
    return this.authenticatedRequest(`/users/${userId}`, token, {
      method: 'GET'
    })
  }

  /**
   * Create a new user (admin only)
   */
  static async createUser(userData, token) {
    return this.authenticatedRequest('/users/', token, {
      method: 'POST',
      body: JSON.stringify(userData)
    })
  }

  /**
   * Update a user
   */
  static async updateUser(userId, userData, token) {
    return this.authenticatedRequest(`/users/${userId}`, token, {
      method: 'PUT',
      body: JSON.stringify(userData)
    })
  }

  /**
   * Suspend or unsuspend a user
   */
  static async suspendUser(userId, suspend, reason, token) {
    return this.authenticatedRequest(`/users/${userId}/suspend`, token, {
      method: 'PUT',
      body: JSON.stringify({ suspend, reason })
    })
  }

  /**
   * Delete (deactivate) a user
   */
  static async deleteUser(userId, token) {
    return this.authenticatedRequest(`/users/${userId}`, token, {
      method: 'DELETE'
    })
  }

  /**
   * Get user statistics
   */
  static async getUserStats(token) {
    return this.authenticatedRequest('/users/stats', token, {
      method: 'GET'
    })
  }

  // ========== Algorithm Management ==========

  /**
   * List all algorithms
   */
  static async getAlgorithms(token) {
    return this.authenticatedRequest('/algorithms/', token, { method: 'GET' })
  }

  /**
   * Get a specific algorithm
   */
  static async getAlgorithm(algorithmId, token) {
    return this.authenticatedRequest(`/algorithms/${algorithmId}`, token, { method: 'GET' })
  }

  /**
   * List only active algorithms
   */
  static async getActiveAlgorithms(token) {
    return this.authenticatedRequest('/algorithms/active', token, { method: 'GET' })
  }

  /**
   * Suspend an algorithm (developer only)
   */
  static async suspendAlgorithm(algorithmId, reason, token) {
    return this.authenticatedRequest(`/algorithms/${algorithmId}/suspend`, token, {
      method: 'PUT',
      body: JSON.stringify({ reason })
    })
  }

  /**
   * Activate an algorithm (developer only)
   */
  static async activateAlgorithm(algorithmId, token) {
    return this.authenticatedRequest(`/algorithms/${algorithmId}/activate`, token, {
      method: 'PUT'
    })
  }

  /**
   * Update algorithm parameters (developer only)
   */
  static async updateAlgorithmParameters(algorithmId, parameters, token) {
    return this.authenticatedRequest(`/algorithms/${algorithmId}/parameters`, token, {
      method: 'PUT',
      body: JSON.stringify({ parameters })
    })
  }

  /**
   * Get algorithm statistics
   */
  static async getAlgorithmStats(token) {
    return this.authenticatedRequest('/algorithms/stats', token, { method: 'GET' })
  }

  // ========== Traffic Map with Region Filter ==========

  /**
   * Get traffic map data with optional region filter
   */
  static async getTrafficMap(region = null) {
    const params = region ? `?region=${encodeURIComponent(region)}` : ''
    return this.makeRequest(`/lta/traffic-map${params}`, { method: 'GET' })
  }

  // ========== Jam Prediction API ==========

  /**
   * Get jam prediction for all roads
   * @param {number} horizonMinutes - Prediction horizon in minutes (default 30)
   * @param {string} region - Region filter (North, South, East, West, Central, or null for all)
   */
  static async getJamPrediction(horizonMinutes = 30, region = null) {
    const params = region ? `?horizon=${horizonMinutes}&region=${region}` : `?horizon=${horizonMinutes}`;
    return this.makeRequest(`/jam-prediction/predict${params}`, {
      method: 'GET'
    })
  }

  /**
   * Get prediction for specific links
   * @param {Array<string>} linkIds - Array of link IDs to predict
   * @param {number} horizonMinutes - Prediction horizon in minutes
   */
  static async getPredictionForLinks(linkIds, horizonMinutes = 30) {
    return this.makeRequest('/jam-prediction/predict-links', {
      method: 'POST',
      body: JSON.stringify({
        link_ids: linkIds,
        horizon: horizonMinutes
      })
    })
  }

  // ========== Weather API (Phase 2) ==========

  /**
   * Get current 2-hour weather forecast
   */
  static async getCurrentWeather() {
    return this.makeRequest('/weather/current', { method: 'GET' })
  }

  /**
   * Get 24-hour weather forecast
   */
  static async get24HourForecast() {
    return this.makeRequest('/weather/forecast/24h', { method: 'GET' })
  }

  /**
   * Get 4-day weather forecast
   */
  static async get4DayForecast() {
    return this.makeRequest('/weather/forecast/4day', { method: 'GET' })
  }

  /**
   * Get rainfall readings
   */
  static async getRainfall() {
    return this.makeRequest('/weather/rainfall', { method: 'GET' })
  }

  /**
   * Get temperature readings
   */
  static async getTemperature() {
    return this.makeRequest('/weather/temperature', { method: 'GET' })
  }

  /**
   * Get air quality (PSI and PM2.5)
   */
  static async getAirQuality() {
    return this.makeRequest('/weather/air-quality', { method: 'GET' })
  }

  /**
   * Get combined weather data for overlay
   */
  static async getCombinedWeather(region = 'All') {
    const params = region !== 'All' ? `?region=${encodeURIComponent(region)}` : ''
    return this.makeRequest(`/weather/combined${params}`, { method: 'GET' })
  }

  /**
   * Get weather monitoring areas
   */
  static async getWeatherAreas() {
    return this.makeRequest('/weather/areas', { method: 'GET' })
  }

  // ========== Transport API (Phase 2) ==========

  /**
   * Get MRT stations
   */
  static async getMrtStations(line = 'All') {
    const params = line !== 'All' ? `?line=${encodeURIComponent(line)}` : ''
    return this.makeRequest(`/transport/mrt/stations${params}`, { method: 'GET' })
  }

  /**
   * Get MRT line information
   */
  static async getMrtLines() {
    return this.makeRequest('/transport/lines', { method: 'GET' })
  }

  /**
   * Get train service alerts
   */
  static async getTrainAlerts() {
    return this.makeRequest('/transport/mrt/alerts', { method: 'GET' })
  }

  /**
   * Get bus stops with optional bounds filtering
   */
  static async getBusStops(bounds = null) {
    let params = ''
    if (bounds) {
      params = `?lat_min=${bounds.latMin}&lat_max=${bounds.latMax}&lon_min=${bounds.lonMin}&lon_max=${bounds.lonMax}`
    }
    return this.makeRequest(`/transport/bus/stops${params}`, { method: 'GET' })
  }

  /**
   * Get bus arrival times for a stop
   */
  static async getBusArrival(busStopCode) {
    return this.makeRequest(`/transport/bus/arrival?bus_stop_code=${busStopCode}`, { method: 'GET' })
  }

  /**
   * Get taxi availability
   */
  static async getTaxiAvailability() {
    return this.makeRequest('/transport/taxi/availability', { method: 'GET' })
  }

  /**
   * Get combined transport data for overlay
   */
  static async getCombinedTransport(lat = 1.3521, lon = 103.8198, radiusKm = 2) {
    return this.makeRequest(
      `/transport/combined?lat=${lat}&lon=${lon}&radius=${radiusKm}`,
      { method: 'GET' }
    )
  }

  // ========== Schedules API (Phase 3) ==========

  /**
   * List schedules
   */
  static async getSchedules(token, showAll = false) {
    return this.authenticatedRequest(`/schedules/?all=${showAll}`, token, { method: 'GET' })
  }

  /**
   * Get a specific schedule
   */
  static async getSchedule(scheduleId, token) {
    return this.authenticatedRequest(`/schedules/${scheduleId}`, token, { method: 'GET' })
  }

  /**
   * Create a new schedule
   */
  static async createSchedule(scheduleData, token) {
    return this.authenticatedRequest('/schedules/', token, {
      method: 'POST',
      body: JSON.stringify(scheduleData)
    })
  }

  /**
   * Update a schedule
   */
  static async updateSchedule(scheduleId, scheduleData, token) {
    return this.authenticatedRequest(`/schedules/${scheduleId}`, token, {
      method: 'PUT',
      body: JSON.stringify(scheduleData)
    })
  }

  /**
   * Delete a schedule
   */
  static async deleteSchedule(scheduleId, token) {
    return this.authenticatedRequest(`/schedules/${scheduleId}`, token, { method: 'DELETE' })
  }

  /**
   * Toggle schedule active status
   */
  static async toggleSchedule(scheduleId, token) {
    return this.authenticatedRequest(`/schedules/${scheduleId}/toggle`, token, { method: 'PUT' })
  }

  /**
   * Run a schedule immediately
   */
  static async runScheduleNow(scheduleId, token) {
    return this.authenticatedRequest(`/schedules/${scheduleId}/run`, token, { method: 'POST' })
  }

  /**
   * Get schedule statistics
   */
  static async getScheduleStats(token) {
    return this.authenticatedRequest('/schedules/stats', token, { method: 'GET' })
  }

  /**
   * Get frequency presets
   */
  static async getFrequencyPresets() {
    return this.makeRequest('/schedules/frequencies', { method: 'GET' })
  }

  // ========== Anomalies API (Phase 3) ==========

  /**
   * Run anomaly detection
   */
  static async detectAnomalies(params, token) {
    return this.authenticatedRequest('/anomalies/detect', token, {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  /**
   * List detected anomalies
   */
  static async getAnomalies(token, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.severity) queryParams.append('severity', params.severity)
    // Support both naming conventions
    const anomalyType = params.type || params.anomaly_type
    if (anomalyType) queryParams.append('type', anomalyType)
    const confirmed = params.confirmed !== undefined ? params.confirmed : params.is_confirmed
    if (confirmed !== undefined && confirmed !== '') queryParams.append('confirmed', confirmed)
    const resolved = params.resolved !== undefined ? params.resolved : params.is_resolved
    if (resolved !== undefined && resolved !== '') queryParams.append('resolved', resolved)
    if (params.limit) queryParams.append('limit', params.limit)
    // Support both offset and page-based pagination
    if (params.offset) queryParams.append('offset', params.offset)
    else if (params.page) queryParams.append('offset', (params.page - 1) * (params.limit || 20))

    return this.authenticatedRequest(`/anomalies/?${queryParams.toString()}`, token, { method: 'GET' })
  }

  /**
   * Get a specific anomaly
   */
  static async getAnomaly(anomalyId, token) {
    return this.authenticatedRequest(`/anomalies/${anomalyId}`, token, { method: 'GET' })
  }

  /**
   * Confirm an anomaly
   */
  static async confirmAnomaly(anomalyId, token) {
    return this.authenticatedRequest(`/anomalies/${anomalyId}/confirm`, token, { method: 'PUT' })
  }

  /**
   * Resolve an anomaly
   */
  static async resolveAnomaly(anomalyId, notes, token) {
    return this.authenticatedRequest(`/anomalies/${anomalyId}/resolve`, token, {
      method: 'PUT',
      body: JSON.stringify({ notes })
    })
  }

  /**
   * Get anomaly statistics
   */
  static async getAnomalyStats(token) {
    return this.authenticatedRequest('/anomalies/stats', token, { method: 'GET' })
  }

  /**
   * Get real-time anomalies (public)
   */
  static async getRealtimeAnomalies() {
    return this.makeRequest('/anomalies/realtime', { method: 'GET' })
  }

  // ========== Logs API (Phase 4) ==========

  /**
   * List system logs
   */
  static async getLogs(token, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.level) queryParams.append('level', params.level)
    if (params.source) queryParams.append('source', params.source)
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.search) queryParams.append('search', params.search)
    if (params.flagged_only) queryParams.append('flagged_only', params.flagged_only)
    if (params.unresolved_only) queryParams.append('unresolved_only', params.unresolved_only)

    return this.authenticatedRequest(`/logs/?${queryParams.toString()}`, token, { method: 'GET' })
  }

  /**
   * Get a specific log entry
   */
  static async getLog(logId, token) {
    return this.authenticatedRequest(`/logs/${logId}`, token, { method: 'GET' })
  }

  /**
   * Flag a log entry
   */
  static async flagLog(logId, token) {
    return this.authenticatedRequest(`/logs/${logId}/flag`, token, { method: 'PUT' })
  }

  /**
   * Unflag a log entry
   */
  static async unflagLog(logId, token) {
    return this.authenticatedRequest(`/logs/${logId}/unflag`, token, { method: 'PUT' })
  }

  /**
   * Resolve a flagged log
   */
  static async resolveLog(logId, notes, token) {
    return this.authenticatedRequest(`/logs/${logId}/resolve`, token, {
      method: 'PUT',
      body: JSON.stringify({ notes })
    })
  }

  /**
   * Get log statistics
   */
  static async getLogStats(token) {
    return this.authenticatedRequest('/logs/stats', token, { method: 'GET' })
  }

  /**
   * Get log levels
   */
  static async getLogLevels() {
    return this.makeRequest('/logs/levels', { method: 'GET' })
  }

  /**
   * Get log sources
   */
  static async getLogSources() {
    return this.makeRequest('/logs/sources', { method: 'GET' })
  }

  // ========== Permissions API (Phase 4) ==========

  /**
   * List all permissions
   */
  static async getPermissions(token, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.category) queryParams.append('category', params.category)
    if (params.active_only) queryParams.append('active_only', params.active_only)

    return this.authenticatedRequest(`/permissions/?${queryParams.toString()}`, token, { method: 'GET' })
  }

  /**
   * Get a specific permission
   */
  static async getPermission(permissionId, token) {
    return this.authenticatedRequest(`/permissions/${permissionId}`, token, { method: 'GET' })
  }

  /**
   * Create a new permission
   */
  static async createPermission(permissionData, token) {
    return this.authenticatedRequest('/permissions/', token, {
      method: 'POST',
      body: JSON.stringify(permissionData)
    })
  }

  /**
   * Update a permission
   */
  static async updatePermission(permissionId, permissionData, token) {
    return this.authenticatedRequest(`/permissions/${permissionId}`, token, {
      method: 'PUT',
      body: JSON.stringify(permissionData)
    })
  }

  /**
   * Suspend a permission
   */
  static async suspendPermission(permissionId, reason, token) {
    return this.authenticatedRequest(`/permissions/${permissionId}/suspend`, token, {
      method: 'PUT',
      body: JSON.stringify({ reason })
    })
  }

  /**
   * Activate a permission
   */
  static async activatePermission(permissionId, token) {
    return this.authenticatedRequest(`/permissions/${permissionId}/activate`, token, { method: 'PUT' })
  }

  /**
   * Delete a permission
   */
  static async deletePermission(permissionId, token) {
    return this.authenticatedRequest(`/permissions/${permissionId}`, token, { method: 'DELETE' })
  }

  /**
   * List roles with permissions
   */
  static async getRolesWithPermissions(token) {
    return this.authenticatedRequest('/permissions/roles', token, { method: 'GET' })
  }

  /**
   * Get permissions for a specific role
   */
  static async getRolePermissions(role, token) {
    return this.authenticatedRequest(`/permissions/roles/${role}`, token, { method: 'GET' })
  }

  /**
   * Update role permissions
   */
  static async updateRolePermissions(role, permissionIds, token) {
    return this.authenticatedRequest(`/permissions/roles/${role}`, token, {
      method: 'PUT',
      body: JSON.stringify({ permission_ids: permissionIds })
    })
  }

  /**
   * Add permission to role
   */
  static async addPermissionToRole(role, permissionId, token) {
    return this.authenticatedRequest(`/permissions/roles/${role}/add`, token, {
      method: 'POST',
      body: JSON.stringify({ permission_id: permissionId })
    })
  }

  /**
   * Remove permission from role
   */
  static async removePermissionFromRole(role, permissionId, token) {
    return this.authenticatedRequest(`/permissions/roles/${role}/remove`, token, {
      method: 'POST',
      body: JSON.stringify({ permission_id: permissionId })
    })
  }

  /**
   * Get permission categories
   */
  static async getPermissionCategories() {
    return this.makeRequest('/permissions/categories', { method: 'GET' })
  }

  // ========== Feedback API (Phase 4) ==========

  /**
   * List all feedback (admin)
   */
  static async getAllFeedback(token, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.category) queryParams.append('category', params.category)
    if (params.status) queryParams.append('status', params.status)
    if (params.rating) queryParams.append('rating', params.rating)

    return this.authenticatedRequest(`/feedback/?${queryParams.toString()}`, token, { method: 'GET' })
  }

  /**
   * Get a specific feedback entry
   */
  static async getFeedback(feedbackId, token) {
    return this.authenticatedRequest(`/feedback/${feedbackId}`, token, { method: 'GET' })
  }

  /**
   * Submit feedback (public)
   */
  static async submitFeedback(feedbackData, token = null) {
    if (token) {
      return this.authenticatedRequest('/feedback/', token, {
        method: 'POST',
        body: JSON.stringify(feedbackData)
      })
    }
    return this.makeRequest('/feedback/', {
      method: 'POST',
      body: JSON.stringify(feedbackData)
    })
  }

  /**
   * Respond to feedback
   */
  static async respondToFeedback(feedbackId, response, token) {
    return this.authenticatedRequest(`/feedback/${feedbackId}/respond`, token, {
      method: 'PUT',
      body: JSON.stringify({ response })
    })
  }

  /**
   * Update feedback status
   */
  static async updateFeedbackStatus(feedbackId, status, token) {
    return this.authenticatedRequest(`/feedback/${feedbackId}/status`, token, {
      method: 'PUT',
      body: JSON.stringify({ status })
    })
  }

  /**
   * Update feedback content (SD-19)
   */
  static async updateFeedback(feedbackId, feedbackData, token) {
    return this.authenticatedRequest(`/feedback/${feedbackId}`, token, {
      method: 'PUT',
      body: JSON.stringify(feedbackData)
    })
  }

  /**
   * Broadcast an existing feedback item
   */
  static async broadcastExistingFeedback(feedbackId, message, token) {
    return this.authenticatedRequest(`/feedback/${feedbackId}/broadcast`, token, {
      method: 'POST',
      body: JSON.stringify({ message })
    })
  }

  /**
   * Create a new broadcast message
   */
  static async broadcastFeedback(broadcastData, token) {
    return this.authenticatedRequest('/feedback/broadcast', token, {
      method: 'POST',
      body: JSON.stringify(broadcastData)
    })
  }

  /**
   * Get broadcast messages (public)
   */
  static async getBroadcasts(limit = 10) {
    return this.makeRequest(`/feedback/broadcasts?limit=${limit}`, { method: 'GET' })
  }

  /**
   * Get feedback statistics
   */
  static async getFeedbackStats(token) {
    return this.authenticatedRequest('/feedback/stats', token, { method: 'GET' })
  }

  /**
   * Get feedback categories
   */
  static async getFeedbackCategories() {
    return this.makeRequest('/feedback/categories', { method: 'GET' })
  }

  /**
   * Get feedback statuses
   */
  static async getFeedbackStatuses() {
    return this.makeRequest('/feedback/statuses', { method: 'GET' })
  }

  /**
   * Get current user's feedback submissions
   */
  static async getMyFeedback(token) {
    return this.authenticatedRequest('/feedback/my-feedback', token, { method: 'GET' })
  }

  /**
   * Delete feedback
   */
  static async deleteFeedback(feedbackId, token) {
    return this.authenticatedRequest(`/feedback/${feedbackId}`, token, { method: 'DELETE' })
  }

  // ========== Backups API (Phase 4) ==========

  /**
   * List all backups
   */
  static async getBackups(token) {
    return this.authenticatedRequest('/backups/', token, { method: 'GET' })
  }

  /**
   * Get a specific backup
   */
  static async getBackup(backupId, token) {
    return this.authenticatedRequest(`/backups/${backupId}`, token, { method: 'GET' })
  }

  /**
   * Create a new backup
   */
  static async createBackup(backupData, token) {
    return this.authenticatedRequest('/backups/', token, {
      method: 'POST',
      body: JSON.stringify(backupData)
    })
  }

  /**
   * Download a backup file
   */
  static async downloadBackup(backupId, token) {
    const url = `${API_BASE_URL}/backups/${backupId}/download`
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to download backup')
    }

    return response.blob()
  }

  /**
   * Restore from a backup
   */
  static async restoreBackup(backupId, token) {
    return this.authenticatedRequest(`/backups/${backupId}/restore`, token, {
      method: 'POST',
      body: JSON.stringify({ confirm: true })
    })
  }

  /**
   * Delete a backup
   */
  static async deleteBackup(backupId, hardDelete, token) {
    return this.authenticatedRequest(`/backups/${backupId}`, token, {
      method: 'DELETE',
      body: JSON.stringify({ hard_delete: hardDelete })
    })
  }

  /**
   * Get backup statistics
   */
  static async getBackupStats(token) {
    return this.authenticatedRequest('/backups/stats', token, { method: 'GET' })
  }

  /**
   * Get available tables for backup
   */
  static async getBackupTables(token) {
    return this.authenticatedRequest('/backups/tables', token, { method: 'GET' })
  }

  // ========== Notifications ==========

  /**
   * Get notification count
   */
  static async getNotificationCount(token) {
    return this.authenticatedRequest('/feedback/notifications/count', token, {
      method: 'GET'
    })
  }

  /**
   * Mark all notifications as read
   */
  static async markNotificationsRead(token) {
    return this.authenticatedRequest('/feedback/notifications/mark-read', token, {
      method: 'POST'
    })
  }

  // ========== Roadwork API (Phase 5 - Government) ==========

  /**
   * Get all roadwork events
   */
  static async getRoadworkEvents(token, status = 'all') {
    const params = status !== 'all' ? `?status=${status}` : ''
    return this.authenticatedRequest(`/roadwork${params}`, token, { method: 'GET' })
  }

  /**
   * Create a new roadwork event
   */
  static async createRoadworkEvent(eventData, token) {
    return this.authenticatedRequest('/roadwork', token, {
      method: 'POST',
      body: JSON.stringify(eventData)
    })
  }

  /**
   * Update a roadwork event
   */
  static async updateRoadworkEvent(eventId, eventData, token) {
    return this.authenticatedRequest(`/roadwork/${eventId}`, token, {
      method: 'PUT',
      body: JSON.stringify(eventData)
    })
  }

  /**
   * Delete a roadwork event
   */
  static async deleteRoadworkEvent(eventId, token) {
    return this.authenticatedRequest(`/roadwork/${eventId}`, token, { method: 'DELETE' })
  }

  // ========== EMAS API (Phase 5 - Government) ==========

  /**
   * Get all EMAS incidents
   */
  static async getEmasIncidents(token, status = 'all') {
    const params = status !== 'all' ? `?status=${status}` : ''
    return this.authenticatedRequest(`/emas/incidents${params}`, token, { method: 'GET' })
  }

  /**
   * Create a new EMAS incident
   */
  static async createEmasIncident(incidentData, token) {
    return this.authenticatedRequest('/emas/incidents', token, {
      method: 'POST',
      body: JSON.stringify(incidentData)
    })
  }

  /**
   * Update EMAS incident status
   */
  static async updateEmasStatus(incidentId, status, token) {
    return this.authenticatedRequest(`/emas/incidents/${incidentId}/status`, token, {
      method: 'PUT',
      body: JSON.stringify({ status })
    })
  }

  /**
   * Delete an EMAS incident
   */
  static async deleteEmasIncident(incidentId, token) {
    return this.authenticatedRequest(`/emas/incidents/${incidentId}`, token, { method: 'DELETE' })
  }
}

export default ApiService