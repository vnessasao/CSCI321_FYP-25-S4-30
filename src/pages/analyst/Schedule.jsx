import { useState, useEffect, useContext } from 'react'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Select from '../../components/Select'
import Input from '../../components/Input'
import Badge from '../../components/Badge'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import { AuthContext } from '../../context/AuthContext'

const AnalystSchedule = () => {
  const { user } = useContext(AuthContext)
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [frequencyPresets, setFrequencyPresets] = useState([])
  const [algorithms, setAlgorithms] = useState([])
  const [stats, setStats] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    model_type: '',
    algorithm_id: '',
    frequency: 'daily',
    notification_email: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    const token = localStorage.getItem('auth_token')

    // Load each resource independently to prevent one failure from blocking others
    try {
      const schedulesRes = await ApiService.getSchedules(token, true)
      if (schedulesRes.success) {
        setSchedules(schedulesRes.data.schedules || [])
      }
    } catch (err) {
      console.error('Failed to load schedules:', err)
      toast.error('Failed to load schedules')
    }

    try {
      const presetsRes = await ApiService.getFrequencyPresets()
      if (presetsRes.success) {
        setFrequencyPresets(presetsRes.data || [])
      }
    } catch (err) {
      console.error('Failed to load frequency presets:', err)
    }

    try {
      const algorithmsRes = await ApiService.getAlgorithms()
      if (algorithmsRes.success) {
        setAlgorithms(algorithmsRes.data.algorithms || [])
      }
    } catch (err) {
      console.error('Failed to load algorithms:', err)
    }

    try {
      const statsRes = await ApiService.getScheduleStats(token)
      if (statsRes.success) {
        setStats(statsRes.data)
      }
    } catch (err) {
      console.error('Failed to load stats:', err)
    }

    setLoading(false)
  }

  const handleCreate = () => {
    setFormData({
      name: '',
      model_type: 'bottleneck_analysis',
      algorithm_id: '',
      frequency: 'daily',
      notification_email: user?.email || '',
    })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!formData.name) {
      toast.error('Please enter a schedule name')
      return
    }
    if (!formData.model_type) {
      toast.error('Please select a model type')
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      // Convert empty string to null for algorithm_id (integer field)
      const dataToSend = {
        ...formData,
        algorithm_id: formData.algorithm_id ? parseInt(formData.algorithm_id, 10) : null
      }
      const res = await ApiService.createSchedule(dataToSend, token)

      if (res.success) {
        toast.success('Schedule created successfully')
        setModalOpen(false)
        loadData()
      } else {
        toast.error(res.error || 'Failed to create schedule')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to create schedule')
    }
  }

  const handleToggle = async (scheduleId) => {
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.toggleSchedule(scheduleId, token)

      if (res.success) {
        toast.success(res.message)
        loadData()
      } else {
        toast.error(res.error || 'Failed to toggle schedule')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to toggle schedule')
    }
  }

  const handleRunNow = async (scheduleId) => {
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.runScheduleNow(scheduleId, token)

      if (res.success) {
        toast.success('Schedule executed successfully')
        loadData()
      } else {
        toast.error(res.error || 'Failed to run schedule')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to run schedule')
    }
  }

  const handleDelete = async (scheduleId) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return

    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.deleteSchedule(scheduleId, token)

      if (res.success) {
        toast.success('Schedule deleted')
        loadData()
      } else {
        toast.error(res.error || 'Failed to delete schedule')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to delete schedule')
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }

  const columns = [
    { key: 'name', label: 'Schedule Name' },
    { key: 'model_type', label: 'Model Type' },
    {
      key: 'cron_expression',
      label: 'Frequency',
      render: (value) => {
        const preset = frequencyPresets.find(p => p.cron_expression === value)
        return <Badge variant="info">{preset ? preset.description : value}</Badge>
      }
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (value) => (
        <Badge variant={value ? 'success' : 'default'}>
          {value ? 'Active' : 'Paused'}
        </Badge>
      ),
    },
    {
      key: 'last_run',
      label: 'Last Run',
      render: (value, row) => (
        <div>
          <div>{formatDate(value)}</div>
          {row.last_run_status && (
            <Badge variant={row.last_run_status === 'completed' ? 'success' : 'danger'} className="text-xs">
              {row.last_run_status}
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'next_run',
      label: 'Next Run',
      render: (value) => formatDate(value),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleToggle(row.id)}
          >
            {row.is_active ? 'Pause' : 'Resume'}
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => handleRunNow(row.id)}
          >
            Run Now
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => handleDelete(row.id)}
          >
            Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Schedule Automated Runs</h2>
            <p className="text-gray-600">Manage automated model execution schedules</p>
          </div>
          <Button onClick={handleCreate}>Create Schedule</Button>
        </div>
      </Card>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-500">Total Schedules</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              <div className="text-sm text-gray-500">Active</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{stats.total_runs}</div>
              <div className="text-sm text-gray-500">Total Runs</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.successful_runs}</div>
              <div className="text-sm text-gray-500">Successful</div>
            </div>
          </Card>
        </div>
      )}

      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <Table columns={columns} data={schedules} emptyMessage="No schedules found" />
        )}
      </Card>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Create Schedule"
      >
        <div className="space-y-4">
          <Input
            label="Schedule Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Daily Morning Analysis"
          />

          <Select
            label="Model Type"
            value={formData.model_type}
            onChange={(e) => setFormData({ ...formData, model_type: e.target.value })}
            options={[
              { value: '', label: 'Select model type' },
              { value: 'bottleneck_analysis', label: 'Bottleneck Analysis' },
              { value: 'congestion_prediction', label: 'Congestion Prediction' },
              { value: 'anomaly_detection', label: 'Anomaly Detection' },
              { value: 'influence_learning', label: 'Influence Learning' },
            ]}
          />

          <Select
            label="Algorithm (Optional)"
            value={formData.algorithm_id}
            onChange={(e) => setFormData({ ...formData, algorithm_id: e.target.value })}
            options={[
              { value: '', label: 'Default algorithm' },
              ...algorithms.map(a => ({ value: a.id.toString(), label: a.display_name || a.name }))
            ]}
          />

          <Select
            label="Frequency"
            value={formData.frequency}
            onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
            options={frequencyPresets.length > 0 ? frequencyPresets.map(p => ({
              value: p.key,
              label: p.description
            })) : [
              { value: 'hourly', label: 'Every hour' },
              { value: 'daily', label: 'Daily at 9:00 AM' },
              { value: 'weekly', label: 'Weekly on Monday' },
              { value: 'monthly', label: 'Monthly on 1st' },
            ]}
          />

          <Input
            label="Notification Email"
            type="email"
            value={formData.notification_email}
            onChange={(e) => setFormData({ ...formData, notification_email: e.target.value })}
            placeholder="email@example.com"
          />

          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>Create Schedule</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default AnalystSchedule
