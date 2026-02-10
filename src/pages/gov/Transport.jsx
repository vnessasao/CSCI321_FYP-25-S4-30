import { useState, useEffect } from 'react'
import Card from '../../components/Card'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import ApiService from '../../api/apiService'
import LoadingSpinner from '../../components/LoadingSpinner'
import Badge from '../../components/Badge'
import Select from '../../components/Select'

const singaporeCenter = [1.3521, 103.8198]

// Static traffic congestion data for major roads
const trafficCongestionData = [
  // Heavy congestion (red) - PIE section
  {
    id: 'pie-heavy-1',
    positions: [[1.3329, 103.7720], [1.3350, 103.7850], [1.3365, 103.7980]],
    level: 'heavy',
    roadName: 'PIE (Tuas)'
  },
  // Moderate congestion (orange) - PIE section
  {
    id: 'pie-moderate-1',
    positions: [[1.3365, 103.7980], [1.3380, 103.8150], [1.3395, 103.8300]],
    level: 'moderate',
    roadName: 'PIE (City)'
  },
  // Heavy congestion (red) - CTE section
  {
    id: 'cte-heavy-1',
    positions: [[1.3100, 103.8398], [1.3200, 103.8398], [1.3300, 103.8395]],
    level: 'heavy',
    roadName: 'CTE (South)'
  },
  // Moderate congestion (orange) - CTE section
  {
    id: 'cte-moderate-1',
    positions: [[1.3300, 103.8395], [1.3400, 103.8390], [1.3500, 103.8385]],
    level: 'moderate',
    roadName: 'CTE (North)'
  },
  // Heavy congestion (red) - ECP section
  {
    id: 'ecp-heavy-1',
    positions: [[1.2980, 103.8600], [1.2985, 103.8750], [1.2990, 103.8900]],
    level: 'heavy',
    roadName: 'ECP (Changi)'
  },
  // Moderate congestion (orange) - AYE section
  {
    id: 'aye-moderate-1',
    positions: [[1.2800, 103.7800], [1.2850, 103.7950], [1.2900, 103.8100]],
    level: 'moderate',
    roadName: 'AYE (Jurong)'
  },
  // Heavy congestion (red) - Orchard Road area
  {
    id: 'orchard-heavy-1',
    positions: [[1.3020, 103.8310], [1.3045, 103.8370], [1.3070, 103.8430]],
    level: 'heavy',
    roadName: 'Orchard Road'
  },
  // Moderate congestion (orange) - Bukit Timah
  {
    id: 'bt-moderate-1',
    positions: [[1.3250, 103.8050], [1.3350, 103.7950], [1.3450, 103.7850]],
    level: 'moderate',
    roadName: 'Bukit Timah Road'
  }
]

// Traffic congestion colors
const congestionColors = {
  heavy: '#DC2626',    // Red
  moderate: '#F97316'  // Orange
}

// Traffic Congestion Overlay Component
function TrafficCongestionOverlay({ show }) {
  if (!show) return null

  return (
    <>
      {trafficCongestionData.map((segment) => (
        <Polyline
          key={segment.id}
          positions={segment.positions}
          pathOptions={{
            color: congestionColors[segment.level],
            weight: 6,
            opacity: 0.8
          }}
        >
          <Tooltip direction="top" offset={[0, -5]} opacity={0.95}>
            <div className="text-center p-1">
              <div className="font-bold text-sm">{segment.roadName}</div>
              <div className={`text-xs ${segment.level === 'heavy' ? 'text-red-600' : 'text-orange-600'}`}>
                {segment.level === 'heavy' ? 'Heavy Congestion' : 'Moderate Congestion'}
              </div>
            </div>
          </Tooltip>
        </Polyline>
      ))}
    </>
  )
}

// MRT Line colors
const lineColors = {
  'NS': '#D42E12',  // Red
  'EW': '#009645',  // Green
  'NE': '#9900AA',  // Purple
  'CC': '#FA9E0D',  // Orange
  'DT': '#005EC4',  // Blue
  'TE': '#9D5B25',  // Brown
  'BP': '#748477',  // Gray
  'SK': '#748477',  // Gray
  'PG': '#748477'   // Gray
}

const lineNames = {
  'NS': 'North-South Line',
  'EW': 'East-West Line',
  'NE': 'North-East Line',
  'CC': 'Circle Line',
  'DT': 'Downtown Line',
  'TE': 'Thomson-East Coast Line'
}

function MrtLineRoutes({ stations, selectedLine }) {
  // Group stations by line
  const stationsByLine = {}
  stations.forEach(station => {
    if (!stationsByLine[station.line]) {
      stationsByLine[station.line] = []
    }
    stationsByLine[station.line].push(station)
  })

  // Sort stations by code within each line for proper ordering
  Object.keys(stationsByLine).forEach(line => {
    stationsByLine[line].sort((a, b) => a.code.localeCompare(b.code))
  })

  const linesToShow = selectedLine === 'All'
    ? Object.keys(stationsByLine)
    : [selectedLine]

  return (
    <>
      {linesToShow.map(line => {
        const lineStations = stationsByLine[line] || []
        if (lineStations.length < 2) return null

        const positions = lineStations.map(s => [s.latitude, s.longitude])
        const color = lineColors[line] || '#000'

        return (
          <Polyline
            key={`line-${line}`}
            positions={positions}
            pathOptions={{
              color: color,
              weight: 4,
              opacity: 0.6
            }}
          />
        )
      })}

      {/* Show small station markers on the routes */}
      {stations
        .filter(s => selectedLine === 'All' || s.line === selectedLine)
        .map((station, index) => (
          <CircleMarker
            key={`${station.code}-${index}`}
            center={[station.latitude, station.longitude]}
            radius={6}
            fillColor={station.color || lineColors[station.line] || '#000'}
            color="#fff"
            weight={2}
            opacity={1}
            fillOpacity={0.9}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
              <div className="text-center p-1">
                <div className="font-bold text-sm">{station.name}</div>
                <div className="text-xs text-gray-600">{station.code}</div>
              </div>
            </Tooltip>
            <Popup>
              <div className="text-center min-w-[150px]">
                <div className="font-bold text-lg">{station.name}</div>
                <div className="text-sm text-gray-600 mb-2">{station.code}</div>
                <Badge
                  variant="info"
                  style={{ backgroundColor: station.color || lineColors[station.line], color: '#fff' }}
                >
                  {lineNames[station.line] || station.line}
                </Badge>
              </div>
            </Popup>
          </CircleMarker>
        ))}
    </>
  )
}

function BusStopMarkers({ busStops }) {
  if (!busStops || busStops.length === 0) return null

  return (
    <>
      {busStops.slice(0, 100).map((stop, index) => (
        <CircleMarker
          key={`bus-${stop.bus_stop_code}-${index}`}
          center={[stop.latitude, stop.longitude]}
          radius={5}
          fillColor="#22c55e"
          color="#16a34a"
          weight={1.5}
          opacity={0.9}
          fillOpacity={0.7}
        >
          <Tooltip direction="top" offset={[0, -5]} opacity={0.95}>
            <div className="text-center p-1">
              <div className="font-bold text-sm">{stop.description}</div>
              <div className="text-xs">{stop.bus_stop_code}</div>
            </div>
          </Tooltip>
          <Popup>
            <div className="min-w-[150px]">
              <div className="font-bold text-lg">{stop.description}</div>
              <div className="text-sm text-gray-600 mb-1">{stop.road_name}</div>
              <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded inline-block">
                Stop Code: {stop.bus_stop_code}
              </div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </>
  )
}

const GovTransport = () => {
  const [stations, setStations] = useState([])
  const [busStops, setBusStops] = useState([])
  const [trainAlerts, setTrainAlerts] = useState(null)
  const [lines, setLines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedLine, setSelectedLine] = useState('All')
  const [showBusStops, setShowBusStops] = useState(false)
  const [showTrafficCongestion, setShowTrafficCongestion] = useState(true)

  useEffect(() => {
    loadTransportData()
  }, [])

  const loadTransportData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [stationsRes, linesRes, alertsRes] = await Promise.all([
        ApiService.getMrtStations(),
        ApiService.getMrtLines(),
        ApiService.getTrainAlerts()
      ])

      if (stationsRes.success) {
        setStations(stationsRes.data.stations || [])
      }

      if (linesRes.success) {
        setLines(linesRes.data.lines || [])
      }

      if (alertsRes.success) {
        setTrainAlerts(alertsRes.data)
      }
    } catch (err) {
      setError(err.message || 'Failed to load transport data')
    } finally {
      setLoading(false)
    }
  }

  const loadBusStops = async () => {
    if (showBusStops && busStops.length === 0) {
      try {
        const res = await ApiService.getBusStops({
          latMin: 1.25,
          latMax: 1.45,
          lonMin: 103.65,
          lonMax: 104.0
        })
        if (res.success) {
          setBusStops(res.data.stops || [])
        }
      } catch (err) {
        console.error('Failed to load bus stops:', err)
      }
    }
  }

  useEffect(() => {
    if (showBusStops) {
      loadBusStops()
    }
  }, [showBusStops])

  const getAlertStatus = () => {
    if (!trainAlerts) return { status: 'unknown', color: 'gray' }
    if (trainAlerts.status === 'normal') return { status: 'Normal Operations', color: 'green' }
    return { status: 'Service Disruption', color: 'red' }
  }

  const alertStatus = getAlertStatus()

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Public Transport Overlay</h2>
            <p className="text-gray-600">MRT stations and bus stops from LTA DataMall</p>
          </div>
          <div className="flex items-center space-x-4">
            <Select
              value={selectedLine}
              onChange={(e) => setSelectedLine(e.target.value)}
              options={[
                { value: 'All', label: 'All Lines' },
                ...Object.entries(lineNames).map(([code, name]) => ({
                  value: code,
                  label: name
                }))
              ]}
            />
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showTrafficCongestion}
                onChange={(e) => setShowTrafficCongestion(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">Traffic Congestion</span>
            </label>
          </div>
        </div>
      </Card>

      {error && (
        <Card className="bg-red-50 border-red-200">
          <p className="text-red-600">{error}</p>
        </Card>
      )}

      {/* Train Service Status */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-4 h-4 rounded-full ${alertStatus.color === 'green' ? 'bg-green-500' : alertStatus.color === 'red' ? 'bg-red-500' : 'bg-gray-400'}`}></div>
            <span className="font-semibold">Train Service Status:</span>
            <Badge variant={alertStatus.color === 'green' ? 'success' : alertStatus.color === 'red' ? 'danger' : 'default'}>
              {alertStatus.status}
            </Badge>
          </div>
          <span className="text-sm text-gray-500">
            {stations.length} stations loaded
          </span>
        </div>
        {trainAlerts?.alerts && trainAlerts.alerts.length > 0 && (
          <div className="mt-3 p-3 bg-red-50 rounded">
            <div className="text-sm font-semibold text-red-700 mb-1">Alerts:</div>
            {trainAlerts.alerts.map((alert, i) => (
              <div key={i} className="text-sm text-red-600">{alert.content}</div>
            ))}
          </div>
        )}
      </Card>

      {/* MRT Line Legend */}
      <Card>
        <h3 className="text-sm font-semibold mb-2">MRT Lines</h3>
        <div className="flex flex-wrap gap-3">
          {lines.map((line) => (
            <div key={line.code} className="flex items-center space-x-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: line.color }}
              ></div>
              <span className="text-sm">{line.name}</span>
              <span className="text-xs text-gray-500">({line.station_count})</span>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <MapContainer
              center={singaporeCenter}
              zoom={12}
              style={{ height: '500px', width: '100%', borderRadius: '0.5rem' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              <TrafficCongestionOverlay show={showTrafficCongestion} />
              <MrtLineRoutes stations={stations} selectedLine={selectedLine} />
              {showBusStops && <BusStopMarkers busStops={busStops} />}
            </MapContainer>

            <div className="mt-4 flex items-center space-x-4 text-sm flex-wrap gap-2">
              <span className="flex items-center">
                <span className="w-3 h-3 rounded-full bg-blue-500 mr-1 border-2 border-white"></span>
                MRT Station
              </span>
              {showBusStops && (
                <span className="flex items-center">
                  <span className="w-3 h-3 rounded-full bg-green-500 mr-1"></span>
                  Bus Stop
                </span>
              )}
              {showTrafficCongestion && (
                <>
                  <span className="flex items-center">
                    <span className="w-6 h-1 bg-red-600 mr-1 rounded"></span>
                    Heavy Congestion
                  </span>
                  <span className="flex items-center">
                    <span className="w-6 h-1 bg-orange-500 mr-1 rounded"></span>
                    Moderate Congestion
                  </span>
                </>
              )}
            </div>
          </>
        )}
      </Card>

      {/* Station List */}
      {selectedLine !== 'All' && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">
            {lineNames[selectedLine]} Stations
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {stations
              .filter(s => s.line === selectedLine)
              .sort((a, b) => a.code.localeCompare(b.code))
              .map((station) => (
                <div
                  key={station.code}
                  className="p-2 bg-gray-50 rounded text-center text-sm"
                >
                  <div className="font-medium">{station.name}</div>
                  <div className="text-xs text-gray-500">{station.code}</div>
                </div>
              ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default GovTransport
