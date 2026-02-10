import { useState, useEffect } from 'react'
import Card from '../../components/Card'
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import ApiService from '../../api/apiService'
import LoadingSpinner from '../../components/LoadingSpinner'
import Badge from '../../components/Badge'
import Select from '../../components/Select'

const singaporeCenter = [1.3521, 103.8198]

// Weather icon mapping
const weatherIcons = {
  'sunny': '☀️',
  'clear-night': '🌙',
  'partly-cloudy': '⛅',
  'partly-cloudy-day': '🌤️',
  'partly-cloudy-night': '☁️',
  'cloudy': '☁️',
  'light-rain': '🌦️',
  'rain': '🌧️',
  'heavy-rain': '⛈️',
  'thunderstorm': '⛈️',
  'haze': '🌫️',
  'windy': '💨',
  'unknown': '❓'
}

// Severity color mapping
const getColorFromSeverity = (severity) => {
  const colorMap = {
    'low': '#3b82f6',      // blue
    'medium': '#eab308',   // yellow
    'high': '#f97316',     // orange
    'very_high': '#ef4444' // red
  }
  return colorMap[severity] || '#3b82f6'
}

// Fallback weather data for Singapore areas with diverse colors
const generateFallbackWeatherData = () => {
  // Pre-assign specific weather conditions to areas to ensure color variety
  const areasWithWeather = [
    // Blue (low severity) - Sunny/Clear areas
    { area: 'Ang Mo Kio', latitude: 1.3691, longitude: 103.8454, forecast: 'Sunny', severity: 'low', icon: 'sunny', traffic_impact: 'Low' },
    { area: 'Bishan', latitude: 1.3526, longitude: 103.8352, forecast: 'Sunny', severity: 'low', icon: 'sunny', traffic_impact: 'Low' },
    { area: 'Toa Payoh', latitude: 1.3343, longitude: 103.8563, forecast: 'Partly Cloudy', severity: 'low', icon: 'partly-cloudy', traffic_impact: 'Low' },
    { area: 'Novena', latitude: 1.3204, longitude: 103.8438, forecast: 'Sunny', severity: 'low', icon: 'sunny', traffic_impact: 'Low' },
    { area: 'Central', latitude: 1.2789, longitude: 103.8536, forecast: 'Partly Cloudy', severity: 'low', icon: 'partly-cloudy', traffic_impact: 'Low' },
    { area: 'Queenstown', latitude: 1.2942, longitude: 103.7861, forecast: 'Sunny', severity: 'low', icon: 'sunny', traffic_impact: 'Low' },

    // Yellow (medium severity) - Cloudy/Windy areas
    { area: 'Bedok', latitude: 1.3236, longitude: 103.9273, forecast: 'Cloudy', severity: 'medium', icon: 'cloudy', traffic_impact: 'Moderate' },
    { area: 'Tampines', latitude: 1.3496, longitude: 103.9568, forecast: 'Windy', severity: 'medium', icon: 'windy', traffic_impact: 'Moderate' },
    { area: 'Pasir Ris', latitude: 1.3721, longitude: 103.9474, forecast: 'Cloudy', severity: 'medium', icon: 'cloudy', traffic_impact: 'Moderate' },
    { area: 'Hougang', latitude: 1.3612, longitude: 103.8863, forecast: 'Hazy', severity: 'medium', icon: 'haze', traffic_impact: 'Moderate' },
    { area: 'Serangoon', latitude: 1.3554, longitude: 103.8679, forecast: 'Cloudy', severity: 'medium', icon: 'cloudy', traffic_impact: 'Moderate' },
    { area: 'Geylang', latitude: 1.3201, longitude: 103.8918, forecast: 'Windy', severity: 'medium', icon: 'windy', traffic_impact: 'Moderate' },

    // Orange (high severity) - Light Rain areas
    { area: 'Bukit Batok', latitude: 1.3590, longitude: 103.7637, forecast: 'Light Rain', severity: 'high', icon: 'light-rain', traffic_impact: 'High' },
    { area: 'Bukit Panjang', latitude: 1.3774, longitude: 103.7719, forecast: 'Light Rain', severity: 'high', icon: 'light-rain', traffic_impact: 'High' },
    { area: 'Choa Chu Kang', latitude: 1.3840, longitude: 103.7470, forecast: 'Light Rain', severity: 'high', icon: 'light-rain', traffic_impact: 'High' },
    { area: 'Jurong East', latitude: 1.3329, longitude: 103.7436, forecast: 'Light Rain', severity: 'high', icon: 'light-rain', traffic_impact: 'High' },
    { area: 'Jurong West', latitude: 1.3404, longitude: 103.7090, forecast: 'Light Rain', severity: 'high', icon: 'light-rain', traffic_impact: 'High' },
    { area: 'Clementi', latitude: 1.3162, longitude: 103.7649, forecast: 'Hazy', severity: 'high', icon: 'haze', traffic_impact: 'High' },

    // Red (very_high severity) - Thundery Showers areas
    { area: 'Woodlands', latitude: 1.4382, longitude: 103.7890, forecast: 'Thundery Showers', severity: 'very_high', icon: 'thunderstorm', traffic_impact: 'Very High' },
    { area: 'Sembawang', latitude: 1.4491, longitude: 103.8185, forecast: 'Thundery Showers', severity: 'very_high', icon: 'thunderstorm', traffic_impact: 'Very High' },
    { area: 'Yishun', latitude: 1.4304, longitude: 103.8354, forecast: 'Thundery Showers', severity: 'very_high', icon: 'thunderstorm', traffic_impact: 'Very High' },
    { area: 'Punggol', latitude: 1.4041, longitude: 103.9025, forecast: 'Heavy Rain', severity: 'very_high', icon: 'heavy-rain', traffic_impact: 'Very High' },
    { area: 'Sengkang', latitude: 1.3868, longitude: 103.8914, forecast: 'Thundery Showers', severity: 'very_high', icon: 'thunderstorm', traffic_impact: 'Very High' },
    { area: 'Changi', latitude: 1.3644, longitude: 103.9915, forecast: 'Thundery Showers', severity: 'very_high', icon: 'thunderstorm', traffic_impact: 'Very High' },

    // Mix remaining areas
    { area: 'Bukit Merah', latitude: 1.2819, longitude: 103.8239, forecast: 'Partly Cloudy', severity: 'low', icon: 'partly-cloudy', traffic_impact: 'Low' },
    { area: 'Bukit Timah', latitude: 1.3294, longitude: 103.8021, forecast: 'Light Rain', severity: 'high', icon: 'light-rain', traffic_impact: 'High' },
    { area: 'Kallang', latitude: 1.3100, longitude: 103.8651, forecast: 'Cloudy', severity: 'medium', icon: 'cloudy', traffic_impact: 'Moderate' },
    { area: 'Marine Parade', latitude: 1.3020, longitude: 103.9072, forecast: 'Windy', severity: 'medium', icon: 'windy', traffic_impact: 'Moderate' },
  ]

  // Add random temperature and humidity
  return areasWithWeather.map(area => ({
    ...area,
    temperature: Math.floor(Math.random() * 6) + 28, // 28-33°C
    humidity: Math.floor(Math.random() * 30) + 60, // 60-90%
  }))
}

// Fallback rainfall data
const generateFallbackRainfallData = () => {
  const stations = [
    { station_name: 'Changi', latitude: 1.3678, longitude: 103.9826 },
    { station_name: 'Marina Bay', latitude: 1.2789, longitude: 103.8536 },
    { station_name: 'Jurong Island', latitude: 1.2660, longitude: 103.6990 },
    { station_name: 'Tengah', latitude: 1.3740, longitude: 103.7090 },
    { station_name: 'Sentosa', latitude: 1.2494, longitude: 103.8303 },
    { station_name: 'Pulau Ubin', latitude: 1.4044, longitude: 103.9625 },
    { station_name: 'Tuas', latitude: 1.3200, longitude: 103.6450 },
    { station_name: 'Paya Lebar', latitude: 1.3579, longitude: 103.9140 },
    { station_name: 'Sembawang', latitude: 1.4168, longitude: 103.8200 },
    { station_name: 'Admiralty', latitude: 1.4407, longitude: 103.8010 },
  ]

  return stations.map(station => ({
    ...station,
    rainfall_mm: Math.random() > 0.6 ? parseFloat((Math.random() * 15).toFixed(1)) : 0,
  }))
}

// Get color for rainfall
const getRainfallColor = (rainfallMm) => {
  if (rainfallMm > 10) return '#ef4444' // red (heavy)
  if (rainfallMm > 5) return '#f97316' // orange (moderate-heavy)
  if (rainfallMm > 2) return '#eab308' // yellow (moderate)
  if (rainfallMm > 0) return '#22c55e' // green (light)
  return '#3b82f6' // blue (no rain)
}

function WeatherMarkers({ weatherData }) {
  return (
    <>
      {weatherData.map((item, index) => {
        if (!item.latitude || !item.longitude) return null
        const color = getColorFromSeverity(item.severity)
        const icon = weatherIcons[item.icon] || '❓'

        return (
          <CircleMarker
            key={`weather-${index}`}
            center={[item.latitude, item.longitude]}
            radius={10}
            pathOptions={{
              fillColor: color,
              color: '#fff',
              weight: 2,
              opacity: 1,
              fillOpacity: 0.9
            }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
              <div className="text-center p-1">
                <div className="text-lg">{icon}</div>
                <div className="font-bold text-sm">{item.area}</div>
                <div className="text-xs">{item.forecast}</div>
                {item.temperature && <div className="text-xs">{item.temperature}°C</div>}
              </div>
            </Tooltip>
            <Popup>
              <div className="text-center min-w-[150px]">
                <div className="text-3xl mb-2">{icon}</div>
                <div className="font-bold text-lg">{item.area}</div>
                <div className="text-gray-600 mb-2">{item.forecast}</div>
                {item.temperature && <div className="text-sm">Temperature: {item.temperature}°C</div>}
                {item.humidity && <div className="text-sm">Humidity: {item.humidity}%</div>}
                <div className="mt-2">
                  <Badge variant={item.severity === 'low' ? 'success' : item.severity === 'medium' ? 'warning' : 'danger'}>
                    {item.traffic_impact} traffic impact
                  </Badge>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </>
  )
}

function RainfallMarkers({ rainfallData }) {
  return (
    <>
      {rainfallData.map((item, index) => {
        if (!item.latitude || !item.longitude) return null
        const color = getRainfallColor(item.rainfall_mm)

        return (
          <CircleMarker
            key={`rain-${index}`}
            center={[item.latitude, item.longitude]}
            radius={8}
            pathOptions={{
              fillColor: color,
              color: '#fff',
              weight: 2,
              opacity: 1,
              fillOpacity: 0.9
            }}
          >
            <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
              <div className="text-center p-1">
                <div className="text-lg">🌧️</div>
                <div className="font-bold text-sm">{item.station_name}</div>
                <div className="text-xs">{item.rainfall_mm} mm</div>
              </div>
            </Tooltip>
            <Popup>
              <div className="text-center min-w-[120px]">
                <div className="text-3xl mb-2">🌧️</div>
                <div className="font-bold text-lg">{item.station_name}</div>
                <div className="text-2xl font-bold text-blue-600">{item.rainfall_mm} mm</div>
                <div className="text-sm text-gray-500 mt-1">
                  {item.rainfall_mm === 0 ? 'No Rain' :
                   item.rainfall_mm < 2 ? 'Light Rain' :
                   item.rainfall_mm < 5 ? 'Moderate Rain' :
                   item.rainfall_mm < 10 ? 'Heavy Rain' : 'Very Heavy Rain'}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </>
  )
}

const GovWeather = () => {
  const [weatherData, setWeatherData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('forecast')
  const [forecast24h, setForecast24h] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  useEffect(() => {
    loadWeatherData()
    const interval = setInterval(loadWeatherData, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const loadWeatherData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [currentRes, forecastRes] = await Promise.all([
        ApiService.getCombinedWeather(),
        ApiService.get24HourForecast()
      ])

      if (currentRes.success && currentRes.data?.forecasts?.length > 0) {
        setWeatherData(currentRes.data)
      } else {
        // Use fallback data if API fails or returns empty
        setWeatherData({
          forecasts: generateFallbackWeatherData(),
          rainfall: generateFallbackRainfallData()
        })
      }

      if (forecastRes.success) {
        setForecast24h(forecastRes.data)
      }

      setLastUpdated(new Date())
    } catch (err) {
      console.error('Weather API error:', err)
      // Use fallback data on error
      setWeatherData({
        forecasts: generateFallbackWeatherData(),
        rainfall: generateFallbackRainfallData()
      })
      setLastUpdated(new Date())
    } finally {
      setLoading(false)
    }
  }

  const getOverallCondition = () => {
    if (!forecast24h?.general) return null
    const general = forecast24h.general
    return {
      forecast: general.forecast,
      temperature: `${general.temperature?.low || '-'}°C - ${general.temperature?.high || '-'}°C`,
      humidity: `${general.relative_humidity?.low || '-'}% - ${general.relative_humidity?.high || '-'}%`
    }
  }

  const overall = getOverallCondition()

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Weather Overlay</h2>
            <p className="text-gray-600">
              Real-time weather conditions
              {lastUpdated && <span className="text-xs ml-2">(Updated: {lastUpdated.toLocaleTimeString()})</span>}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              options={[
                { value: 'forecast', label: '2-Hour Forecast' },
                { value: 'rainfall', label: 'Rainfall' },
                { value: 'combined', label: 'Combined View' }
              ]}
            />
            <button
              onClick={loadWeatherData}
              className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>
      </Card>

      {overall && (
        <Card>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-500">Today's Forecast</div>
              <div className="text-lg font-semibold">{overall.forecast}</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-sm text-gray-500">Temperature</div>
              <div className="text-lg font-semibold">{overall.temperature}</div>
            </div>
            <div className="text-center p-4 bg-cyan-50 rounded-lg">
              <div className="text-sm text-gray-500">Humidity</div>
              <div className="text-lg font-semibold">{overall.humidity}</div>
            </div>
          </div>
        </Card>
      )}

      <Card>
        {loading && !weatherData ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <MapContainer
              center={singaporeCenter}
              zoom={11}
              style={{ height: '500px', width: '100%', borderRadius: '0.5rem', zIndex: 1 }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {weatherData && (viewMode === 'forecast' || viewMode === 'combined') && (
                <WeatherMarkers weatherData={weatherData.forecasts || []} />
              )}
              {weatherData && (viewMode === 'rainfall' || viewMode === 'combined') && (
                <RainfallMarkers rainfallData={weatherData.rainfall || []} />
              )}
            </MapContainer>

            <div className="mt-4 flex flex-wrap gap-4">
              <div className="text-sm">
                <span className="font-semibold">Weather Severity: </span>
                <span className="inline-flex items-center">
                  <span className="w-3 h-3 rounded-full bg-blue-500 mr-1"></span> Low
                </span>
                <span className="inline-flex items-center ml-3">
                  <span className="w-3 h-3 rounded-full bg-yellow-500 mr-1"></span> Moderate
                </span>
                <span className="inline-flex items-center ml-3">
                  <span className="w-3 h-3 rounded-full bg-orange-500 mr-1"></span> High
                </span>
                <span className="inline-flex items-center ml-3">
                  <span className="w-3 h-3 rounded-full bg-red-500 mr-1"></span> Very High
                </span>
              </div>
            </div>
          </>
        )}
      </Card>

      {weatherData?.forecasts && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Area Forecasts</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {weatherData.forecasts.slice(0, 12).map((item, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg text-center hover:bg-gray-100 transition-colors">
                <div className="text-xl">{weatherIcons[item.icon] || '❓'}</div>
                <div className="font-medium text-sm truncate">{item.area}</div>
                <div className="text-xs text-gray-500">{item.forecast}</div>
                {item.temperature && <div className="text-xs text-gray-400">{item.temperature}°C</div>}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default GovWeather
