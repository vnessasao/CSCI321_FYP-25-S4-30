import Card from '../../components/Card'
import EmptyState from '../../components/EmptyState'
import { FiServer } from 'react-icons/fi'

const DevIntegrations = () => {
  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">API Integrations</h2>
        <p className="text-gray-600">Manage external API integrations</p>
      </Card>

      <Card>
        <EmptyState
          icon={FiServer}
          message="API integrations management coming soon"
        />
      </Card>
    </div>
  )
}

export default DevIntegrations

