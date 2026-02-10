import { useState, useEffect } from 'react'
import { getHotspots } from '../../api/mockApi'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Select from '../../components/Select'
import Badge from '../../components/Badge'
import EmptyState from '../../components/EmptyState'

const PublicHotspots = () => {
  const [region, setRegion] = useState('All')
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState('delay')

  useEffect(() => {
    loadHotspots()
  }, [region])

  const loadHotspots = async () => {
    setLoading(true)
    const data = await getHotspots(region)
    const sorted = [...data].sort((a, b) => {
      if (sortBy === 'delay') return b.avgDelay - a.avgDelay
      return a.roadName.localeCompare(b.roadName)
    })
    setHotspots(sorted)
    setLoading(false)
  }

  useEffect(() => {
    if (hotspots.length > 0) {
      loadHotspots()
    }
  }, [sortBy])

  const getSeverityVariant = (severity) => {
    switch (severity) {
      case 'heavy':
        return 'danger'
      case 'moderate':
        return 'warning'
      default:
        return 'success'
    }
  }

  const columns = [
    {
      key: 'id',
      label: 'Rank',
      render: (_, __, index) => index + 1,
    },
    {
      key: 'roadName',
      label: 'Road Name',
    },
    {
      key: 'region',
      label: 'Region',
    },
    {
      key: 'avgDelay',
      label: 'Average Delay',
      render: (value) => `${value} min`,
    },
    {
      key: 'severity',
      label: 'Congestion Severity',
      render: (value) => (
        <Badge variant={getSeverityVariant(value)}>
          {value.charAt(0).toUpperCase() + value.slice(1)}
        </Badge>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-1">Daily Top Hotspots</h2>
            <p className="text-gray-600">Most congested areas in Singapore today</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            {/* <Select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              options={[
                { value: 'All', label: 'All Regions' },
                { value: 'North', label: 'North' },
                { value: 'Central', label: 'Central' },
                { value: 'South', label: 'South' },
                { value: 'East', label: 'East' },
                { value: 'West', label: 'West' },
              ]}
              className="w-full sm:w-48"
            /> */}
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              options={[
                { value: 'delay', label: 'Sort by Delay' },
                { value: 'name', label: 'Sort by Name' },
              ]}
              className="w-full sm:w-48"
            />
          </div>
        </div>
      </Card>

      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <Table
            columns={columns}
            data={hotspots}
            emptyMessage="No hotspots found for the selected region"
          />
        )}
      </Card>
    </div>
  )
}

export default PublicHotspots

