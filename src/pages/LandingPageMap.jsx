import React, { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import { FiMap } from 'react-icons/fi'
import Button from '../components/Button'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix default icon issue in react-leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Singapore coordinates
const SINGAPORE_CENTER = [1.3521, 103.8198]
const SINGAPORE_BOUNDS = [
  [1.16, 103.6], // Southwest
  [1.48, 104.0]  // Northeast
]

// Map updater component to refresh GeoJSON data
const MapUpdater = ({ geoJsonData }) => {
  const map = useMap()

  useEffect(() => {
    if (geoJsonData && geoJsonData.features && geoJsonData.features.length > 0) {
      // Clear existing layers (except tile layer)
      map.eachLayer((layer) => {
        if (layer instanceof L.GeoJSON) {
          map.removeLayer(layer)
        }
      })

      // Add new GeoJSON data
      const geoJsonLayer = L.geoJSON(geoJsonData, {
        style: getTrafficStyle,
        onEachFeature: (feature, layer) => {
          // Add tooltip on hover
          const props = feature.properties
          const popupContent = `
            <div style="font-family: system-ui, -apple-system, sans-serif;">
              <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">
                ${props.road_name || 'Unknown Road'}
              </h4>
              <div style="font-size: 12px; color: #666;">
                <p style="margin: 2px 0;">Speed: ${props.speed.toFixed(1)} km/h</p>
                <p style="margin: 2px 0;">Congestion:
                  <span style="
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    ${getCongestionBadgeStyle(props.congestion)}
                  ">
                    ${props.congestion.toUpperCase()}
                  </span>
                </p>
              </div>
            </div>
          `

          layer.bindTooltip(popupContent, {
            permanent: false,
            direction: 'top',
            offset: [0, -10],
            className: 'custom-tooltip'
          })
        }
      })

      geoJsonLayer.addTo(map)
    }
  }, [geoJsonData, map])

  return null
}

// Get congestion badge styling
const getCongestionBadgeStyle = (congestion) => {
  switch (congestion) {
    case 'heavy':
      return 'background: #fef2f2; color: #dc2626; border: 1px solid #fecaca;'
    case 'moderate':
      return 'background: #fffbeb; color: #d97706; border: 1px solid #fed7aa;'
    case 'normal':
      return 'background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0;'
    default:
      return 'background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb;'
  }
}

// Style function for traffic segments
const getTrafficStyle = (feature) => {
  const congestion = feature.properties.congestion

  let color
  switch (congestion) {
    case 'heavy':
      color = '#dc2626' // Red
      break
    case 'moderate':
      color = '#d97706' // Yellow/Orange
      break
    case 'normal':
      color = '#16a34a' // Green
      break
    default:
      color = '#6b7280' // Gray
  }

  return {
    color: color,
    weight: 4,
    opacity: 0.8,
    lineCap: 'round',
    lineJoin: 'round'
  }
}

const LandingPageMap = () => {
  const [trafficData, setTrafficData] = useState(null)
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef(null)
  const navigate = useNavigate()

  // Fetch traffic data from API
  const fetchTrafficData = async () => {
    try {
      const response = await fetch('/api/lta/traffic-map', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch traffic data')
      }

      const data = await response.json()

      if (data.features && Array.isArray(data.features)) {
        setTrafficData(data)
      }
    } catch (err) {
      console.error('Error fetching traffic data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Setup auto-refresh
  useEffect(() => {
    // Initial fetch
    fetchTrafficData()

    // Setup interval for auto-refresh every 60 seconds
    intervalRef.current = setInterval(fetchTrafficData, 60000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return (
    <div className="h-screen w-screen relative overflow-hidden">
      {/* Full Screen Map */}
      <MapContainer
        center={SINGAPORE_CENTER}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        maxBounds={SINGAPORE_BOUNDS}
        maxBoundsViscosity={1.0}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {trafficData && (
          <MapUpdater geoJsonData={trafficData} />
        )}
      </MapContainer>

      {/* Top Navigation Bar - Floating */}
      <div className="absolute top-0 left-0 right-0 z-[1000]">
        <div className="bg-white/95 backdrop-blur-sm shadow-lg border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo */}
              <div className="flex items-center cursor-pointer" onClick={() => navigate('/')}>
                <FiMap className="text-primary-600 text-2xl mr-2" />
                <h1 className="text-2xl font-bold text-primary-600">Flow Radar</h1>
              </div>

              {/* Auth Buttons */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => navigate('/login')}
                  className="px-6 py-2"
                >
                  Login
                </Button>
                <Button
                  onClick={() => navigate('/signup')}
                  className="px-6 py-2"
                >
                  Sign Up
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Welcome Overlay Card */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-[1000] w-full max-w-2xl px-4">
        <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl p-6 border border-gray-200">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Real-time Traffic Intelligence for Singapore
            </h2>
            <p className="text-gray-600 mb-4">
              View live traffic conditions, plan your routes, and avoid congestion with our intelligent traffic monitoring system.
            </p>
            <div className="flex gap-4 justify-center">
              <Button
                onClick={() => navigate('/signup')}
                className="px-8 py-3"
              >
                Get Started Free
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/guest')}
                className="px-8 py-3"
              >
                Continue as Guest
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Legend - Bottom Right */}
      <div className="absolute bottom-8 right-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-4 border border-gray-200">
        <h4 className="font-semibold text-gray-900 mb-3 text-sm">Traffic Conditions</h4>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-green-500 rounded"></div>
            <span className="text-xs text-gray-700">Normal Flow</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-yellow-500 rounded"></div>
            <span className="text-xs text-gray-700">Moderate Congestion</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-red-500 rounded"></div>
            <span className="text-xs text-gray-700">Heavy Congestion</span>
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-[1001]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
            <p className="text-gray-600 font-medium">Loading traffic data...</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default LandingPageMap
