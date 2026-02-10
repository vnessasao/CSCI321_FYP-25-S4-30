import Card from '../../components/Card'
import Button from '../../components/Button'
import { toast, ToastContainer } from '../../components/Toast'

const GovSimulation = () => {
  const handleRunSimulation = () => {
    toast.info('Event simulation feature coming soon')
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Event Simulation</h2>
        <p className="text-gray-600">Simulate traffic events and predict their impact</p>
      </Card>

      <Card>
        <div className="space-y-4">
          <p className="text-gray-600">
            This feature allows you to simulate various traffic events and analyze their potential
            impact on traffic flow.
          </p>
          <Button onClick={handleRunSimulation}>Run Simulation</Button>
        </div>
      </Card>
    </div>
  )
}

export default GovSimulation

