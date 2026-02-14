import { useState, useEffect, useContext } from 'react'
import { AuthContext } from '../../context/AuthContext'
import ApiService from '../../api/apiService'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Input from '../../components/Input'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import Modal from '../../components/Modal'
import { toast, ToastContainer } from '../../components/Toast'
import { FiRefreshCw, FiCpu, FiPause, FiPlay, FiInfo } from 'react-icons/fi'

const DevAlgorithms = () => {
  const { token } = useContext(AuthContext)
  const [algorithms, setAlgorithms] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [suspendModalOpen, setSuspendModalOpen] = useState(false)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)
  const [selectedAlgorithm, setSelectedAlgorithm] = useState(null)
  const [suspendReason, setSuspendReason] = useState('')

  useEffect(() => {
    if (token) {
      loadAlgorithms()
      loadStats()
    }
  }, [token])

  const loadAlgorithms = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await ApiService.getAlgorithms(token)
      if (response.success) {
        setAlgorithms(response.algorithms)
      } else {
        setError('Failed to load algorithms')
      }
    } catch (err) {
      console.error('Error loading algorithms:', err)
      setError(err.message || 'Failed to load algorithms')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await ApiService.getAlgorithmStats(token)
      if (response.success) {
        setStats(response.stats)
      }
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  const handleSuspendClick = (algorithm) => {
    setSelectedAlgorithm(algorithm)
    setSuspendReason('')
    setSuspendModalOpen(true)
  }

  const handleViewDetails = (algorithm) => {
    setSelectedAlgorithm(algorithm)
    setDetailsModalOpen(true)
  }

  const handleSuspend = async () => {
    if (!selectedAlgorithm || !token) return

    if (!suspendReason.trim()) {
      toast.error('Please provide a reason for suspension')
      return
    }

    try {
      await ApiService.suspendAlgorithm(selectedAlgorithm.id, suspendReason, token)
      toast.success(`Algorithm "${selectedAlgorithm.name}" suspended`)
      setSuspendModalOpen(false)
      loadAlgorithms()
      loadStats()
    } catch (err) {
      toast.error(err.message || 'Failed to suspend algorithm')
    }
  }

  const handleActivate = async (algorithm) => {
    if (!token) {
      toast.error('Authentication required')
      return
    }

    try {
      await ApiService.activateAlgorithm(algorithm.id, token)
      toast.success(`Algorithm "${algorithm.name}" activated`)
      loadAlgorithms()
      loadStats()
    } catch (err) {
      toast.error(err.message || 'Failed to activate algorithm')
    }
  }

  const filteredAlgorithms = algorithms.filter((alg) =>
    alg.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (alg.display_name && alg.display_name.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const columns = [
    {
      key: 'name',
      label: 'Module Name',
      render: (value, row) => (
        <div>
          <p className="font-medium">{row.display_name || value}</p>
          <p className="text-xs text-gray-500">{value}</p>
        </div>
      )
    },
    {
      key: 'model_type',
      label: 'Type',
      render: (value) => (
        <Badge variant={value === 'spread_model' ? 'primary' : 'secondary'}>
          {value || 'Unknown'}
        </Badge>
      )
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (value, row) => (
        <div>
          <Badge variant={value ? 'success' : 'danger'}>
            {value ? 'Active' : 'Suspended'}
          </Badge>
          {row.suspended_at && (
            <p className="text-xs text-gray-500 mt-1">
              {new Date(row.suspended_at).toLocaleDateString()}
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'updated_at',
      label: 'Last Updated',
      render: (value) => value ? new Date(value).toLocaleDateString() : '-',
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="secondary" onClick={() => handleViewDetails(row)}>
            <FiInfo className="mr-1" />
            View
          </Button>
          {row.is_active ? (
            <Button
              size="sm"
              variant="danger"
              onClick={() => handleSuspendClick(row)}
            >
              <FiPause className="mr-1" />
              Suspend
            </Button>
          ) : (
            <Button
              size="sm"
              variant="primary"
              onClick={() => handleActivate(row)}
            >
              <FiPlay className="mr-1" />
              Activate
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />

      {/* Header */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Algorithm Modules</h2>
            <p className="text-gray-600">Manage and monitor algorithm modules (SD-02/03)</p>
          </div>
          <div className="flex gap-3 w-full sm:w-auto">
            <Input
              placeholder="Search algorithms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64"
            />
            <Button variant="secondary" onClick={loadAlgorithms}>
              <FiRefreshCw className={loading ? 'animate-spin' : ''} />
            </Button>
          </div>
        </div>
      </Card>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <FiCpu className="text-blue-500 text-xl" />
              <div>
                <p className="text-sm text-gray-500">Total Algorithms</p>
                <p className="text-xl font-bold">{stats.total}</p>
              </div>
            </div>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Active</p>
            <p className="text-xl font-bold text-green-600">{stats.active}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Suspended</p>
            <p className="text-xl font-bold text-red-600">{stats.suspended}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">By Type</p>
            <div className="text-xs text-gray-600">
              {stats.by_type && Object.entries(stats.by_type).map(([type, count]) => (
                <span key={type} className="mr-2">{type}: {count}</span>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Algorithms Table */}
      <Card>
        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <Table
            columns={columns}
            data={filteredAlgorithms}
            emptyMessage="No algorithms found"
          />
        )}
      </Card>

      {/* Suspend Modal */}
      <Modal
        isOpen={suspendModalOpen}
        onClose={() => setSuspendModalOpen(false)}
        title="Suspend Algorithm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to suspend <strong>{selectedAlgorithm?.display_name || selectedAlgorithm?.name}</strong>?
          </p>
          <p className="text-sm text-yellow-600 bg-yellow-50 p-3 rounded">
            Warning: Suspending this algorithm will prevent it from being used in traffic analysis until reactivated.
          </p>
          <Input
            label="Reason for Suspension"
            value={suspendReason}
            onChange={(e) => setSuspendReason(e.target.value)}
            placeholder="Enter reason..."
            required
          />
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="secondary" onClick={() => setSuspendModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleSuspend}>
              Suspend Algorithm
            </Button>
          </div>
        </div>
      </Modal>

      {/* Details Modal */}
      <Modal
        isOpen={detailsModalOpen}
        onClose={() => setDetailsModalOpen(false)}
        title="Algorithm Details"
      >
        {selectedAlgorithm && (
          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-500">Name</label>
              <p className="font-medium">{selectedAlgorithm.display_name || selectedAlgorithm.name}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">Internal ID</label>
              <p className="font-mono text-sm">{selectedAlgorithm.name}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">Type</label>
              <p>{selectedAlgorithm.model_type || 'Unknown'}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">Description</label>
              <p className="text-gray-700">{selectedAlgorithm.description || 'No description available'}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">Status</label>
              <Badge variant={selectedAlgorithm.is_active ? 'success' : 'danger'}>
                {selectedAlgorithm.is_active ? 'Active' : 'Suspended'}
              </Badge>
            </div>
            {selectedAlgorithm.suspended_reason && (
              <div>
                <label className="text-sm text-gray-500">Suspension Reason</label>
                <p className="text-red-600">{selectedAlgorithm.suspended_reason}</p>
              </div>
            )}
            {selectedAlgorithm.parameters && Object.keys(selectedAlgorithm.parameters).length > 0 && (
              <div>
                <label className="text-sm text-gray-500">Parameters</label>
                <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
                  {JSON.stringify(selectedAlgorithm.parameters, null, 2)}
                </pre>
              </div>
            )}
            <div className="flex justify-end pt-4">
              <Button variant="secondary" onClick={() => setDetailsModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default DevAlgorithms
