import { useState, useEffect } from 'react'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Select from '../../components/Select'
import Input from '../../components/Input'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import { FiAlertTriangle, FiCheck, FiRefreshCw, FiSearch, FiZap } from 'react-icons/fi'

const AnalystAnomalies = () => {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)
  const [detecting, setDetecting] = useState(false)
  const [stats, setStats] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0, pages: 1 })
  const [filters, setFilters] = useState({
    anomaly_type: '',
    severity: '',
    is_confirmed: '',
    is_resolved: ''
  })
  const [detectParams, setDetectParams] = useState({
    threshold: 2.5,
    lookback_hours: 24
  })
  const [detectModalOpen, setDetectModalOpen] = useState(false)

  useEffect(() => {
    loadData()
  }, [filters, pagination.page])

  const loadData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      const [anomaliesRes, statsRes] = await Promise.all([
        ApiService.getAnomalies(token, {
          page: pagination.page,
          limit: pagination.limit,
          ...filters
        }),
        ApiService.getAnomalyStats(token)
      ])

      if (anomaliesRes.success) {
        setAnomalies(anomaliesRes.data.anomalies || [])
        setPagination(prev => ({
          ...prev,
          total: anomaliesRes.data.pagination?.total || 0,
          pages: anomaliesRes.data.pagination?.pages || 1
        }))
      }

      if (statsRes.success) {
        setStats(statsRes.data)
      }
    } catch (err) {
      toast.error('Failed to load anomalies')
    } finally {
      setLoading(false)
    }
  }

  const handleDetect = async () => {
    setDetecting(true)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.detectAnomalies(detectParams, token)

      if (res.success) {
        const count = res.data.total || 0
        const isDemo = res.data.is_demo_data ? ' (demo data)' : ''
        toast.success(`Detection complete: ${count} anomalies found${isDemo}`)
        setDetectModalOpen(false)
        loadData()
      } else {
        toast.error(res.error || 'Detection failed')
      }
    } catch (err) {
      toast.error(err.message || 'Detection failed')
    } finally {
      setDetecting(false)
    }
  }

  const handleConfirm = async (anomalyId) => {
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.confirmAnomaly(anomalyId, token)

      if (res.success) {
        toast.success('Anomaly confirmed')
        loadData()
      } else {
        toast.error(res.error || 'Failed to confirm anomaly')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to confirm anomaly')
    }
  }

  const openResolveModal = (anomaly) => {
    setSelectedAnomaly(anomaly)
    setResolutionNotes('')
    setModalOpen(true)
  }

  const handleResolve = async () => {
    if (!selectedAnomaly) return

    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.resolveAnomaly(selectedAnomaly.id, resolutionNotes, token)

      if (res.success) {
        toast.success('Anomaly resolved')
        setModalOpen(false)
        setSelectedAnomaly(null)
        loadData()
      } else {
        toast.error(res.error || 'Failed to resolve anomaly')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to resolve anomaly')
    }
  }

  const getSeverityVariant = (severity) => {
    switch (severity) {
      case 'critical': return 'danger'
      case 'high': return 'danger'
      case 'medium': return 'warning'
      case 'low': return 'info'
      default: return 'default'
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'speed_anomaly': return '🏎️'
      case 'speed_drop': return '🐢'
      case 'speed_spike': return '🏎️'
      case 'flow_anomaly': return '🚗'
      case 'occupancy_anomaly': return '📊'
      case 'incident_spike': return '🚨'
      default: return '⚠️'
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }

  const columns = [
    {
      key: 'anomaly_type',
      label: 'Type',
      render: (value) => (
        <div className="flex items-center space-x-2">
          <span>{getTypeIcon(value)}</span>
          <span className="text-sm">{value?.replace(/_/g, ' ')}</span>
        </div>
      )
    },
    {
      key: 'severity',
      label: 'Severity',
      render: (value) => (
        <Badge variant={getSeverityVariant(value)}>{value}</Badge>
      )
    },
    {
      key: 'road_name',
      label: 'Location',
      render: (value) => (
        <div>
          <div className="font-medium">{value || 'Unknown'}</div>
        </div>
      )
    },
    {
      key: 'current_speed',
      label: 'Value',
      render: (value, row) => (
        <div className="text-sm">
          <div className="font-mono">{value?.toFixed(2)} km/h</div>
          <div className="text-xs text-gray-500">
            Expected: {row.expected_speed?.toFixed(2) || '-'} km/h
          </div>
          <div className="text-xs text-gray-500">
            Deviation: {row.deviation_percent?.toFixed(1) || '-'}%
          </div>
        </div>
      )
    },
    {
      key: 'detected_at',
      label: 'Detected',
      render: (value) => <span className="text-sm">{formatDate(value)}</span>
    },
    {
      key: 'is_confirmed',
      label: 'Status',
      render: (value, row) => (
        <div className="flex flex-col space-y-1">
          {row.is_resolved ? (
            <Badge variant="success">Resolved</Badge>
          ) : value ? (
            <Badge variant="warning">Confirmed</Badge>
          ) : (
            <Badge variant="default">Unconfirmed</Badge>
          )}
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          {!row.is_confirmed && !row.is_resolved && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleConfirm(row.id)}
              title="Confirm anomaly"
            >
              <FiCheck className="w-4 h-4" />
            </Button>
          )}
          {!row.is_resolved && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => openResolveModal(row)}
              title="Resolve anomaly"
            >
              Resolve
            </Button>
          )}
        </div>
      )
    }
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Anomaly Detection</h2>
            <p className="text-gray-600">Detect and manage traffic anomalies using statistical analysis</p>
          </div>
          <div className="flex space-x-2">
            <Button onClick={loadData} variant="secondary">
              <FiRefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setDetectModalOpen(true)}>
              <FiZap className="w-4 h-4 mr-2" />
              Run Detection
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total || 0}</div>
              <div className="text-sm text-gray-500">Total Anomalies</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.by_severity?.critical || 0}</div>
              <div className="text-sm text-gray-500">Critical</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.by_severity?.high || 0}</div>
              <div className="text-sm text-gray-500">High</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.unresolved || 0}</div>
              <div className="text-sm text-gray-500">Unresolved</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.resolved_24h || 0}</div>
              <div className="text-sm text-gray-500">Resolved (24h)</div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="w-40">
            <Select
              label="Type"
              value={filters.anomaly_type}
              onChange={(e) => setFilters({ ...filters, anomaly_type: e.target.value })}
              options={[
                { value: '', label: 'All Types' },
                { value: 'speed_drop', label: 'Speed Drop (Congestion)' },
                { value: 'speed_spike', label: 'Speed Spike (Unusual)' },
                { value: 'speed_anomaly', label: 'Speed Anomaly' },
                { value: 'flow_anomaly', label: 'Flow Anomaly' },
                { value: 'occupancy_anomaly', label: 'Occupancy Anomaly' },
                { value: 'incident_spike', label: 'Incident Spike' }
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              label="Severity"
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              options={[
                { value: '', label: 'All Severities' },
                { value: 'critical', label: 'Critical' },
                { value: 'high', label: 'High' },
                { value: 'medium', label: 'Medium' },
                { value: 'low', label: 'Low' }
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              label="Status"
              value={filters.is_resolved}
              onChange={(e) => setFilters({ ...filters, is_resolved: e.target.value })}
              options={[
                { value: '', label: 'All Status' },
                { value: 'false', label: 'Unresolved' },
                { value: 'true', label: 'Resolved' }
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              label="Confirmed"
              value={filters.is_confirmed}
              onChange={(e) => setFilters({ ...filters, is_confirmed: e.target.value })}
              options={[
                { value: '', label: 'All' },
                { value: 'true', label: 'Confirmed' },
                { value: 'false', label: 'Unconfirmed' }
              ]}
            />
          </div>
        </div>
      </Card>

      {/* Anomalies Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <Table columns={columns} data={anomalies} emptyMessage="No anomalies found" />

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="text-sm text-gray-500">
                  Showing {((pagination.page - 1) * pagination.limit) + 1} to{' '}
                  {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                  {pagination.total} entries
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pagination.page === 1}
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 text-sm">
                    Page {pagination.page} of {pagination.pages}
                  </span>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pagination.page === pagination.pages}
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Resolve Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Resolve Anomaly"
      >
        <div className="space-y-4">
          {selectedAnomaly && (
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex items-center space-x-2 mb-2">
                <span>{getTypeIcon(selectedAnomaly.anomaly_type)}</span>
                <Badge variant={getSeverityVariant(selectedAnomaly.severity)}>
                  {selectedAnomaly.severity}
                </Badge>
              </div>
              <div className="text-sm">
                <strong>Type:</strong> {selectedAnomaly.anomaly_type?.replace(/_/g, ' ')}
              </div>
              <div className="text-sm text-gray-600">
                <strong>Location:</strong> {selectedAnomaly.location_name || 'Unknown'}
              </div>
              <div className="text-sm text-gray-600">
                <strong>Detected:</strong> {formatDate(selectedAnomaly.detected_at)}
              </div>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resolution Notes
            </label>
            <textarea
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              className="w-full border rounded-md p-2 text-sm"
              rows={3}
              placeholder="Describe how the anomaly was resolved..."
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleResolve}>Mark as Resolved</Button>
          </div>
        </div>
      </Modal>

      {/* Detection Parameters Modal */}
      <Modal
        isOpen={detectModalOpen}
        onClose={() => setDetectModalOpen(false)}
        title="Run Anomaly Detection"
      >
        <div className="space-y-4">
          <div className="p-3 bg-blue-50 rounded text-sm text-blue-700">
            <FiAlertTriangle className="inline w-4 h-4 mr-1" />
            This will analyze recent traffic data and detect anomalies using Z-score statistical analysis.
          </div>

          <Input
            label="Z-Score Threshold"
            type="number"
            step="0.1"
            min="1"
            max="5"
            value={detectParams.threshold}
            onChange={(e) => setDetectParams({ ...detectParams, threshold: parseFloat(e.target.value) })}
          />
          <p className="text-xs text-gray-500 -mt-2">
            Higher values = fewer anomalies detected. Recommended: 2.0-3.0
          </p>

          <Input
            label="Lookback Hours"
            type="number"
            min="1"
            max="168"
            value={detectParams.lookback_hours}
            onChange={(e) => setDetectParams({ ...detectParams, lookback_hours: parseInt(e.target.value) })}
          />
          <p className="text-xs text-gray-500 -mt-2">
            Number of hours of historical data to analyze
          </p>

          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setDetectModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleDetect} disabled={detecting}>
              {detecting ? 'Detecting...' : 'Run Detection'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default AnalystAnomalies
