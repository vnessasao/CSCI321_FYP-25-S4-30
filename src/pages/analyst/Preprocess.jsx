import { useState } from 'react'
import { runPreprocessing } from '../../api/mockApi'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Select from '../../components/Select'
import LoadingSpinner from '../../components/LoadingSpinner'
import { toast, ToastContainer } from '../../components/Toast'

const AnalystPreprocess = () => {
  const [step, setStep] = useState(1)
  const [datasetId, setDatasetId] = useState('')
  const [processing, setProcessing] = useState(false)
  const [logs, setLogs] = useState([])

  const handleStep1 = () => {
    if (!datasetId) {
      toast.error('Please select a dataset')
      return
    }
    setStep(2)
  }

  const handleStep2 = async () => {
    setStep(3)
    setProcessing(true)
    setLogs([])

    try {
      const result = await runPreprocessing(datasetId)
      setLogs(result.logs)
      toast.success('Preprocessing completed successfully')
    } catch (error) {
      toast.error('Preprocessing failed')
    } finally {
      setProcessing(false)
    }
  }

  const handleReset = () => {
    setStep(1)
    setDatasetId('')
    setLogs([])
    setProcessing(false)
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Data Preprocessing</h2>
        <div className="flex items-center space-x-4 mb-6">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  step >= s
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {s}
              </div>
              {s < 3 && (
                <div
                  className={`w-16 h-1 ${
                    step > s ? 'bg-primary-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </Card>

      {step === 1 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Step 1: Upload/Select Dataset</h3>
          <Select
            label="Select Dataset"
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            options={[
              { value: '', label: 'Select a dataset' },
              { value: 'dataset-1', label: 'Traffic Data 2024-01' },
              { value: 'dataset-2', label: 'Traffic Data 2024-02' },
              { value: 'dataset-3', label: 'Traffic Data 2024-03' },
            ]}
          />
          <Button onClick={handleStep1} className="mt-4">
            Next
          </Button>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Step 2: Basic Checks Summary</h3>
          <div className="space-y-2 mb-4">
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✓</span>
              <span>Data format validated</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✓</span>
              <span>No missing values detected</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✓</span>
              <span>Coordinates normalized</span>
            </div>
          </div>
          <div className="flex space-x-2">
            <Button variant="secondary" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button onClick={handleStep2}>Confirm Preprocessing</Button>
          </div>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Step 3: Preprocessing Logs</h3>
          {processing ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
              {logs.length === 0 ? (
                <p>No logs available</p>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="mb-1">
                    {log}
                  </div>
                ))
              )}
            </div>
          )}
          <Button onClick={handleReset} className="mt-4" variant="secondary">
            Start Over
          </Button>
        </Card>
      )}
    </div>
  )
}

export default AnalystPreprocess

