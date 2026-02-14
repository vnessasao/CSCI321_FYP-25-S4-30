import Card from '../../components/Card'
import EmptyState from '../../components/EmptyState'
import { FiLayers } from 'react-icons/fi'

const DevVisualization = () => {
  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Visualization Modules</h2>
        <p className="text-gray-600">Manage visualization and chart modules</p>
      </Card>

      <Card>
        <EmptyState
          icon={FiLayers}
          message="Visualization modules feature coming soon"
        />
      </Card>
    </div>
  )
}

export default DevVisualization

