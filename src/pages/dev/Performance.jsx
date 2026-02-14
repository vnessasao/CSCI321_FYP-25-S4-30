import { useState, useEffect } from 'react'
import { getPerformanceMetrics } from '../../api/mockApi'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'

const DevPerformance = () => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [])

  const loadMetrics = async () => {
    setLoading(true)
    const data = await getPerformanceMetrics()
    setMetrics(data)
    setLoading(false)
  }

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
        <h2 className="text-2xl font-bold text-gray-900 mb-2">System Performance</h2>
        <p className="text-gray-600">Monitor system performance metrics</p>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-gray-600 mb-1">Avg API Response Time</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.avgApiResponseTime}ms</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">DB Query Time</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.dbQueryTime}ms</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Jobs Queued</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.jobsQueued}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Jobs Running</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.jobsRunning}</p>
        </Card>
      </div>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Performance Trends</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={metrics.trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              name="Response Time (ms)"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

export default DevPerformance

