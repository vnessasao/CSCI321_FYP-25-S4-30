import { useState, useContext } from 'react'
import ApiService from '../../api/apiService'
import { AuthContext } from '../../context/AuthContext'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Button from '../../components/Button'
import { toast, ToastContainer } from '../../components/Toast'

const PublicReportIncident = () => {
  const { token } = useContext(AuthContext)
  const [formData, setFormData] = useState({
    incident_type: '',
    location: '',
    date: new Date().toISOString().slice(0, 10),
    time: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
    period: new Date().getHours() >= 12 ? 'PM' : 'AM',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    description: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [locationLoading, setLocationLoading] = useState(false)

  const getCurrentLocation = async () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by this browser')
      return
    }

    setLocationLoading(true)
    
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        
        try {
          // Use Nominatim API for reverse geocoding (free OpenStreetMap service)
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1`
          )
          
          if (!response.ok) {
            throw new Error('Failed to fetch address')
          }
          
          const data = await response.json()
          
          // Format the address from the response
          const address = data.display_name || `${latitude}, ${longitude}`
          
          setFormData({ ...formData, location: address })
          toast.success('Location detected successfully')
        } catch (error) {
          toast.error('Failed to get address for your location')
          // Fallback to coordinates
          setFormData({ ...formData, location: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}` })
        } finally {
          setLocationLoading(false)
        }
      },
      (error) => {
        setLocationLoading(false)
        let errorMessage = 'Failed to get your location'
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied. Please enable location permissions.'
            break
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable.'
            break
          case error.TIMEOUT:
            errorMessage = 'Location request timed out.'
            break
          default:
            errorMessage = 'An unknown error occurred while getting location.'
            break
        }
        
        toast.error(errorMessage)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.incident_type || !formData.location || !formData.date || !formData.time || !formData.description.trim()) {
      toast.error('Please fill in all required fields')
      return
    }

    if (!token) {
      toast.error('You must be logged in to report incidents')
      return
    }

    setSubmitting(true)
    try {
      await ApiService.submitIncident(formData, token)
      toast.success('Incident reported successfully!')
      setFormData({
        incident_type: '',
        location: '',
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
        period: new Date().getHours() >= 12 ? 'PM' : 'AM',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        description: '',
      })
    } catch (error) {
      toast.error(error.message || 'Failed to submit incident')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Report Road Incident</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Incident Type *"
            value={formData.incident_type}
            onChange={(e) => setFormData({ ...formData, incident_type: e.target.value })}
            required
            options={[
              { value: '', label: 'Select incident type' },
              { value: 'Accident', label: 'Accident' },
              { value: 'Vehicle breakdown', label: 'Vehicle breakdown' },
              { value: 'Roadworks', label: 'Roadworks' },
              { value: 'Obstruction', label: 'Obstruction' },
            ]}
          />

          <div>
            <Input
              label="Location *"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="Enter the location of the incident"
              required
            />
            <Button
              type="button"
              variant="outline"
              className="mt-2"
              onClick={getCurrentLocation}
              disabled={locationLoading}
            >
              {locationLoading ? 'Getting Location...' : 'Use Current Location'}
            </Button>
          </div>

          <div className="space-y-2">
            <Input
              label="Date *"
              type="date"
              value={formData.date}
              max={new Date().toISOString().slice(0, 10)}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              required
            />
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  label="Time *"
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  required
                />
              </div>
              <div className="w-20">
                <Select
                  label="Period *"
                  value={formData.period}
                  onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                  required
                  options={[
                    { value: 'AM', label: 'AM' },
                    { value: 'PM', label: 'PM' },
                  ]}
                />
              </div>
            </div>
          </div>

          <div className="bg-gray-50 p-3 rounded-md">
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Timezone (Auto-detected)
            </label>
            <p className="text-sm text-gray-700">{formData.timezone}</p>
            <p className="text-xs text-gray-500 mt-1">
              Times will be converted to UTC for storage
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className={`input-field ${formData.description.trim().length < 5 && formData.description.length > 0 ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
              rows={4}
              placeholder="Provide additional details about the incident (minimum 5 characters)"
              required
            />
            <div className="mt-1 flex justify-between items-center">
              <div className="text-sm">
                {formData.description.trim().length < 5 && formData.description.length > 0 ? (
                  <span className="text-red-600">
                    Minimum 5 characters required ({5 - formData.description.trim().length} more needed)
                  </span>
                ) : formData.description.trim().length >= 5 ? (
                  <span className="text-green-600">✓ Description looks good</span>
                ) : (
                  <span className="text-gray-500">Enter incident description</span>
                )}
              </div>
              <span className="text-xs text-gray-400">
                {formData.description.length}/500
              </span>
            </div>
          </div>

          <Button type="submit" disabled={submitting} className="w-full md:w-auto">
            {submitting ? 'Submitting...' : 'Submit Report'}
          </Button>
        </form>
      </Card>
    </div>
  )
}

export default PublicReportIncident

