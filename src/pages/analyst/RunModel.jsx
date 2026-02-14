import { useState, useEffect } from 'react'
import { runTrafficModel, getJobStatus } from '../../api/mockApi'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Select from '../../components/Select'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import { toast, ToastContainer } from '../../components/Toast'

const AnalystRunModel = () => {
  const [formData, setFormData] = useState({
    timeInterval: 'hourly',
    region: 'All',
  })
  const [jobStatus, setJobStatus] = useState(null)
  const [running, setRunning] = useState(false)

  const handleRun = async (e) => {
    e.preventDefault()
    setRunning(true)
    setJobStatus({ status: 'pending', progress: 0 })

    try {
      const result = await runTrafficModel(formData)
      setJobStatus({ ...result, progress: 0 })

      // Simulate job progression
      setTimeout(async () => {
        setJobStatus({ ...result, status: 'running', progress: 50 })
        setTimeout(async () => {
          const finalStatus = await getJobStatus(result.jobId)
          setJobStatus({ ...finalStatus, progress: 100 })
          setRunning(false)
          toast.success('Model run completed successfully')
        }, 2000)
      }, 1500)
    } catch (error) {
      toast.error('Failed to run model')
      setRunning(false)
    }
  }

  const getStatusVariant = (status) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'running':
        return 'info'
      case 'pending':
        return 'warning'
      default:
        return 'default'
    }
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Run Traffic Flow Model</h2>
        <form onSubmit={handleRun} className="space-y-4">
          <Select
            label="Time Interval"
            value={formData.timeInterval}
            onChange={(e) => setFormData({ ...formData, timeInterval: e.target.value })}
            options={[
              { value: 'hourly', label: 'Hourly' },
              { value: '4-hourly', label: '4-hourly' },
              { value: 'daily', label: 'Daily' },
            ]}
          />

          <Select
            label="Select Region or Road Subsets"
            value={formData.region}
            onChange={(e) => setFormData({ ...formData, region: e.target.value })}
            options={[
              { value: 'All', label: 'All Regions' },
              { value: 'North', label: 'North' },
              { value: 'South', label: 'South' },
              { value: 'East', label: 'East' },
              { value: 'West', label: 'West' },
              { value: 'Central', label: 'Central' },
            ]}
          />

          <Button type="submit" disabled={running} className="w-full md:w-auto">
            {running ? 'Running...' : 'Run Model'}
          </Button>
        </form>
      </Card>

      {jobStatus && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Job Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <Badge variant={getStatusVariant(jobStatus.status)}>
                  {jobStatus.status.charAt(0).toUpperCase() + jobStatus.status.slice(1)}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600">Progress</p>
                <p className="text-lg font-semibold">{jobStatus.progress}%</p>
              </div>
            </div>

            {jobStatus.status === 'running' && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${jobStatus.progress}%` }}
                />
              </div>
            )}

            {jobStatus.status === 'completed' && jobStatus.result && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">Results</h4>
                <div className="space-y-1 text-sm">
                  <p>
                    <strong>Model:</strong> {jobStatus.result.model}
                  </p>
                  <p>
                    <strong>Accuracy:</strong> {(jobStatus.result.accuracy * 100).toFixed(2)}%
                  </p>
                  <p>
                    <strong>Predictions:</strong> {jobStatus.result.predictions}
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}

export default AnalystRunModel

