import { useNavigate } from 'react-router-dom'
import { FiMap, FiNavigation, FiAlertCircle, FiArrowRight } from 'react-icons/fi'
import { useAuth } from '../context/AuthContext'
import Card from '../components/Card'
import Button from '../components/Button'

const GuestDashboard = () => {
  const navigate = useNavigate()
  const { loginAsGuest } = useAuth()

  const handleContinueAsGuest = (path) => {
    // Set guest mode in auth context
    loginAsGuest()
    // Navigate to the selected feature
    navigate(path)
  }

  const features = [
    {
      icon: FiMap,
      title: 'Live Traffic Map',
      description: 'View real-time traffic conditions across Singapore with color-coded congestion levels.',
      path: '/map',
      color: 'blue'
    },
    {
      icon: FiNavigation,
      title: 'Route Status',
      description: 'Check traffic conditions along your route and get alternative suggestions.',
      path: '/route-status',
      color: 'green'
    },
    {
      icon: FiAlertCircle,
      title: 'Traffic Hotspots',
      description: 'Discover frequently congested areas and plan your journey accordingly.',
      path: '/hotspots',
      color: 'orange'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50">
      {/* Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 bg-white shadow-sm border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <FiMap className="text-primary-600 text-2xl mr-2" />
              <h1 className="text-2xl font-bold text-primary-600">Flow Radar</h1>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => navigate('/login')}
                className="px-4 py-2 text-sm"
              >
                Login
              </Button>
              <Button
                onClick={() => navigate('/signup')}
                className="px-4 py-2 text-sm"
              >
                Sign Up
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome, Guest!
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Explore our public traffic features. Select a feature below to get started.
          </p>
        </div>

        {/* Guest Notice */}
        <Card className="mb-8 bg-blue-50 border-blue-200">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <FiAlertCircle className="text-blue-600 text-2xl" />
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                You're browsing as a guest
              </h3>
              <p className="text-blue-800 mb-3">
                Some features like bookmarking routes and saving preferences require an account.
                Create a free account to unlock all features!
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => navigate('/signup')}
                  className="px-4 py-2 text-sm"
                  size="sm"
                >
                  Create Account
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 text-sm"
                  size="sm"
                >
                  Login
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="hover:shadow-lg transition-all duration-200 cursor-pointer group"
              onClick={() => handleContinueAsGuest(feature.path)}
            >
              <div className="text-center">
                <div className={`w-16 h-16 bg-${feature.color}-100 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`text-${feature.color}-600 text-3xl`} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 mb-4">
                  {feature.description}
                </p>
                <Button
                  variant="outline"
                  className="w-full flex items-center justify-center gap-2"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleContinueAsGuest(feature.path)
                  }}
                >
                  Explore
                  <FiArrowRight />
                </Button>
              </div>
            </Card>
          ))}
        </div>

        {/* Additional Info */}
        <Card className="bg-gray-50">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Want More Features?
            </h3>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              Create a free account to access personalized dashboards, save your favorite routes,
              report incidents, and get advanced traffic analytics based on your role.
            </p>
            <div className="flex gap-4 justify-center">
              <Button
                onClick={() => navigate('/signup')}
                className="px-8 py-3 text-lg flex items-center gap-2"
              >
                Create Free Account
                <FiArrowRight />
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <FiMap className="text-primary-400 text-xl mr-2" />
              <span className="text-lg font-semibold text-white">Flow Radar</span>
            </div>
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} Flow Radar. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default GuestDashboard
