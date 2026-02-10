import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { toast, ToastContainer } from '../components/Toast'
import Input from '../components/Input'
import Button from '../components/Button'
import Card from '../components/Card'
import ApiService from '../api/apiService'

const Login = () => {
  const [role, setRole] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [twoFA, setTwoFA] = useState('')
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const validate = () => {
    const newErrors = {}
    if (!email.trim()) {
      newErrors.email = 'Email is required'
    }
    if (!password.trim()) {
      newErrors.password = 'Password is required'
    }
    if (!role.trim()) {
      newErrors.role = 'Please select a role'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setIsLoading(true)
    
    try {
      // Make API call to authenticate user
      const response = await ApiService.login({
        email,
        password,
        role
      })
      
      console.log('Login successful:', response)
      
      // Store JWT token and user data
      login(response.user.email, response.user.role, response.token)
      
      // Redirect to map page after login for all roles
      toast.success('Login successful!')
      navigate('/map')
      
    } catch (error) {
      console.error('Login failed:', error)
      toast.error(error.message || 'Login failed. Please check your credentials.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGuestAccess = () => {
    login('guest@example.com', 'guest')
    toast.success('Continuing as guest')
    navigate('/map')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <ToastContainer />
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600 mb-2">Flow Radar</h1>
          <p className="text-gray-600">Real-time traffic & congestion intelligence</p>
        </div>

        {/* Role Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Role
          </label>
          <div className="grid grid-cols-2 gap-2">
            {['public', 'government', 'developer', 'analyst'].map((r) => (
              <button
                key={r}
                onClick={() => setRole(r)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  role === r
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </button>
            ))}
          </div>
          {errors.role && (
            <p className="mt-2 text-sm text-red-600">{errors.role}</p>
          )}
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            placeholder="Enter your email"
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            placeholder="Enter your password"
            required
          />

          {role === 'government' && (
            <Input
              label="2FA Token (Optional)"
              type="text"
              value={twoFA}
              onChange={(e) => setTwoFA(e.target.value)}
              placeholder="Enter 2FA token"
            />
          )}

          <div className="space-y-2">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Logging in...' : 'Login'}
            </Button>
            {role === 'public' && (
              <Button
                type="button"
                variant="secondary"
                className="w-full"
                onClick={handleGuestAccess}
              >
                Continue as Guest
              </Button>
            )}
          </div>
          
          <div className="text-center mt-4">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
            >
              Don't have an account? Sign Up
            </button>
          </div>
        </form>
      </Card>
    </div>
  )
}

export default Login

