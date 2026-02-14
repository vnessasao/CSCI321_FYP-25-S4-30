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
import { FiFlag, FiCheck, FiSearch, FiRefreshCw } from 'react-icons/fi'

const DevLogs = () => {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [levels, setLevels] = useState([])
  const [sources, setSources] = useState([])
  const [selectedLog, setSelectedLog] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [resolveNotes, setResolveNotes] = useState('')
  const [pagination, setPagination] = useState({ page: 1, limit: 50, total: 0, pages: 1 })

  // Filters
  const [filters, setFilters] = useState({
    level: '',
    source: '',
    search: '',
    flagged_only: false,
    unresolved_only: false,
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    loadLogs()
  }, [filters, pagination.page])

  const loadInitialData = async () => {
    try {
      const [levelsRes, sourcesRes] = await Promise.all([
        ApiService.getLogLevels(),
        ApiService.getLogSources()
      ])

      if (levelsRes.success) setLevels(levelsRes.data || [])
      if (sourcesRes.success) setSources(sourcesRes.data || [])

      await loadStats()
    } catch (err) {
      console.error('Failed to load initial data:', err)
    }
  }

  const loadLogs = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.getLogs(token, {
        page: pagination.page,
        limit: pagination.limit,
        ...filters
      })

      if (res.success) {
        setLogs(res.data.logs || [])
        setPagination(prev => ({
          ...prev,
          total: res.data.pagination.total,
          pages: res.data.pagination.pages
        }))
      }
    } catch (err) {
      toast.error('Failed to load logs')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.getLogStats(token)
      if (res.success) {
        setStats(res.data)
      }
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const handleFlag = async (logId) => {
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.flagLog(logId, token)
      if (res.success) {
        toast.success('Log flagged for review')
        loadLogs()
        loadStats()
      }
    } catch (err) {
      toast.error('Failed to flag log')
    }
  }

  const handleUnflag = async (logId) => {
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.unflagLog(logId, token)
      if (res.success) {
        toast.success('Log unflagged')
        loadLogs()
        loadStats()
      }
    } catch (err) {
      toast.error('Failed to unflag log')
    }
  }

  const handleResolve = async () => {
    if (!selectedLog) return

    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.resolveLog(selectedLog.id, resolveNotes, token)
      if (res.success) {
        toast.success('Log marked as resolved')
        setModalOpen(false)
        setSelectedLog(null)
        setResolveNotes('')
        loadLogs()
        loadStats()
      }
    } catch (err) {
      toast.error('Failed to resolve log')
    }
  }

  const openResolveModal = (log) => {
    setSelectedLog(log)
    setResolveNotes('')
    setModalOpen(true)
  }

  const getLevelBadgeVariant = (level) => {
    switch (level) {
      case 'ERROR':
      case 'CRITICAL':
        return 'danger'
      case 'WARNING':
        return 'warning'
      case 'INFO':
        return 'info'
      case 'DEBUG':
        return 'default'
      default:
        return 'default'
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }

  const columns = [
    {
      key: 'timestamp',
      label: 'Time',
      render: (value) => (
        <span className="text-sm whitespace-nowrap">{formatDate(value)}</span>
      )
    },
    {
      key: 'log_level',
      label: 'Level',
      render: (value) => (
        <Badge variant={getLevelBadgeVariant(value)}>{value}</Badge>
      )
    },
    {
      key: 'source',
      label: 'Source',
      render: (value) => (
        <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">{value}</span>
      )
    },
    {
      key: 'message',
      label: 'Message',
      render: (value) => (
        <div className="max-w-md truncate text-sm">{value}</div>
      )
    },
    {
      key: 'is_flagged',
      label: 'Status',
      render: (value, row) => (
        <div className="flex items-center space-x-1">
          {value && (
            <Badge variant={row.is_resolved ? 'success' : 'warning'}>
              {row.is_resolved ? 'Resolved' : 'Flagged'}
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          {!row.is_flagged ? (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleFlag(row.id)}
              title="Flag for review"
            >
              <FiFlag className="w-4 h-4" />
            </Button>
          ) : (
            <>
              {!row.is_resolved && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => openResolveModal(row)}
                  title="Mark as resolved"
                >
                  <FiCheck className="w-4 h-4" />
                </Button>
              )}
              <Button
                size="sm"
                variant="secondary"
                onClick={() => handleUnflag(row.id)}
                title="Unflag"
              >
                Unflag
              </Button>
            </>
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
            <h2 className="text-2xl font-bold text-gray-900 mb-2">System Logs</h2>
            <p className="text-gray-600">View and manage system logs</p>
          </div>
          <Button onClick={() => loadLogs()}>
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </Card>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.by_level?.ERROR || 0}</div>
              <div className="text-sm text-gray-500">Errors (7d)</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.by_level?.WARNING || 0}</div>
              <div className="text-sm text-gray-500">Warnings (7d)</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.by_level?.INFO || 0}</div>
              <div className="text-sm text-gray-500">Info (7d)</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.unresolved || 0}</div>
              <div className="text-sm text-gray-500">Unresolved</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{stats.error_rate_24h || 0}%</div>
              <div className="text-sm text-gray-500">Error Rate (24h)</div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="w-40">
            <Select
              label="Level"
              value={filters.level}
              onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              options={[
                { value: '', label: 'All Levels' },
                ...levels.map(l => ({ value: l, label: l }))
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              label="Source"
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              options={[
                { value: '', label: 'All Sources' },
                ...sources.map(s => ({ value: s, label: s }))
              ]}
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <Input
              label="Search"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              placeholder="Search in messages..."
            />
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.flagged_only}
                onChange={(e) => setFilters({ ...filters, flagged_only: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm">Flagged Only</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.unresolved_only}
                onChange={(e) => setFilters({ ...filters, unresolved_only: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm">Unresolved Only</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Logs Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <Table columns={columns} data={logs} emptyMessage="No logs found" />

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
        title="Resolve Log Entry"
      >
        <div className="space-y-4">
          {selectedLog && (
            <div className="p-3 bg-gray-50 rounded">
              <div className="text-sm text-gray-500 mb-1">Log Message:</div>
              <div className="text-sm">{selectedLog.message}</div>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resolution Notes
            </label>
            <textarea
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              className="w-full border rounded-md p-2 text-sm"
              rows={3}
              placeholder="Enter resolution notes..."
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
    </div>
  )
}

export default DevLogs
