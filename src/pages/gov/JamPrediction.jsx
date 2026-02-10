import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import 'leaflet/dist/leaflet.css'

const JamPrediction = () => {
  // State management
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(false)
  const [timeHorizon, setTimeHorizon] = useState(30)
  const [modelType, setModelType] = useState('LIM')
  const [mapCenter, setMapCenter] = useState([1.3521, 103.8198]) // Singapore
  const [mapZoom, setMapZoom] = useState(12)
  const [statistics, setStatistics] = useState(null)
  const [activeAlgorithms, setActiveAlgorithms] = useState([])
  const [loadingAlgorithms, setLoadingAlgorithms] = useState(true)

  // Fetch active algorithms on mount
  useEffect(() => {
    const fetchActiveAlgorithms = async () => {
      try {
        const response = await ApiService.get('/algorithms/active')
        if (response.success && response.algorithms) {
          // Filter to exclude Greedy Bottleneck Finder (only show spread models)
          const spreadModels = response.algorithms.filter(algo => algo.name !== 'GREEDY')
          setActiveAlgorithms(spreadModels)
          // Set default model to first active algorithm if current is not active
          if (spreadModels.length > 0) {
            const currentIsActive = spreadModels.some(a => a.name === modelType)
            if (!currentIsActive) {
              setModelType(spreadModels[0].name)
            }
          }
        }
      } catch (error) {
        console.error('Error fetching active algorithms:', error)
        toast.error('Failed to load active algorithms')
      } finally {
        setLoadingAlgorithms(false)
      }
    }

    fetchActiveAlgorithms()
  }, [])

  // Load predictions on mount
  useEffect(() => {
    // This page will be enhanced with prediction functionality
    // For now, show a placeholder
  }, [])

  // Run prediction
  const handleRunPrediction = async () => {
    setLoading(true)

    try {
      toast.info('Running jam spread prediction...')

      const response = await ApiService.post('/jam-prediction/predict', {
        time_horizon: timeHorizon,
        model_type: modelType
      })

      if (response.success) {
        setPredictions(response.predictions)
        setStatistics(response.statistics)
        toast.success(`Prediction complete! Found ${response.predictions.length} road segments.`)
      } else {
        toast.error(response.error || 'Failed to run prediction')
      }

    } catch (error) {
      console.error('Prediction error:', error)
      toast.error(error.message || 'Failed to run prediction')
    } finally {
      setLoading(false)
    }
  }

  // Get risk level color
  const getRiskColor = (probability) => {
    if (probability >= 0.7) return '#DC2626' // Red - High risk
    if (probability >= 0.3) return '#F97316' // Orange - Medium risk
    return '#84CC16' // Green - Low risk
  }

  // Get risk level label
  const getRiskLevel = (probability) => {
    if (probability >= 0.7) return 'High'
    if (probability >= 0.3) return 'Medium'
    return 'Low'
  }

  // Extract coordinates from prediction (handles both geometry and coordinates format)
  const getCoordinates = (prediction) => {
    // If coordinates object exists (legacy format)
    if (prediction.coordinates && prediction.coordinates.lat !== undefined) {
      return [prediction.coordinates.lat, prediction.coordinates.lon]
    }
    // If geometry exists (GeoJSON format)
    if (prediction.geometry && prediction.geometry.coordinates) {
      const coords = prediction.geometry.coordinates
      if (prediction.geometry.type === 'LineString' && coords.length > 0) {
        // Get midpoint of the line
        const midIndex = Math.floor(coords.length / 2)
        const [lon, lat] = coords[midIndex]
        return [lat, lon]
      } else if (prediction.geometry.type === 'Point') {
        const [lon, lat] = coords
        return [lat, lon]
      }
    }
    // Fallback to Singapore center
    return [1.3521, 103.8198]
  }

  return (
    <div className="space-y-6">
      <ToastContainer />

      {/* Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Jam Spread Prediction
            </h2>
          </div>
        </div>
      </Card>

      {/* Controls */}
      <Card>
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-900">Prediction Parameters</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Time Horizon */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Horizon
              </label>
              <select
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
                <option value={120}>2 hours</option>
                <option value={720}>12 hours (Half Day)</option>
                <option value={1440}>24 hours (Full Day)</option>
              </select>
            </div>

            {/* Model Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model Type
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loadingAlgorithms || activeAlgorithms.length === 0}
              >
                {loadingAlgorithms ? (
                  <option>Loading algorithms...</option>
                ) : activeAlgorithms.length === 0 ? (
                  <option>No active algorithms available</option>
                ) : (
                  activeAlgorithms.map((algo) => (
                    <option key={algo.id} value={algo.name}>
                      {algo.display_name}
                    </option>
                  ))
                )}
              </select>
              {!loadingAlgorithms && activeAlgorithms.length === 0 && (
                <p className="text-sm text-red-600 mt-1">
                  No algorithms are currently active. Please activate algorithms in the management page.
                </p>
              )}
            </div>
          </div>

          <Button onClick={handleRunPrediction} disabled={loading || loadingAlgorithms || activeAlgorithms.length === 0} className="w-full">
            {loading ? 'Running Prediction...' : 'Run Prediction'}
          </Button>
        </div>
      </Card>

      {/* Statistics Card */}
      {statistics && (
        <Card>
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900">Prediction Statistics</h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Total Roads</div>
                <div className="text-2xl font-bold text-gray-900">{statistics.total_roads}</div>
              </div>

              <div className="bg-red-50 rounded-lg p-4">
                <div className="text-sm text-red-600 mb-1">High Risk</div>
                <div className="text-2xl font-bold text-red-600">{statistics.high_risk_roads}</div>
              </div>

              <div className="bg-orange-50 rounded-lg p-4">
                <div className="text-sm text-orange-600 mb-1">Medium Risk</div>
                <div className="text-2xl font-bold text-orange-600">{statistics.medium_risk_roads}</div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm text-green-600 mb-1">Low Risk</div>
                <div className="text-2xl font-bold text-green-600">{statistics.low_risk_roads}</div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-sm text-blue-600 mb-1">Average Jam Probability</div>
              <div className="text-xl font-bold text-blue-900">
                {(statistics.average_jam_probability * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Info Card */}
      <Card>
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-900">How It Works</h3>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Jam Spread Prediction</h4>
            <p className="text-blue-800 text-sm">
              This feature uses advanced models (LIM, LTM, SIR, SIS) to predict how traffic jams
              spread across Singapore's road network over different time horizons (30 minutes to 24 hours).
              The system analyzes historical patterns to forecast congestion risk on major roads and expressways.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl mb-2">🔴</div>
              <h4 className="font-medium text-gray-900 mb-1">High Risk (≥70%)</h4>
              <p className="text-sm text-gray-600">
                Very likely to experience congestion within the time horizon
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl mb-2">🟠</div>
              <h4 className="font-medium text-gray-900 mb-1">Medium Risk (30-70%)</h4>
              <p className="text-sm text-gray-600">
                Moderate chance of congestion spreading to this road
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl mb-2">🟢</div>
              <h4 className="font-medium text-gray-900 mb-1">Low Risk (&lt;30%)</h4>
              <p className="text-sm text-gray-600">
                Unlikely to experience congestion in this time period
              </p>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Usage Instructions</h4>
            <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
              <li>Select a time horizon (30 minutes to 24 hours) to forecast congestion</li>
              <li>Choose a prediction model based on your use case (LIM recommended for general use)</li>
              <li>Click "Run Prediction" to generate congestion forecasts</li>
              <li>View results on the interactive map and detailed statistics</li>
              <li>Click on any road marker to see detailed congestion information</li>
            </ol>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-yellow-900 mb-2">📊 Model Information</h4>
            <div className="space-y-2 text-sm text-yellow-800">
              <p><strong>LIM (Linear Independent Cascade):</strong> Uses Monte Carlo simulations with probabilistic spread. Best for general traffic prediction.</p>
              <p><strong>LTM (Linear Threshold Model):</strong> Threshold-based activation. Good for sudden congestion events.</p>
              <p><strong>SIR Model:</strong> Epidemic model with recovery. Models temporary jams well.</p>
              <p><strong>SIS Model:</strong> Epidemic model without immunity. For recurring congestion patterns.</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Map Placeholder */}
      <Card>
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-900">Prediction Map</h3>

          <div className="relative">
            <MapContainer
              center={mapCenter}
              zoom={mapZoom}
              style={{ height: '500px', width: '100%', borderRadius: '8px' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />

              {/* Render prediction markers */}
              {predictions.map((prediction, index) => (
                <CircleMarker
                  key={index}
                  center={getCoordinates(prediction)}
                  radius={8 + (prediction.jam_probability * 12)}
                  fillColor={getRiskColor(prediction.jam_probability)}
                  color="#fff"
                  weight={2}
                  opacity={0.9}
                  fillOpacity={0.7}
                >
                  <Popup>
                    <div className="min-w-[250px]">
                      <h4 className="font-semibold text-gray-900 mb-2">{prediction.road_name}</h4>

                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Jam Probability:</span>
                          <span className="font-semibold" style={{ color: getRiskColor(prediction.jam_probability) }}>
                            {(prediction.jam_probability * 100).toFixed(1)}%
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Risk Level:</span>
                          <span
                            className="px-2 py-0.5 rounded-full text-xs font-medium"
                            style={{
                              backgroundColor: `${getRiskColor(prediction.jam_probability)}20`,
                              color: getRiskColor(prediction.jam_probability)
                            }}
                          >
                            {getRiskLevel(prediction.jam_probability)}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Duration:</span>
                          <span className="font-medium text-gray-900">
                            {prediction.predicted_duration_minutes} min
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Speed:</span>
                          <span className="font-medium text-gray-900">
                            {prediction.predicted_speed_kmh} km/h
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Affected Vehicles:</span>
                          <span className="font-medium text-gray-900">
                            ~{prediction.affected_vehicles_estimate}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Confidence:</span>
                          <span className="font-medium text-gray-900">
                            {(prediction.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}

              {predictions.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center z-[1000] pointer-events-none">
                  <div className="bg-white bg-opacity-90 rounded-lg p-6 shadow-lg text-center max-w-md">
                    <div className="text-4xl mb-3">📍</div>
                    <h4 className="font-semibold text-gray-900 mb-2">No Predictions Yet</h4>
                    <p className="text-sm text-gray-600">
                      Select a time horizon and model type, then click "Run Prediction" to see congestion forecasts
                    </p>
                  </div>
                </div>
              )}
            </MapContainer>

            {/* Legend */}
            <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 z-[1000]">
              <h4 className="font-semibold text-gray-900 mb-2 text-sm">Risk Level</h4>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#DC2626' }}></div>
                  <span className="text-xs text-gray-700">High Risk (≥70%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#F97316' }}></div>
                  <span className="text-xs text-gray-700">Medium Risk (30-70%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#84CC16' }}></div>
                  <span className="text-xs text-gray-700">Low Risk (&lt;30%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Predictions Table Placeholder */}
      {predictions.length > 0 && (
        <Card>
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900">Prediction Results</h3>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Road Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Jam Probability
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Level
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time Horizon
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {predictions.map((prediction, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {prediction.road_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {(prediction.jam_probability * 100).toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className="px-2 py-1 text-xs font-medium rounded-full"
                          style={{
                            backgroundColor: `${getRiskColor(prediction.jam_probability)}20`,
                            color: getRiskColor(prediction.jam_probability)
                          }}
                        >
                          {getRiskLevel(prediction.jam_probability)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {timeHorizon} minutes
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

export default JamPrediction
