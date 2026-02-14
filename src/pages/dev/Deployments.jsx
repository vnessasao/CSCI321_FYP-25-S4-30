import Card from '../../components/Card'
import EmptyState from '../../components/EmptyState'
import { FiCloud } from 'react-icons/fi'

const DevDeployments = () => {
  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Deployments</h2>
        <p className="text-gray-600">Manage system deployments and releases</p>
      </Card>

      <Card>
        <EmptyState
          icon={FiCloud}
          message="Deployment management coming soon"
        />
      </Card>
    </div>
  )
}

export default DevDeployments

