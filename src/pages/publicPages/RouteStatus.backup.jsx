import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import ApiService from '../../api/apiService'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import { toast, ToastContainer } from '../../components/Toast'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const singaporeCenter = [1.3521, 103.8198]

// Custom marker icons
const startIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const endIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const PublicRouteStatus = () => {
  const [sourceQuery, setSourceQuery] = useState('')
  const [destQuery, setDestQuery] = useState('')
  const [sourceResults, setSourceResults] = useState([])
  const [destResults, setDestResults] = useState([])
  const [selectedSource, setSelectedSource] = useState(null)
  const [selectedDest, setSelectedDest] = useState(null)
  const [sourceLoading, setSourceLoading] = useState(false)
  const [destLoading, setDestLoading] = useState(false)
  const [showSourceDropdown, setShowSourceDropdown] = useState(false)
  const [showDestDropdown, setShowDestDropdown] = useState(false)
  const [loading, setLoading] = useState(false)
  const [routeData, setRouteData] = useState(null)

  const sourceRef = useRef(null)
  const destRef = useRef(null)
  const sourceDebounceRef = useRef(null)
  const destDebounceRef = useRef(null)

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (sourceRef.current && !sourceRef.current.contains(event.target)) {
        setShowSourceDropdown(false)
      }
      if (destRef.current && !destRef.current.contains(event.target)) {
        setShowDestDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced search for source
  useEffect(() => {
    if (sourceDebounceRef.current) {
      clearTimeout(sourceDebounceRef.current)
    }

    if (sourceQuery.length < 2) {
      setSourceResults([])
      return
    }

    sourceDebounceRef.current = setTimeout(async () => {
      setSourceLoading(true)
      try {
        const response = await ApiService.searchLocations(sourceQuery)
        if (response.success) {
          setSourceResults(response.results)
          setShowSourceDropdown(true)
        }
      } catch (error) {
        console.error('Search error:', error)
      } finally {
        setSourceLoading(false)
      }
    }, 300)

    return () => {
      if (sourceDebounceRef.current) {
        clearTimeout(sourceDebounceRef.current)
      }
    }
  }, [sourceQuery])

  // Debounced search for destination
  useEffect(() => {
    if (destDebounceRef.current) {
      clearTimeout(destDebounceRef.current)
    }

    if (destQuery.length < 2) {
      setDestResults([])
      return
    }

    destDebounceRef.current = setTimeout(async () => {
      setDestLoading(true)
      try {
        const response = await ApiService.searchLocations(destQuery)
        if (response.success) {
          setDestResults(response.results)
          setShowDestDropdown(true)
        }
      } catch (error) {
        console.error('Search error:', error)
      } finally {
        setDestLoading(false)
      }
    }, 300)

    return () => {
      if (destDebounceRef.current) {
        clearTimeout(destDebounceRef.current)
      }
    }
  }, [destQuery])

  const handleSelectSource = (location) => {
    setSelectedSource(location)
    setSourceQuery(location.name || location.address)
    setShowSourceDropdown(false)
  }

  const handleSelectDest = (location) => {
    setSelectedDest(location)
    setDestQuery(location.name || location.address)
    setShowDestDropdown(false)
  }

  const handleCheckRoute = async (e) => {
    e.preventDefault()

    if (!selectedSource) {
      toast.error('Please select a source location from the dropdown')
      return
    }
    if (!selectedDest) {
      toast.error('Please select a destination location from the dropdown')
      return
    }

    setLoading(true)
    setRouteData(null)

    try {
      const response = await ApiService.getRouteTraffic(
        { lat: selectedSource.lat, lon: selectedSource.lon },
        { lat: selectedDest.lat, lon: selectedDest.lon }
      )

      if (response.success) {
        setRouteData(response)
        toast.success('Route analyzed successfully')
      } else {
        toast.error(response.error || 'Failed to get route')
      }
    } catch (error) {
      console.error('Route error:', error)
      toast.error('Failed to check route status. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const getCongestionColor = (congestion) => {
    switch (congestion) {
      case 'free':
        return '#22c55e'
      case 'moderate':
        return '#eab308'
      case 'heavy':
        return '#ef4444'
      default:
        return '#3b82f6'
    }
  }

  const getOverallCongestion = () => {
    if (!routeData?.segments) return 'free'
    const heavyCount = routeData.segments.filter(s => s.congestion === 'heavy').length
    const moderateCount = routeData.segments.filter(s => s.congestion === 'moderate').length
    if (heavyCount > 0) return 'heavy'
    if (moderateCount > 0) return 'moderate'
    return 'free'
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Route Traffic Status</h2>
        <p className="text-gray-600 mb-4">
          Enter start and destination locations to view live traffic conditions along your route.
        </p>
        <form onSubmit={handleCheckRoute} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Source Input with Autocomplete */}
            <div ref={sourceRef} className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source
              </label>
              <input
                type="text"
                value={sourceQuery}
                onChange={(e) => {
                  setSourceQuery(e.target.value)
                  setSelectedSource(null)
                }}
                onFocus={() => sourceResults.length > 0 && setShowSourceDropdown(true)}
                placeholder="Type to search (e.g., Orchard Road)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {sourceLoading && (
                <div className="absolute right-3 top-9">
                  <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                </div>
              )}
              {showSourceDropdown && sourceResults.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {sourceResults.map((result, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSelectSource(result)}
                      className="px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                    >
                      <div className="font-medium text-gray-900">{result.name}</div>
                      <div className="text-sm text-gray-500">{result.address}</div>
                    </div>
                  ))}
                </div>
              )}
              {selectedSource && (
                <div className="mt-1 text-xs text-green-600">
                  ✓ Selected: {selectedSource.name}
                </div>
              )}
            </div>

            {/* Destination Input with Autocomplete */}
            <div ref={destRef} className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination
              </label>
              <input
                type="text"
                value={destQuery}
                onChange={(e) => {
                  setDestQuery(e.target.value)
                  setSelectedDest(null)
                }}
                onFocus={() => destResults.length > 0 && setShowDestDropdown(true)}
                placeholder="Type to search (e.g., Changi Airport)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {destLoading && (
                <div className="absolute right-3 top-9">
                  <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                </div>
              )}
              {showDestDropdown && destResults.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {destResults.map((result, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSelectDest(result)}
                      className="px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                    >
                      <div className="font-medium text-gray-900">{result.name}</div>
                      <div className="text-sm text-gray-500">{result.address}</div>
                    </div>
                  ))}
                </div>
              )}
              {selectedDest && (
                <div className="mt-1 text-xs text-green-600">
                  ✓ Selected: {selectedDest.name}
                </div>
              )}
            </div>
          </div>
          <Button type="submit" disabled={loading || !selectedSource || !selectedDest} className="w-full md:w-auto">
            {loading ? 'Analyzing Route...' : 'Check Route Traffic'}
          </Button>
        </form>
      </Card>

      {loading && (
        <Card>
          <div className="flex flex-col items-center justify-center py-12">
            <LoadingSpinner />
            <p className="mt-4 text-gray-600">Fetching live traffic data...</p>
          </div>
        </Card>
      )}

      {routeData && !loading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <h3 className="text-lg font-semibold mb-4">Route Summary</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-gray-600">Overall Status</p>
                    <Badge
                      variant={
                        getOverallCongestion() === 'free'
                          ? 'success'
                          : getOverallCongestion() === 'moderate'
                          ? 'warning'
                          : 'danger'
                      }
                      className="mt-1"
                    >
                      {getOverallCongestion() === 'free' ? 'Clear' :
                       getOverallCongestion() === 'moderate' ? 'Moderate Traffic' : 'Heavy Traffic'}
                    </Badge>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Distance</p>
                  <p className="text-2xl font-bold text-gray-900">{routeData.distance} km</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Estimated Travel Time</p>
                  <p className="text-2xl font-bold text-gray-900">{Math.round(routeData.estimatedTime)} min</p>
                  {routeData.totalDelay > 0 && (
                    <p className="text-sm text-red-500">
                      (+{routeData.totalDelay} min delay due to traffic)
                    </p>
                  )}
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold mb-4">Route Segments</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {routeData.segments.length > 0 ? (
                  routeData.segments.map((segment, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{segment.roadName}</p>
                        {segment.delay > 0 && (
                          <p className="text-sm text-gray-600">+{segment.delay} min delay</p>
                        )}
                      </div>
                      <Badge
                        variant={
                          segment.congestion === 'free'
                            ? 'success'
                            : segment.congestion === 'moderate'
                            ? 'warning'
                            : 'danger'
                        }
                      >
                        {segment.congestion}
                      </Badge>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No segment data available</p>
                )}
              </div>
            </Card>
          </div>

          <Card>
            <h3 className="text-lg font-semibold mb-4">Route Map</h3>
            <div className="mb-3 flex gap-4 text-sm">
              <span className="flex items-center gap-1">
                <span className="w-4 h-1 bg-green-500 rounded"></span> Free flow
              </span>
              <span className="flex items-center gap-1">
                <span className="w-4 h-1 bg-yellow-500 rounded"></span> Moderate
              </span>
              <span className="flex items-center gap-1">
                <span className="w-4 h-1 bg-red-500 rounded"></span> Heavy
              </span>
            </div>
            <MapContainer
              center={selectedSource ? [selectedSource.lat, selectedSource.lon] : singaporeCenter}
              zoom={13}
              style={{ height: '500px', width: '100%', borderRadius: '0.5rem' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />

              {/* Start Marker */}
              {selectedSource && (
                <Marker position={[selectedSource.lat, selectedSource.lon]} icon={startIcon}>
                  <Popup>
                    <div>
                      <p className="font-semibold text-green-600">Start</p>
                      <p>{selectedSource.name}</p>
                    </div>
                  </Popup>
                </Marker>
              )}

              {/* End Marker */}
              {selectedDest && (
                <Marker position={[selectedDest.lat, selectedDest.lon]} icon={endIcon}>
                  <Popup>
                    <div>
                      <p className="font-semibold text-red-600">Destination</p>
                      <p>{selectedDest.name}</p>
                    </div>
                  </Popup>
                </Marker>
              )}

              {/* Route Polyline */}
              {routeData.route && routeData.route.length > 0 && (
                <Polyline
                  positions={routeData.route}
                  color={getCongestionColor(getOverallCongestion())}
                  weight={5}
                  opacity={0.8}
                >
                  <Popup>
                    <div>
                      <p className="font-semibold">
                        {selectedSource?.name} → {selectedDest?.name}
                      </p>
                      <p>Distance: {routeData.distance} km</p>
                      <p>Time: {Math.round(routeData.estimatedTime)} min</p>
                    </div>
                  </Popup>
                </Polyline>
              )}
            </MapContainer>
          </Card>
        </>
      )}
    </div>
  )
}

export default PublicRouteStatus
