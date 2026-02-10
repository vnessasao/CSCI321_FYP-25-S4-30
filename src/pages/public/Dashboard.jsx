import { useNavigate } from 'react-router-dom'
import { FiMap, FiNavigation, FiAlertCircle, FiFileText } from 'react-icons/fi'
import Card from '../../components/Card'
import Button from '../../components/Button'

const PublicDashboard = () => {
  const navigate = useNavigate()

  const shortcuts = [
    {
      title: 'View Congestion Map',
      description: 'See real-time traffic conditions across Singapore',
      icon: FiMap,
      path: '/map',
      color: 'bg-blue-500',
    },
    {
      title: 'Check Route Traffic',
      description: 'Check traffic status for your planned route',
      icon: FiNavigation,
      path: '/route-status',
      color: 'bg-green-500',
    },
    {
      title: 'View Daily Top Hotspots',
      description: 'See the most congested areas today',
      icon: FiAlertCircle,
      path: '/hotspots',
      color: 'bg-orange-500',
    },
    {
      title: 'Report Road Incident',
      description: 'Report accidents, breakdowns, or roadworks',
      icon: FiFileText,
      path: '/report-incident',
      color: 'bg-red-500',
    },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Flow Radar</h2>
        <p className="text-gray-600">
          Access real-time traffic information, check route conditions, and stay informed about
          congestion hotspots across Singapore. Use the quick actions below to get started.
        </p>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {shortcuts.map((shortcut) => {
          const Icon = shortcut.icon
          return (
            <Card key={shortcut.path} className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-start space-x-4">
                <div className={`${shortcut.color} p-3 rounded-lg text-white`}>
                  <Icon size={24} />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {shortcut.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">{shortcut.description}</p>
                  <Button
                    onClick={() => navigate(shortcut.path)}
                    className="w-full sm:w-auto"
                  >
                    Open
                  </Button>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

export default PublicDashboard

