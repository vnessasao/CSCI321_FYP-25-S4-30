import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import { useState, useEffect } from 'react'
import { getRoadsData } from '../../api/mockApi'
import Card from '../../components/Card'
import LoadingSpinner from '../../components/LoadingSpinner'
import 'leaflet/dist/leaflet.css'

const singaporeCenter = [1.3521, 103.8198]

const GovHeatmap = () => {
  const [roadsData, setRoadsData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRoads()
  }, [])

  const loadRoads = async () => {
    setLoading(true)
    const data = await getRoadsData('All')
    setRoadsData(data)
    setLoading(false)
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
        return '#6b7280'
    }
  }

  const getCongestionStyle = (feature) => {
    return {
      color: getCongestionColor(feature.properties.congestion),
      weight: 6,
      opacity: 0.9,
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Congestion Heatmap</h2>
        <p className="text-gray-600">Visual representation of traffic congestion across Singapore</p>
      </Card>

      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <MapContainer
            center={singaporeCenter}
            zoom={11}
            style={{ height: '600px', width: '100%', borderRadius: '0.5rem' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {roadsData && (
              <GeoJSON data={roadsData} style={getCongestionStyle} />
            )}
          </MapContainer>
        )}
      </Card>
    </div>
  )
}

export default GovHeatmap

