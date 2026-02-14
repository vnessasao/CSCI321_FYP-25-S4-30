import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRegionData } from '../../api/mockApi'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Badge from '../../components/Badge'

const GovDashboard = () => {
  const [regionData, setRegionData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    const data = await getRegionData()
    setRegionData(data)
    setLoading(false)
  }

  const formatTimeAgo = (timestamp) => {
    const minutes = Math.floor((Date.now() - new Date(timestamp).getTime()) / 60000)
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes} min ago`
    const hours = Math.floor(minutes / 60)
    return `${hours} hour${hours > 1 ? 's' : ''} ago`
  }

  const chartData = regionData
    ? Object.entries(regionData).map(([region, data]) => ({
        region,
        congestion: (data.congestionIndex * 100).toFixed(1),
      }))
    : []

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Government Dashboard</h2>
        <p className="text-gray-600">Overview of traffic conditions across all regions</p>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(regionData).map(([region, data]) => (
          <Card key={region}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{region}</h3>
              <Badge
                variant={
                  data.congestionIndex > 0.7
                    ? 'danger'
                    : data.congestionIndex > 0.4
                    ? 'warning'
                    : 'success'
                }
              >
                {(data.congestionIndex * 100).toFixed(0)}%
              </Badge>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-sm text-gray-600">Congestion Index</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.congestionIndex.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Critical Alerts</p>
                <p className="text-xl font-semibold text-danger-600">{data.alerts}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Last Updated</p>
                <p className="text-sm text-gray-500">{formatTimeAgo(data.lastUpdated)}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold mb-4">Congestion Severity by Region</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="congestion" stroke="#3b82f6" name="Congestion %" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Button onClick={() => navigate('/gov/heatmap')} className="w-full">
              View Heatmap
            </Button>
            <Button
              onClick={() => navigate('/gov/reports')}
              variant="secondary"
              className="w-full"
            >
              Generate Report
            </Button>
            <Button
              onClick={() => navigate('/gov/alerts')}
              variant="danger"
              className="w-full"
            >
              View Critical Alerts
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default GovDashboard

