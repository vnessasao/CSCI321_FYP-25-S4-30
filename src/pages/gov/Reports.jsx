import Card from '../../components/Card'
import Button from '../../components/Button'
import Select from '../../components/Select'
import { useState } from 'react'
import { toast, ToastContainer } from '../../components/Toast'

const GovReports = () => {
  const [timeRange, setTimeRange] = useState('daily')
  const [region, setRegion] = useState('All')

  const handleGenerate = () => {
    toast.success('Report generation started (mock)')
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Time-based Congestion Reports</h2>
        <p className="text-gray-600">Generate detailed traffic reports for analysis</p>
      </Card>

      <Card>
        <form className="space-y-4">
          <Select
            label="Time Range"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            options={[
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly' },
              { value: 'monthly', label: 'Monthly' },
            ]}
          />

          <Select
            label="Region"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            options={[
              { value: 'All', label: 'All Regions' },
              { value: 'North', label: 'North' },
              { value: 'South', label: 'South' },
              { value: 'East', label: 'East' },
              { value: 'West', label: 'West' },
              { value: 'Central', label: 'Central' },
            ]}
          />

          <Button onClick={handleGenerate}>Generate Report</Button>
        </form>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Report Preview</h3>
        <p className="text-gray-600">
          Report generation feature will display detailed analytics here.
        </p>
      </Card>
    </div>
  )
}

export default GovReports

