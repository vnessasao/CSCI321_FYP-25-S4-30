import { useState, useEffect, useContext } from 'react'
import { AuthContext } from '../../context/AuthContext'
import ApiService from '../../api/apiService'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import { toast, ToastContainer } from '../../components/Toast'

const GovEMAS = () => {
  const { token } = useContext(AuthContext)
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadIncidents()
  }, [])

  const loadIncidents = async () => {
    if (!token) return
    setLoading(true)
    try {
      const response = await ApiService.getEmasIncidents(token)
      if (response.success) {
        setIncidents(response.data || [])
      }
    } catch (error) {
      console.error('Failed to load EMAS incidents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleMarkCleared = async (incidentId) => {
    try {
      const response = await ApiService.updateEmasStatus(incidentId, 'Cleared', token)
      if (response.success) {
        setIncidents(
          incidents.map((inc) =>
            inc.id === incidentId ? { ...inc, status: 'Cleared' } : inc
          )
        )
        toast.success('Incident marked as cleared')
      } else {
        toast.error(response.message || 'Failed to update status')
      }
    } catch (error) {
      toast.error('Failed to update incident status')
    }
  }

  const columns = [
    {
      key: 'id',
      label: 'Incident ID',
    },
    {
      key: 'location',
      label: 'Location',
    },
    {
      key: 'type',
      label: 'Type',
      render: (value, row) => (
        <span className={row.roadwork_id ? 'font-semibold text-orange-600' : ''}>
          {value || 'General'}
          {row.roadwork_id && ' (Roadwork)'}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => (
        <Badge variant={value === 'Cleared' ? 'success' : 'warning'}>
          {value}
        </Badge>
      ),
    },
    {
      key: 'time',
      label: 'Reported At',
      render: (value) => value ? new Date(value).toLocaleString() : '-',
    },
    {
      key: 'roadwork_end',
      label: 'Expected End',
      render: (value, row) => row.roadwork_id && value
        ? new Date(value).toLocaleString()
        : '-',
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => handleMarkCleared(row.id)}
          disabled={row.status === 'Cleared'}
        >
          Mark Cleared
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">EMAS Incident Status</h2>
        <p className="text-gray-600">Manage and track emergency incidents</p>
      </Card>

      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <Table columns={columns} data={incidents} emptyMessage="No incidents found" />
        )}
      </Card>
    </div>
  )
}

export default GovEMAS

