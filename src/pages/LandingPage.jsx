import { useNavigate } from 'react-router-dom'
import { FiMap, FiActivity, FiAlertCircle, FiNavigation, FiUsers, FiArrowRight } from 'react-icons/fi'
import Button from '../components/Button'

const LandingPage = () => {
  const navigate = useNavigate()

  const features = [
    {
      icon: FiMap,
      title: 'View Live Congestion Maps',
      description: 'Instantly see traffic conditions across roads using color-coded congestion levels.'
    },
    {
      icon: FiActivity,
      title: 'Analyze Traffic Conditions',
      description: 'Understand speed, flow, and density on each road segment through interactive pop-ups.'
    },
    {
      icon: FiAlertCircle,
      title: 'Detect Congestion Hotspots',
      description: 'Identify frequently congested roads and bottlenecks based on traffic patterns.'
    },
    {
      icon: FiNavigation,
      title: 'Plan Better Routes',
      description: 'Check traffic conditions along selected routes before you travel.'
    },
    {
      icon: FiUsers,
      title: 'Support Smarter Decisions',
      description: 'Access role-specific dashboards designed for public users, analysts, and authorities.'
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

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-36 pb-16">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            See the City. <span className="text-primary-600">Understand the Traffic.</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-4 leading-relaxed">
            Flow Radar is an intelligent traffic monitoring platform that transforms 
            road and vehicle data into clear, real-time traffic insights.
          </p>
          <p className="text-lg text-gray-500 max-w-3xl mx-auto mb-10">
            Explore live congestion maps, identify traffic hotspots, and understand how traffic 
            conditions change across the road network — all in one interactive view.
          </p>
          <div className="flex flex-col items-center gap-4">
            <div className="flex gap-4">
              <Button
                onClick={() => navigate('/signup')}
                className="px-8 py-3 text-lg flex items-center gap-2"
              >
                Get Started
                <FiArrowRight />
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/login')}
                className="px-8 py-3 text-lg"
              >
                Login to Dashboard
              </Button>
            </div>
            <button
              onClick={() => navigate('/guest')}
              className="text-primary-600 hover:text-primary-700 font-medium text-lg underline"
            >
              Continue as Guest
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h3 className="text-3xl font-bold text-gray-900 mb-4">What You Can Do</h3>
          <div className="w-20 h-1 bg-primary-600 mx-auto rounded"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100"
            >
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="text-primary-600 text-2xl" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-3">
                {feature.title}
              </h4>
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
          
          {/* Extra feature for better layout */}
          <div className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100 md:col-span-2 lg:col-span-1">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <FiActivity className="text-primary-600 text-2xl" />
            </div>
            <h4 className="text-xl font-semibold text-gray-900 mb-3">
              Built for Smarter Mobility
            </h4>
            <p className="text-gray-600 leading-relaxed">
              Designed to support traffic awareness, planning, and management through data-driven insights.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center border border-gray-100">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to Transform Your Traffic Experience?
            </h3>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Join Flow Radar today and gain access to real-time traffic intelligence 
              that helps you make smarter mobility decisions.
            </p>
            <Button
              onClick={() => navigate('/signup')}
              className="px-10 py-4 text-lg flex items-center gap-2 mx-auto"
            >
              Create Your Account
              <FiArrowRight />
            </Button>
            <p className="text-sm text-gray-500 mt-4">
              Already have an account?{' '}
              <button
                onClick={() => navigate('/login')}
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                Sign in here
              </button>
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300">
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

export default LandingPage
