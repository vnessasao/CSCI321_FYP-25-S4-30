import { useState, useEffect } from 'react'
import { getAlerts, acknowledgeAlert } from '../../api/mockApi'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import { toast, ToastContainer } from '../../components/Toast'

const GovAlerts = () => {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    setLoading(true)
    const data = await getAlerts()
    setAlerts(data)
    setLoading(false)
  }

  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId)
      setAlerts(
        alerts.map((alert) =>
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      )
      toast.success('Alert acknowledged')
    } catch (error) {
      toast.error('Failed to acknowledge alert')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Critical Congestion Alerts</h2>
        <p className="text-gray-600">Monitor and manage critical traffic alerts</p>
      </Card>

      <div className="space-y-4">
        {alerts.length === 0 ? (
          <Card>
            <p className="text-center text-gray-500 py-8">No alerts yet.</p>
          </Card>
        ) : (
          alerts.map((alert) => (
            <Card
              key={alert.id}
              className={alert.acknowledged ? 'bg-gray-50 opacity-75' : ''}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-semibold text-gray-900">{alert.message}</h3>
                    {alert.acknowledged && (
                      <Badge variant="success">Acknowledged</Badge>
                    )}
                  </div>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p>
                      <strong>Road ID:</strong> {alert.roadId}
                    </p>
                    <p>
                      <strong>Region:</strong> {alert.region}
                    </p>
                    <p>
                      <strong>Timestamp:</strong>{' '}
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                {!alert.acknowledged && (
                  <Button
                    onClick={() => handleAcknowledge(alert.id)}
                    variant="secondary"
                  >
                    Acknowledge
                  </Button>
                )}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}

export default GovAlerts

