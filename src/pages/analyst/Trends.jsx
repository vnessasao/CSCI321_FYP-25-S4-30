import { useState, useEffect } from 'react'
import ApiService from '../../api/apiService'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Select from '../../components/Select'
import { FiRefreshCw, FiDownload, FiCalendar } from 'react-icons/fi'

const AnalystTrends = () => {
  const [timescale, setTimescale] = useState('daily')
  const [region, setRegion] = useState('All')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Set default date range based on timescale
  useEffect(() => {
    const today = new Date()
    const to = today.toISOString().split('T')[0]
    setDateTo(to)

    let from = new Date()
    switch (timescale) {
      case 'hourly':
        from.setDate(from.getDate() - 1)
        break
      case 'daily':
        from.setDate(from.getDate() - 30)
        break
      case 'weekly':
        from.setDate(from.getDate() - 84) // 12 weeks
        break
      case 'monthly':
        from.setFullYear(from.getFullYear() - 1)
        break
      case 'yearly':
        from.setFullYear(from.getFullYear() - 3)
        break
      default:
        from.setDate(from.getDate() - 30)
    }
    setDateFrom(from.toISOString().split('T')[0])
  }, [timescale])

  useEffect(() => {
    if (dateFrom && dateTo) {
      loadTrends()
    }
  }, [timescale, region, dateFrom, dateTo])

  const loadTrends = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await ApiService.getHistoricalTrends({
        timescale,
        region,
        date_from: dateFrom,
        date_to: dateTo
      })

      if (result.success) {
        // Transform data for charts
        const chartData = result.trends.map(item => ({
          date: formatDate(item.timestamp, timescale),
          avgCongestion: item.avg_congestion,
          maxCongestion: item.max_congestion,
          avgSpeed: item.avg_speed,
          sampleCount: item.sample_count,
          jammed: item.congestion_breakdown.jammed,
          heavy: item.congestion_breakdown.heavy,
          moderate: item.congestion_breakdown.moderate,
          free: item.congestion_breakdown.free
        }))

        setData({
          trends: chartData,
          summary: result.summary,
          dataPoints: result.data_points
        })
      } else {
        setError('Failed to load trends data')
      }
    } catch (err) {
      console.error('Error loading trends:', err)
      setError(err.message || 'Failed to load trends data')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (timestamp, scale) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    switch (scale) {
      case 'hourly':
        return date.toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
      case 'daily':
        return date.toLocaleDateString('en-SG', { month: 'short', day: 'numeric' })
      case 'weekly':
        return `Week ${getWeekNumber(date)}`
      case 'monthly':
        return date.toLocaleDateString('en-SG', { month: 'short', year: '2-digit' })
      case 'yearly':
        return date.getFullYear().toString()
      default:
        return date.toLocaleDateString('en-SG')
    }
  }

  const getWeekNumber = (date) => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
    const dayNum = d.getUTCDay() || 7
    d.setUTCDate(d.getUTCDate() + 4 - dayNum)
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7)
  }

  const exportData = () => {
    if (!data) return
    const csvContent = [
      ['Date', 'Avg Congestion', 'Max Congestion', 'Avg Speed', 'Samples', 'Jammed', 'Heavy', 'Moderate', 'Free'].join(','),
      ...data.trends.map(row =>
        [row.date, row.avgCongestion, row.maxCongestion, row.avgSpeed, row.sampleCount, row.jammed, row.heavy, row.moderate, row.free].join(',')
      )
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `traffic_trends_${timescale}_${region}_${dateFrom}_${dateTo}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">View Historical Trends</h2>
            <p className="text-gray-600">Analyze traffic patterns over time (TA-08)</p>
          </div>
          <div className="flex flex-wrap gap-3 w-full lg:w-auto">
            <Select
              value={timescale}
              onChange={(e) => setTimescale(e.target.value)}
              options={[
                { value: 'hourly', label: 'Hourly' },
                { value: 'daily', label: 'Daily' },
                { value: 'weekly', label: 'Weekly' },
                { value: 'monthly', label: 'Monthly' },
                { value: 'yearly', label: 'Yearly' },
              ]}
              className="w-full sm:w-36"
            />
            <Select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              options={[
                { value: 'All', label: 'All Regions' },
                { value: 'North', label: 'North' },
                { value: 'South', label: 'South' },
                { value: 'East', label: 'East' },
                { value: 'West', label: 'West' },
                { value: 'Central', label: 'Central' },
              ]}
              className="w-full sm:w-36"
            />
            <div className="flex items-center gap-2">
              <FiCalendar className="text-gray-500" />
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
              />
            </div>
            <button
              onClick={loadTrends}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <FiRefreshCw className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
            <button
              onClick={exportData}
              disabled={!data}
              className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <FiDownload />
              Export
            </button>
          </div>
        </div>
      </Card>

      {error && (
        <Card className="bg-red-50 border-red-200">
          <p className="text-red-600">{error}</p>
        </Card>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {!loading && data && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <h4 className="text-sm text-gray-500 mb-1">Overall Avg Congestion</h4>
              <p className="text-2xl font-bold text-gray-900">
                {(data.summary.overall_avg_congestion * 100).toFixed(1)}%
              </p>
            </Card>
            <Card>
              <h4 className="text-sm text-gray-500 mb-1">Peak Congestion</h4>
              <p className="text-2xl font-bold text-red-600">
                {(data.summary.peak_congestion * 100).toFixed(1)}%
              </p>
            </Card>
            <Card>
              <h4 className="text-sm text-gray-500 mb-1">Roads Analyzed</h4>
              <p className="text-2xl font-bold text-blue-600">
                {data.summary.total_roads_analyzed}
              </p>
            </Card>
          </div>

          {/* Congestion Index Chart */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">Congestion Index Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avgCongestion"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Avg Congestion"
                  dot={data.trends.length < 50}
                />
                <Line
                  type="monotone"
                  dataKey="maxCongestion"
                  stroke="#ef4444"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Max Congestion"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Average Speed Chart */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">Average Speed Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis unit=" km/h" />
                <Tooltip formatter={(v) => `${v.toFixed(1)} km/h`} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avgSpeed"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Avg Speed"
                  dot={data.trends.length < 50}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Congestion Breakdown Bar Chart */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">Congestion State Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="free" stackId="a" fill="#22c55e" name="Free Flow" />
                <Bar dataKey="moderate" stackId="a" fill="#eab308" name="Moderate" />
                <Bar dataKey="heavy" stackId="a" fill="#f97316" name="Heavy" />
                <Bar dataKey="jammed" stackId="a" fill="#ef4444" name="Jammed" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Data Points Info */}
          <Card className="bg-gray-50">
            <p className="text-sm text-gray-600">
              Showing {data.dataPoints} data points from {dateFrom} to {dateTo} |
              Timescale: {timescale} | Region: {region}
            </p>
          </Card>
        </>
      )}

      {!loading && !data && !error && (
        <Card className="text-center py-12">
          <p className="text-gray-500">No historical data available. Upload and preprocess data first.</p>
        </Card>
      )}
    </div>
  )
}

export default AnalystTrends
