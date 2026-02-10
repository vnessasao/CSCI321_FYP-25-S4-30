import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'

const DataUpload = () => {
  const navigate = useNavigate()
  const location = useLocation()

  // Determine base path based on current route (gov or analyst)
  const basePath = location.pathname.startsWith('/analyst') ? '/analyst' : '/gov'

  // State management
  const [sessionId, setSessionId] = useState(null)
  const [sessionStatus, setSessionStatus] = useState('pending')
  const [files, setFiles] = useState({ roadNetwork: null, gpsTrajectories: null })
  const [uploadProgress, setUploadProgress] = useState({ roads: false, gps: false })
  const [preprocessingSummary, setPreprocessingSummary] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [k, setK] = useState(10)
  const [timeHorizon, setTimeHorizon] = useState(30)
  const [modelType, setModelType] = useState('LIM')
  const [activeAlgorithms, setActiveAlgorithms] = useState([])
  const [loadingAlgorithms, setLoadingAlgorithms] = useState(true)

  // Refs for file inputs
  const roadNetworkInputRef = useRef(null)
  const gpsInputRef = useRef(null)

  // Polling interval
  const pollingInterval = useRef(null)

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current)
      }
    }
  }, [])

  // Fetch active algorithms on mount
  useEffect(() => {
    const fetchActiveAlgorithms = async () => {
      try {
        const response = await ApiService.get('/algorithms/active')
        if (response.success && response.algorithms) {
          // Filter to show only GREEDY algorithm for bottleneck analysis, or spread models as fallback
          const relevantAlgorithms = response.algorithms.filter(algo => 
            algo.model_type === 'GREEDY' || algo.model_type !== 'GREEDY'
          )
          setActiveAlgorithms(relevantAlgorithms)
          // Set default model to first active algorithm if available
          if (relevantAlgorithms.length > 0) {
            const currentIsActive = relevantAlgorithms.some(a => a.model_type === modelType)
            if (!currentIsActive) {
              setModelType(relevantAlgorithms[0].model_type)
            }
          }
        }
      } catch (error) {
        console.error('Error fetching active algorithms:', error)
        toast.error('Failed to load active algorithms')
      } finally {
        setLoadingAlgorithms(false)
      }
    }

    fetchActiveAlgorithms()
  }, [])

  // File selection handlers
  const handleRoadNetworkChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const extension = file.name.split('.').pop().toLowerCase()
      if (extension === 'geojson' || extension === 'json') {
        setFiles(prev => ({ ...prev, roadNetwork: file }))
        toast.success(`Selected: ${file.name}`)
      } else {
        toast.error('Please select a .geojson or .json file')
        e.target.value = ''
      }
    }
  }

  const handleGpsChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const extension = file.name.split('.').pop().toLowerCase()
      if (extension === 'csv') {
        setFiles(prev => ({ ...prev, gpsTrajectories: file }))
        toast.success(`Selected: ${file.name}`)
      } else {
        toast.error('Please select a .csv file')
        e.target.value = ''
      }
    }
  }

  // Upload files
  const handleUploadFiles = async () => {
    if (!files.roadNetwork || !files.gpsTrajectories) {
      toast.error('Please select both files')
      return
    }

    setIsProcessing(true)

    try {
      // Create session
      toast.info('Creating upload session...')
      const sessionResponse = await ApiService.createUploadSession()

      if (!sessionResponse.success) {
        throw new Error(sessionResponse.error || 'Failed to create session')
      }

      const newSessionId = sessionResponse.session_id
      setSessionId(newSessionId)

      // Upload road network
      setUploadProgress({ roads: true, gps: false })
      toast.info('Uploading road network...')
      const roadResponse = await ApiService.uploadRoadNetwork(newSessionId, files.roadNetwork)

      if (!roadResponse.success) {
        throw new Error(roadResponse.error || 'Failed to upload road network')
      }

      // Upload GPS trajectories
      setUploadProgress({ roads: true, gps: true })
      toast.info('Uploading GPS trajectories...')
      const gpsResponse = await ApiService.uploadGpsTrajectories(newSessionId, files.gpsTrajectories)

      if (!gpsResponse.success) {
        throw new Error(gpsResponse.error || 'Failed to upload GPS trajectories')
      }

      toast.success('Files uploaded successfully!')
      setSessionStatus('uploaded')

    } catch (error) {
      console.error('Upload error:', error)
      toast.error(error.message || 'Failed to upload files')
      setSessionStatus('pending')
    } finally {
      setIsProcessing(false)
    }
  }

  // Preprocess data
  const handlePreprocess = async () => {
    if (!sessionId) {
      toast.error('No session found')
      return
    }

    setIsProcessing(true)
    setSessionStatus('preprocessing')

    try {
      toast.info('Starting preprocessing...')
      const response = await ApiService.preprocessData(sessionId)

      if (!response.success) {
        throw new Error(response.error || 'Preprocessing failed')
      }

      // Start polling for status
      startPolling()

    } catch (error) {
      console.error('Preprocessing error:', error)
      toast.error(error.message || 'Failed to start preprocessing')
      setSessionStatus('uploaded')
      setIsProcessing(false)
    }
  }

  // Poll session status
  const startPolling = () => {
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current)
    }

    pollingInterval.current = setInterval(async () => {
      try {
        const statusResponse = await ApiService.getSessionStatus(sessionId)

        if (!statusResponse.success) {
          throw new Error('Failed to get session status')
        }

        const session = statusResponse.session
        setSessionStatus(session.status)

        if (session.status === 'ready') {
          // Preprocessing complete
          clearInterval(pollingInterval.current)
          pollingInterval.current = null

          setPreprocessingSummary({
            roadCount: session.road_count,
            gpsCount: session.gps_point_count,
            processingTime: calculateProcessingTime(
              session.preprocessing_started_at,
              session.preprocessing_completed_at
            )
          })

          toast.success('Preprocessing completed!')
          setIsProcessing(false)

        } else if (session.status === 'failed') {
          // Preprocessing failed
          clearInterval(pollingInterval.current)
          pollingInterval.current = null

          toast.error(`Preprocessing failed: ${session.error_message}`)
          setIsProcessing(false)
        }

      } catch (error) {
        console.error('Polling error:', error)
        clearInterval(pollingInterval.current)
        pollingInterval.current = null
        setIsProcessing(false)
      }
    }, 2000) // Poll every 2 seconds
  }

  // Calculate processing time
  const calculateProcessingTime = (startTime, endTime) => {
    if (!startTime || !endTime) return 0
    const start = new Date(startTime)
    const end = new Date(endTime)
    return ((end - start) / 1000).toFixed(2)
  }

  // Run model
  const handleRunModel = async () => {
    if (!sessionId) {
      toast.error('No session found')
      return
    }

    setIsProcessing(true)

    try {
      toast.info('Running bottleneck analysis model...')
      const response = await ApiService.runBottleneckModel(sessionId, k, timeHorizon, modelType)

      if (!response.success) {
        throw new Error(response.error || 'Model run failed')
      }

      toast.success('Model completed successfully!')

      // Navigate to bottlenecks page with results
      navigate(`${basePath}/bottlenecks?sessionId=${sessionId}&k=${k}&horizon=${timeHorizon}&model=${modelType}`)

    } catch (error) {
      console.error('Model error:', error)
      toast.error(error.message || 'Failed to run model')
    } finally {
      setIsProcessing(false)
    }
  }

  // Get status badge color
  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800'
      case 'uploaded':
        return 'bg-blue-100 text-blue-800'
      case 'preprocessing':
        return 'bg-yellow-100 text-yellow-800'
      case 'ready':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <ToastContainer />

      {/* Header */}
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload & Analyze Traffic Data
        </h2>
        <p className="text-gray-600">
          Upload road network and GPS trajectory data, preprocess it, and run bottleneck analysis
        </p>
      </Card>

      {/* Section 1: Upload Files */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">📁</span>
            <h3 className="text-xl font-semibold text-gray-900">1. Upload Files</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Road Network Upload */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-blue-500 transition-colors">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Road Network (GeoJSON)
              </label>
              <input
                ref={roadNetworkInputRef}
                type="file"
                accept=".geojson,.json"
                onChange={handleRoadNetworkChange}
                className="hidden"
                disabled={uploadProgress.roads}
              />
              <Button
                onClick={() => roadNetworkInputRef.current?.click()}
                variant="secondary"
                disabled={uploadProgress.roads}
                className="w-full mb-2"
              >
                {files.roadNetwork ? '✓ ' + files.roadNetwork.name : 'Select File'}
              </Button>
              {uploadProgress.roads && (
                <div className="flex items-center justify-center text-green-600 text-sm">
                  <span>✓ Uploaded</span>
                </div>
              )}
            </div>

            {/* GPS Trajectories Upload */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-blue-500 transition-colors">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GPS Trajectories (CSV)
              </label>
              <input
                ref={gpsInputRef}
                type="file"
                accept=".csv"
                onChange={handleGpsChange}
                className="hidden"
                disabled={uploadProgress.gps}
              />
              <Button
                onClick={() => gpsInputRef.current?.click()}
                variant="secondary"
                disabled={uploadProgress.gps}
                className="w-full mb-2"
              >
                {files.gpsTrajectories ? '✓ ' + files.gpsTrajectories.name : 'Select File'}
              </Button>
              {uploadProgress.gps && (
                <div className="flex items-center justify-center text-green-600 text-sm">
                  <span>✓ Uploaded</span>
                </div>
              )}
            </div>
          </div>

          <Button
            onClick={handleUploadFiles}
            disabled={!files.roadNetwork || !files.gpsTrajectories || isProcessing || uploadProgress.roads}
            className="w-full"
          >
            {isProcessing && sessionStatus === 'pending' ? 'Uploading...' : 'Upload Files'}
          </Button>
        </div>
      </Card>

      {/* Section 2: Preprocess Data */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">⚙️</span>
              <h3 className="text-xl font-semibold text-gray-900">2. Preprocess Data</h3>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(sessionStatus)}`}>
              {sessionStatus.charAt(0).toUpperCase() + sessionStatus.slice(1)}
            </span>
          </div>

          {sessionStatus === 'preprocessing' && (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Processing data...</span>
            </div>
          )}

          {preprocessingSummary && sessionStatus === 'ready' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-medium text-green-900 mb-2">Preprocessing Complete</h4>
              <div className="grid grid-cols-3 gap-4 text-sm text-green-800">
                <div>
                  <span className="font-medium">Roads:</span> {preprocessingSummary.roadCount}
                </div>
                <div>
                  <span className="font-medium">GPS Points:</span> {preprocessingSummary.gpsCount}
                </div>
                <div>
                  <span className="font-medium">Time:</span> {preprocessingSummary.processingTime}s
                </div>
              </div>
            </div>
          )}

          {sessionStatus === 'failed' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Preprocessing failed. Please try uploading the files again.</p>
            </div>
          )}

          <Button
            onClick={handlePreprocess}
            disabled={sessionStatus !== 'uploaded' || isProcessing}
            className="w-full"
          >
            {sessionStatus === 'preprocessing' ? 'Preprocessing...' : 'Preprocess Data'}
          </Button>
        </div>
      </Card>

      {/* Section 3: Run Model */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🎯</span>
            <h3 className="text-xl font-semibold text-gray-900">3. Run Bottleneck Analysis</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* K Slider */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Bottlenecks (K): {k}
              </label>
              <input
                type="range"
                min="5"
                max="20"
                value={k}
                onChange={(e) => setK(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                disabled={sessionStatus !== 'ready'}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>5</span>
                <span>20</span>
              </div>
            </div>

            {/* Time Horizon Dropdown */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Horizon
              </label>
              <select
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={sessionStatus !== 'ready'}
              >
                <option value={5}>5 minutes</option>
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
              </select>
            </div>

            {/* Model Type Dropdown */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model Type
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={sessionStatus !== 'ready' || loadingAlgorithms || activeAlgorithms.length === 0}
              >
                {loadingAlgorithms ? (
                  <option>Loading...</option>
                ) : activeAlgorithms.length === 0 ? (
                  <option>No active algorithms</option>
                ) : (
                  activeAlgorithms.map((algo) => (
                    <option key={algo.id} value={algo.model_type}>
                      {algo.display_name}
                    </option>
                  ))
                )}
              </select>
              {!loadingAlgorithms && activeAlgorithms.length === 0 && (
                <p className="text-xs text-red-600 mt-1">
                  No active algorithms available
                </p>
              )}
            </div>
          </div>

          <Button
            onClick={handleRunModel}
            disabled={sessionStatus !== 'ready' || isProcessing || loadingAlgorithms || activeAlgorithms.length === 0}
            className="w-full"
          >
            {isProcessing && sessionStatus === 'ready' ? 'Running Model...' : 'Run Model'}
          </Button>

          {sessionStatus !== 'ready' && (
            <p className="text-sm text-gray-500 text-center">
              Complete preprocessing before running the model
            </p>
          )}
          {sessionStatus === 'ready' && activeAlgorithms.length === 0 && (
            <p className="text-sm text-red-600 text-center">
              No active algorithms available. Please activate algorithms in the management page.
            </p>
          )}
        </div>
      </Card>
    </div>
  )
}

export default DataUpload
