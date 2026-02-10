import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast, ToastContainer } from '../components/Toast'
import Input from '../components/Input'
import Button from '../components/Button'
import Card from '../components/Card'
import Select from '../components/Select'
import ApiService from '../api/apiService'

const SignupPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [role, setRole] = useState('public')
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const roleOptions = [
    { value: 'public', label: 'Public' },
    { value: 'government', label: 'Government' },
    { value: 'developer', label: 'Developer' },
    { value: 'analyst', label: 'Analyst' }
  ]

  const validate = () => {
    const newErrors = {}
    
    if (!email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid'
    }
    
    if (!password.trim()) {
      newErrors.password = 'Password is required'
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters'
    }
    
    if (!confirmPassword.trim()) {
      newErrors.confirmPassword = 'Please confirm your password'
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }
    
    if (!role) {
      newErrors.role = 'Please select a role'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSignup = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setIsLoading(true)
    
    try {
      // Make API call to create user account
      const response = await ApiService.signup({
        email,
        password,
        role
      })
      
      console.log('Signup successful:', response)
      toast.success('Account created successfully! Please log in.')
      navigate('/login')
      
    } catch (error) {
      console.error('Signup failed:', error)
      toast.error(error.message || 'Failed to create account. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLoginRedirect = () => {
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <ToastContainer />
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600 mb-2">Flow Radar</h1>
          <p className="text-gray-600">Real-time traffic & congestion intelligence</p>
        </div>

        <form onSubmit={handleSignup} className="space-y-4">
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

          <Input
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            placeholder="Confirm your password"
            required
          />

          <Select
            label="Role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            error={errors.role}
            options={roleOptions}
          />

          <div className="space-y-3 pt-2">
            <Button 
              type="submit" 
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Creating Account...' : 'Sign Up'}
            </Button>
            
            <div className="text-center">
              <button
                type="button"
                onClick={handleLoginRedirect}
                className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
              >
                Already have an account? Login
              </button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  )
}

export default SignupPage