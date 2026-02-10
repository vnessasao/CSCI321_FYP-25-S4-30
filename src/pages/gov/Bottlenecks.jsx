import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import { PulsingFlowLine } from '../../components/AnimatedFlowLine'
import 'leaflet/dist/leaflet.css'

// Component to handle map center/zoom changes
const MapController = ({ center, zoom }) => {
  const map = useMap()

  useEffect(() => {
    if (center && zoom) {
      map.setView(center, zoom)
    }
  }, [center, zoom, map])

  return null
}

const Bottlenecks = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()

  // Determine base path based on current route (gov or analyst)
  const basePath = location.pathname.startsWith('/analyst') ? '/analyst' : '/gov'

  // State management
  const [bottlenecks, setBottlenecks] = useState([])
  const [influenceFlows, setInfluenceFlows] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedBottlenecks, setSelectedBottlenecks] = useState([])
  const [mapCenter, setMapCenter] = useState([1.3521, 103.8198]) // Singapore
  const [mapZoom, setMapZoom] = useState(12)
  const [showFlows, setShowFlows] = useState(true)
  const [highlightedBottleneck, setHighlightedBottleneck] = useState(null)
  const [isRestoringData, setIsRestoringData] = useState(false)
  const [isPreinsertedData, setIsPreinsertedData] = useState(true)

  // Parameters from URL or defaults
  const sessionId = searchParams.get('sessionId')
  const k = parseInt(searchParams.get('k')) || 10
  const horizon = parseInt(searchParams.get('horizon')) || 30

  // Check active session info
  const checkActiveSession = async () => {
    try {
      const response = await ApiService.getActiveSessionInfo()
      if (response.success) {
        setIsPreinsertedData(response.is_preinserted)
      }
    } catch (error) {
      console.error('Error checking active session:', error)
      // Default to showing as preinserted if check fails
      setIsPreinsertedData(true)
    }
  }

  // Load bottlenecks on mount or when params change
  useEffect(() => {
    // Auto-load bottlenecks using sample data
    checkActiveSession()
    loadBottlenecks()
    loadInfluenceFlows()
  }, [k, horizon])

  // Load bottlenecks from API
  const loadBottlenecks = async () => {
    setLoading(true)

    try {
      const response = await ApiService.getTopBottlenecks(k, horizon, 'LIM', false)

      if (!response.success) {
        throw new Error(response.error || 'Failed to load bottlenecks')
      }

      setBottlenecks(response.bottlenecks || [])
      toast.success(`Loaded ${response.bottlenecks?.length || 0} bottlenecks`)

    } catch (error) {
      console.error('Error loading bottlenecks:', error)
      toast.error(error.message || 'Failed to load bottlenecks')
    } finally {
      setLoading(false)
    }
  }

  // Load influence flows for animation
  const loadInfluenceFlows = async () => {
    try {
      const response = await ApiService.getBottleneckImpacts(horizon)

      if (response.success && response.impacts) {
        setInfluenceFlows(response.impacts)
      }
    } catch (error) {
      console.error('Error loading influence flows:', error)
      // Don't show error toast - flows are optional enhancement
    }
  }

  // Recalculate bottlenecks
  const handleRecalculate = async () => {
    setLoading(true)

    try {
      toast.info('Recalculating bottlenecks...')
      const response = await ApiService.calculateBottlenecks(k, horizon, 'LIM')

      if (!response.success) {
        throw new Error(response.error || 'Calculation failed')
      }

      setBottlenecks(response.bottlenecks || [])
      toast.success('Bottlenecks recalculated successfully')

      // Reload flows after recalculation
      loadInfluenceFlows()

    } catch (error) {
      console.error('Error recalculating:', error)
      toast.error(error.message || 'Failed to recalculate bottlenecks')
    } finally {
      setLoading(false)
    }
  }

  // Handle what-if analysis
  const handleWhatIfAnalysis = async () => {
    if (selectedBottlenecks.length === 0) {
      toast.warning('Please select at least one bottleneck to analyze')
      return
    }

    setLoading(true)

    try {
      toast.info('Running what-if analysis...')
      const response = await ApiService.whatIfAnalysis(selectedBottlenecks, horizon, 'LIM')

      if (!response.success) {
        throw new Error(response.error || 'Analysis failed')
      }

      // Show results in a toast or modal
      toast.success(
        `Fixing ${selectedBottlenecks.length} bottlenecks reduces jam count from ${response.baseline_jam_count} to ${response.fixed_jam_count}`
      )

    } catch (error) {
      console.error('Error in what-if analysis:', error)
      toast.error(error.message || 'What-if analysis failed')
    } finally {
      setLoading(false)
    }
  }

  // Get color by rank (gradient from red to yellow-green)
  const getColorByRank = (rank, totalCount) => {
    const colors = ['#DC2626', '#EF4444', '#F97316', '#FACC15', '#84CC16']
    const index = Math.floor(((rank - 1) / totalCount) * colors.length)
    return colors[Math.min(index, colors.length - 1)]
  }

  // Get radius by benefit score
  const getRadiusByScore = (score, maxScore) => {
    if (maxScore === 0) return 15
    return 10 + (score / maxScore) * 20 // 10-30 pixel radius
  }

  // Get flow color based on probability
  const getFlowColor = (probability) => {
    if (probability >= 0.7) return '#DC2626' // Red - high impact
    if (probability >= 0.5) return '#F97316' // Orange - medium-high
    if (probability >= 0.3) return '#FACC15' // Yellow - medium
    return '#84CC16' // Green - low
  }

  // Get max benefit score
  const maxBenefitScore = bottlenecks.length > 0
    ? Math.max(...bottlenecks.map(b => b.benefit_score || 0))
    : 1

  // Toggle bottleneck selection
  const toggleBottleneckSelection = (roadNodeId) => {
    setSelectedBottlenecks(prev => {
      if (prev.includes(roadNodeId)) {
        return prev.filter(id => id !== roadNodeId)
      } else {
        return [...prev, roadNodeId]
      }
    })
  }

  // Center map on specific bottleneck and show its flows
  const centerOnBottleneck = (lat, lon, bottleneckId) => {
    setMapCenter([lat, lon])
    setMapZoom(14)
    setHighlightedBottleneck(bottleneckId)
  }

  // Navigate back to upload page
  const goToUpload = () => {
    navigate(`${basePath}/data-upload`)
  }

  // Restore pre-inserted data
  const handleRestorePreinsertedData = async () => {
    setIsRestoringData(true)

    try {
      toast.info('Restoring pre-inserted data...')
      const response = await ApiService.restorePreinsertedData()

      if (!response.success) {
        throw new Error(response.error || 'Failed to restore pre-inserted data')
      }

      toast.success('Pre-inserted data restored successfully')

      // Check session info and reload bottlenecks with the restored data
      await checkActiveSession()
      await loadBottlenecks()
      await loadInfluenceFlows()

    } catch (error) {
      console.error('Error restoring pre-inserted data:', error)
      toast.error(error.message || 'Failed to restore pre-inserted data')
    } finally {
      setIsRestoringData(false)
    }
  }

  // Filter flows to show only those from highlighted bottleneck or all
  const visibleFlows = highlightedBottleneck
    ? influenceFlows.filter(f => f.bottleneck_id === highlightedBottleneck)
    : influenceFlows

  return (
    <div className="space-y-6">
      <ToastContainer />

      {/* Header */}
      <Card>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Bottleneck Finder
            </h2>
            <p className="text-gray-600">
              Top {k} traffic bottlenecks with {horizon}-minute time horizon
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={showFlows ? 'primary' : 'secondary'}
              onClick={() => setShowFlows(!showFlows)}
            >
              {showFlows ? 'Hide' : 'Show'} Flow Lines
            </Button>
            {highlightedBottleneck && (
              <Button
                variant="secondary"
                onClick={() => setHighlightedBottleneck(null)}
              >
                Show All Flows
              </Button>
            )}
            <Button onClick={handleRecalculate} disabled={loading}>
              Recalculate
            </Button>
            {!isPreinsertedData && (
              <Button 
                variant="secondary" 
                onClick={handleRestorePreinsertedData}
                disabled={isRestoringData || loading}
              >
                Restore Pre-inserted Data
              </Button>
            )}
            <Button variant="secondary" onClick={goToUpload}>
              Upload Data
            </Button>
          </div>
        </div>
      </Card>

      {/* Map Visualization */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">Map View</h3>
            {influenceFlows.length > 0 && (
              <span className="text-sm text-gray-500">
                Showing {visibleFlows.length} congestion flow{visibleFlows.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading bottlenecks...</span>
            </div>
          ) : bottlenecks.length > 0 ? (
            <div className="relative">
              <MapContainer
                center={mapCenter}
                zoom={mapZoom}
                style={{ height: '600px', width: '100%', borderRadius: '8px' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />

                <MapController center={mapCenter} zoom={mapZoom} />

                {/* Animated flow lines showing congestion spread */}
                {showFlows && visibleFlows.map((flow, index) => (
                  <PulsingFlowLine
                    key={`flow-${flow.bottleneck_id}-${flow.affected_id}-${index}`}
                    from={flow.bottleneck_coords}
                    to={flow.affected_coords}
                    color={getFlowColor(flow.probability)}
                    probability={flow.probability}
                    fromName={flow.bottleneck_name}
                    toName={flow.affected_name}
                  />
                ))}

                {/* Bottleneck markers (rendered on top of flow lines) */}
                {bottlenecks.map((bottleneck) => (
                  <CircleMarker
                    key={bottleneck.road_node_id}
                    center={[bottleneck.coordinates.lat, bottleneck.coordinates.lon]}
                    radius={getRadiusByScore(bottleneck.benefit_score, maxBenefitScore)}
                    pathOptions={{
                      fillColor: getColorByRank(bottleneck.rank, k),
                      fillOpacity: highlightedBottleneck === bottleneck.road_node_id ? 1 : 0.7,
                      color: highlightedBottleneck === bottleneck.road_node_id ? '#1E40AF' : '#ffffff',
                      weight: highlightedBottleneck === bottleneck.road_node_id ? 4 : 2
                    }}
                    eventHandlers={{
                      click: () => {
                        setHighlightedBottleneck(
                          highlightedBottleneck === bottleneck.road_node_id
                            ? null
                            : bottleneck.road_node_id
                        )
                      }
                    }}
                  >
                    <Popup>
                      <div className="p-2 min-w-[200px]">
                        <h4 className="font-bold text-gray-900">Rank #{bottleneck.rank}</h4>
                        <p className="text-sm text-gray-700 mt-1">{bottleneck.road_name}</p>
                        <div className="mt-2 text-xs text-gray-600 space-y-1">
                          <div>
                            <span className="font-medium">Benefit Score:</span> {bottleneck.benefit_score.toFixed(2)}
                          </div>
                          <div>
                            <span className="font-medium">Affected Roads:</span> {bottleneck.affected_roads_count}
                          </div>
                        </div>
                        <button
                          className="mt-3 w-full bg-blue-600 text-white text-xs py-1 px-2 rounded hover:bg-blue-700"
                          onClick={() => centerOnBottleneck(
                            bottleneck.coordinates.lat,
                            bottleneck.coordinates.lon,
                            bottleneck.road_node_id
                          )}
                        >
                          Show Impact Flows
                        </button>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>

              {/* Legend */}
              <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 z-[1000] max-w-[200px]">
                <h4 className="font-semibold text-gray-900 mb-2 text-sm">Severity Level</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#DC2626' }}></div>
                    <span className="text-xs text-gray-700">Critical Bottleneck</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#F97316' }}></div>
                    <span className="text-xs text-gray-700">Major Bottleneck</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#FACC15' }}></div>
                    <span className="text-xs text-gray-700">Moderate Bottleneck</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#84CC16' }}></div>
                    <span className="text-xs text-gray-700">Minor Bottleneck</span>
                  </div>
                </div>

                {showFlows && (
                  <>
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-2 text-sm">Flow Lines</h4>
                      <p className="text-xs text-gray-500 mb-2">
                        Animated lines show how congestion spreads from one road to another
                      </p>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-1 rounded" style={{ backgroundColor: '#DC2626' }}></div>
                          <span className="text-xs text-gray-700">High Impact (70%+)</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-1 rounded" style={{ backgroundColor: '#F97316' }}></div>
                          <span className="text-xs text-gray-700">Medium (50-70%)</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-1 rounded" style={{ backgroundColor: '#FACC15' }}></div>
                          <span className="text-xs text-gray-700">Low (30-50%)</span>
                        </div>
                      </div>
                    </div>
                  </>
                )}

                <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
                  Circle size indicates benefit score
                </div>
              </div>

              {/* Instructions overlay */}
              {influenceFlows.length > 0 && (
                <div className="absolute bottom-4 left-4 bg-white/90 rounded-lg shadow-lg p-3 z-[1000] max-w-[250px]">
                  <p className="text-xs text-gray-600">
                    <strong>Tip:</strong> Click on a bottleneck (circle) to see only its impact flows.
                    The animated dots show how congestion spreads from that road to others.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-96 text-gray-500">
              <p className="mb-4">No bottlenecks to display</p>
              <p className="text-sm">Click "Upload Data" to load custom road network and GPS trajectory files</p>
            </div>
          )}
        </div>
      </Card>

      {/* Bottleneck List */}
      {bottlenecks.length > 0 && (
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <h3 className="text-xl font-semibold text-gray-900">Bottleneck Rankings</h3>
              <Button
                onClick={handleWhatIfAnalysis}
                disabled={selectedBottlenecks.length === 0 || loading}
                variant="secondary"
              >
                What-If Analysis ({selectedBottlenecks.length} selected)
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Select
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Road Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Benefit Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Affected Roads
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {bottlenecks.map((bottleneck) => (
                    <tr
                      key={bottleneck.road_node_id}
                      className={`transition-colors ${
                        highlightedBottleneck === bottleneck.road_node_id
                          ? 'ring-2 ring-blue-500'
                          : ''
                      }`}
                      style={{
                        backgroundColor: `${getColorByRank(bottleneck.rank, k)}15`
                      }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedBottlenecks.includes(bottleneck.road_node_id)}
                          onChange={() => toggleBottleneckSelection(bottleneck.road_node_id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: getColorByRank(bottleneck.rank, k) }}
                          ></div>
                          <span className="text-sm font-medium text-gray-900">#{bottleneck.rank}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{bottleneck.road_name}</div>
                        <div className="text-xs text-gray-500">{bottleneck.road_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{bottleneck.benefit_score.toFixed(2)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{bottleneck.affected_roads_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex space-x-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => centerOnBottleneck(
                              bottleneck.coordinates.lat,
                              bottleneck.coordinates.lon,
                              bottleneck.road_node_id
                            )}
                          >
                            Show on Map
                          </Button>
                        </div>
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

export default Bottlenecks
