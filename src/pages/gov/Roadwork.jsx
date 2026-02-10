import { useState, useEffect, useContext } from 'react'
import { AuthContext } from '../../context/AuthContext'
import ApiService from '../../api/apiService'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import { toast, ToastContainer } from '../../components/Toast'

const GovRoadwork = () => {
  const { token } = useContext(AuthContext)
  const [formData, setFormData] = useState({
    location: '',
    startTime: new Date().toISOString().slice(0, 16),
    endTime: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
    emasIncident: false,
  })
  const [activeEvents, setActiveEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadRoadworkEvents()
  }, [])

  const loadRoadworkEvents = async () => {
    if (!token) return
    setLoading(true)
    try {
      const response = await ApiService.getRoadworkEvents(token, 'active')
      if (response.success) {
        setActiveEvents(response.data || [])
      }
    } catch (error) {
      console.error('Failed to load roadwork events:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.location || !formData.startTime || !formData.endTime) {
      toast.error('Please fill in all required fields')
      return
    }

    setSubmitting(true)
    try {
      const response = await ApiService.createRoadworkEvent(formData, token)
      if (response.success) {
        toast.success('Roadwork event created successfully')
        setFormData({
          location: '',
          startTime: new Date().toISOString().slice(0, 16),
          endTime: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
          emasIncident: false,
        })
        loadRoadworkEvents()
      } else {
        toast.error(response.message || 'Failed to create roadwork event')
      }
    } catch (error) {
      toast.error(error.message || 'Failed to create roadwork event')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (eventId) => {
    if (!confirm('Are you sure you want to delete this event?')) return
    try {
      const response = await ApiService.deleteRoadworkEvent(eventId, token)
      if (response.success) {
        toast.success('Event deleted')
        loadRoadworkEvents()
      }
    } catch (error) {
      toast.error('Failed to delete event')
    }
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Input Roadwork Event</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Location *"
                type="text"
                placeholder="Enter location (e.g., Orchard Road, Marina Bay)"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              />

              <Input
                label="Start Time *"
                type="datetime-local"
                value={formData.startTime}
                onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
              />

              <Input
                label="End Time *"
                type="datetime-local"
                value={formData.endTime}
                onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
              />

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="emas"
                  checked={formData.emasIncident}
                  onChange={(e) =>
                    setFormData({ ...formData, emasIncident: e.target.checked })
                  }
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="emas" className="ml-2 text-sm text-gray-700">
                  EMAS Incident
                </label>
              </div>

              <Button type="submit" disabled={submitting} className="w-full md:w-auto">
                {submitting ? 'Creating...' : 'Create Roadwork Event'}
              </Button>
            </form>
          </Card>
        </div>

        <div>
          <Card>
            <h3 className="text-lg font-semibold mb-4">Active Road Events</h3>
            {loading ? (
              <div className="flex justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="space-y-3">
                {activeEvents.length === 0 ? (
                  <p className="text-sm text-gray-500">No active events</p>
                ) : (
                  activeEvents.map((event) => (
                    <div key={event.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-medium text-gray-900">{event.location}</p>
                        <div className="flex items-center gap-2">
                          {event.emas && <Badge variant="danger">EMAS</Badge>}
                          <button
                            onClick={() => handleDelete(event.id)}
                            className="text-red-500 hover:text-red-700 text-xs"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600">
                        {event.startTime ? new Date(event.startTime).toLocaleString() : '-'} -{' '}
                        {event.endTime ? new Date(event.endTime).toLocaleString() : '-'}
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

export default GovRoadwork

