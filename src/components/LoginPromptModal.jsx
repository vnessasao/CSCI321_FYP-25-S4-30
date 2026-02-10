import { useNavigate } from 'react-router-dom'
import { FiX, FiLock } from 'react-icons/fi'
import Button from './Button'

const LoginPromptModal = ({ isOpen, onClose, feature = 'this feature' }) => {
  const navigate = useNavigate()

  if (!isOpen) return null

  const handleLogin = () => {
    navigate('/login')
  }

  const handleSignup = () => {
    navigate('/signup')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close"
        >
          <FiX className="text-2xl" />
        </button>

        {/* Content */}
        <div className="p-8 text-center">
          {/* Icon */}
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <FiLock className="text-primary-600 text-3xl" />
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            Login Required
          </h2>

          {/* Description */}
          <p className="text-gray-600 mb-6">
            You need to create an account or login to use {feature}.
            Create a free account to unlock all features!
          </p>

          {/* Benefits */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold text-gray-900 mb-2">With an account you can:</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Save and manage your favorite routes</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Bookmark locations and get personalized traffic updates</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Report incidents and contribute to the community</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Access advanced analytics and insights</span>
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleSignup}
              className="w-full"
            >
              Create Free Account
            </Button>
            <Button
              variant="outline"
              onClick={handleLogin}
              className="w-full"
            >
              Login to Existing Account
            </Button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-sm font-medium"
            >
              Continue as Guest
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPromptModal
