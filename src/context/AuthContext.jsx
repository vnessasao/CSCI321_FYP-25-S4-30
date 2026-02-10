import { createContext, useContext, useState, useEffect } from 'react'
import ApiService from '../api/apiService'

export const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(null)

  useEffect(() => {
    // Check for existing token and verify it on app startup
    const checkAuthentication = async () => {
      const storedToken = localStorage.getItem('auth_token')
      const storedUser = localStorage.getItem('trafficUser')
      const sessionUser = sessionStorage.getItem('trafficUser')

      // Check for guest session first
      if (sessionUser) {
        const guestData = JSON.parse(sessionUser)
        if (guestData.isGuest) {
          setUser(guestData)
          setLoading(false)
          return
        }
      }

      if (storedToken && storedUser) {
        try {
          // Verify token is still valid
          const response = await ApiService.verifyToken(storedToken)

          if (response.valid) {
            setToken(storedToken)
            setUser(JSON.parse(storedUser))
          } else {
            // Token is invalid, clear storage
            localStorage.removeItem('auth_token')
            localStorage.removeItem('trafficUser')
          }
        } catch (error) {
          console.error('Token verification failed:', error)
          // Clear invalid token and user data
          localStorage.removeItem('auth_token')
          localStorage.removeItem('trafficUser')
        }
      }

      setLoading(false)
    }

    checkAuthentication()
  }, [])

  const login = (email, role, authToken = null) => {
    const userData = { email, role }
    setUser(userData)
    localStorage.setItem('trafficUser', JSON.stringify(userData))

    // Store token if provided (from API login)
    if (authToken) {
      setToken(authToken)
      localStorage.setItem('auth_token', authToken)
    }
  }

  const loginAsGuest = () => {
    const guestData = { email: 'guest@trafficsense.com', role: 'guest', isGuest: true }
    setUser(guestData)
    // Don't store guest in localStorage so it doesn't persist
    sessionStorage.setItem('trafficUser', JSON.stringify(guestData))
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('trafficUser')
    localStorage.removeItem('auth_token')
    sessionStorage.removeItem('trafficUser')
  }

  const getAuthHeader = () => {
    return token ? `Bearer ${token}` : null
  }

  const value = {
    user,
    token,
    login,
    loginAsGuest,
    logout,
    loading,
    isAuthenticated: !!user,
    isGuest: user?.isGuest || false,
    getAuthHeader,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

