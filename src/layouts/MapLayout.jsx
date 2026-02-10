import { useState, useRef, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ApiService from '../api/apiService'
import {
  FiMenu,
  FiX,
  FiLogOut,
  FiMap,
  FiNavigation,
  FiAlertCircle,
  FiFileText,
  FiHeart,
  FiBarChart2,
  FiChevronDown,
  FiBell,
  FiDatabase,
  FiShield,
  FiCloud,
  FiUsers
} from 'react-icons/fi'

const MapLayout = () => {
  const { user, logout, token } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [notificationCount, setNotificationCount] = useState(0)
  const [showNotificationPopup, setShowNotificationPopup] = useState(false)
  const dropdownRef = useRef(null)

  // Fetch notification count
  useEffect(() => {
    const fetchNotifications = async () => {
      if (token && user) {
        try {
          const response = await ApiService.getNotificationCount(token)
          if (response.success) {
            setNotificationCount(response.data.count)
          }
        } catch (error) {
          console.error('Failed to fetch notifications:', error)
        }
      }
    }

    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [token, user])

  const handleNotificationClick = async () => {
    setShowNotificationPopup(!showNotificationPopup)
    if (notificationCount > 0) {
      try {
        await ApiService.markNotificationsRead(token)
        setNotificationCount(0)
      } catch (error) {
        console.error('Failed to mark notifications as read:', error)
      }
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const getMenuItems = () => {
    if (!user) return []

    switch (user.role) {
      case 'public':
      case 'guest':
        return [
          { path: '/dashboard', label: 'Dashboard', icon: FiBarChart2 },
          { path: '/map', label: 'Live Congestion Map', icon: FiMap },
          { path: '/route-status', label: 'Route Traffic Status', icon: FiNavigation },
          { path: '/hotspots', label: 'Daily Top Hotspots', icon: FiAlertCircle },
          { path: '/report-incident', label: 'Report Road Incident', icon: FiFileText },
          { path: '/feedback', label: 'Feedback', icon: FiHeart },
          { path: '/my-feedback', label: 'My Feedback', icon: FiHeart },
        ]
      case 'government':
        return [
          { path: '/gov/dashboard', label: 'Dashboard', icon: FiBarChart2 },
          { path: '/map', label: 'Live Congestion Map', icon: FiMap },
          // { path: '/gov/heatmap', label: 'Congestion Heatmap', icon: FiMap }, // Hidden per user request
          { path: '/gov/roadwork', label: 'Roadwork Event', icon: FiFileText },
          { path: '/gov/emas', label: 'EMAS Incident', icon: FiAlertCircle },
          // { path: '/gov/reports', label: 'Reports', icon: FiFileText }, // Hidden per user request
          { path: '/gov/data-upload', label: 'Upload & Analyze', icon: FiDatabase },
          { path: '/gov/bottlenecks', label: 'Bottleneck Finder', icon: FiAlertCircle },
          { path: '/gov/jam-prediction', label: 'Jam Prediction', icon: FiNavigation },
          { path: '/gov/trends', label: 'View Historical Trends', icon: FiBarChart2 },
          { path: '/gov/weather', label: 'Weather Overlay', icon: FiCloud },
          // { path: '/gov/transport', label: 'Public Transport Overlay', icon: FiNavigation }, // Hidden per user request
          { path: '/gov/manage-users', label: 'Manage User Accounts', icon: FiUsers },
        ]
      case 'developer':
        return [
          { path: '/dev/algorithms', label: 'Algorithms', icon: FiBarChart2 },
          { path: '/map', label: 'Live Congestion Map', icon: FiMap },
          { path: '/dev/backup', label: 'Backup & Restore', icon: FiDatabase },
          { path: '/dev/access-roles', label: 'Access Roles', icon: FiShield },
          { path: '/dev/feedback', label: 'Feedback Management', icon: FiHeart },
          // { path: '/dev/performance', label: 'Performance', icon: FiBarChart2 }, // Kept for future use
          // { path: '/dev/logs', label: 'Logs', icon: FiFileText }, // Kept for future use
        ]
      case 'analyst':
        return [
          { path: '/analyst/data-upload', label: 'Upload & Analyze', icon: FiBarChart2 },
          { path: '/map', label: 'Live Congestion Map', icon: FiMap },
          { path: '/analyst/bottlenecks', label: 'Bottleneck Finder', icon: FiAlertCircle },
          { path: '/analyst/jam-prediction', label: 'Jam Prediction', icon: FiNavigation },
          { path: '/analyst/preprocess', label: 'Data Preprocessing', icon: FiDatabase },
          { path: '/analyst/run-model', label: 'Run Traffic Flow Model', icon: FiBarChart2 },
          { path: '/analyst/trends', label: 'View Historical Trends', icon: FiBarChart2 },
          { path: '/analyst/schedule', label: 'Schedule Automated Runs', icon: FiFileText },
          { path: '/analyst/anomalies', label: 'Detect Anomalies', icon: FiAlertCircle },
        ]
      default:
        return []
    }
  }

  const menuItems = getMenuItems()
  const visibleItems = menuItems.slice(0, 4) // Show first 4 items in navbar
  const dropdownItems = menuItems.slice(4) // Rest go in dropdown

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Navbar with Menu Items */}
      <nav className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Logo + Menu Items */}
            <div className="flex items-center space-x-1">
              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
              >
                {mobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
              </button>

              {/* Logo */}
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-primary-600">Flow Radar</h1>
              </div>

              {/* Desktop Menu Items */}
              <div className="hidden lg:flex items-center ml-8 space-x-1">
                {visibleItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={`
                        flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium
                        transition-colors whitespace-nowrap
                        ${isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-700 hover:bg-gray-100'
                        }
                      `}
                    >
                      <Icon size={16} />
                      <span>{item.label}</span>
                    </button>
                  )
                })}

                {/* More dropdown for additional items */}
                {dropdownItems.length > 0 && (
                  <div className="relative" ref={dropdownRef}>
                    <button
                      onClick={() => setDropdownOpen(!dropdownOpen)}
                      className="flex items-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      <span>More</span>
                      <FiChevronDown size={16} className={`transform transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {dropdownOpen && (
                      <div className="absolute left-0 mt-1 w-72 max-h-64 overflow-y-auto bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-[9999]">
                        {dropdownItems.map((item) => {
                          const Icon = item.icon
                          const isActive = location.pathname === item.path
                          return (
                            <button
                              key={item.path}
                              onClick={() => {
                                navigate(item.path)
                                setDropdownOpen(false)
                              }}
                              className={`
                                w-full flex items-center space-x-3 px-4 py-2 text-sm
                                ${isActive
                                  ? 'bg-primary-50 text-primary-700'
                                  : 'text-gray-700 hover:bg-gray-100'
                                }
                              `}
                            >
                              <Icon size={16} />
                              <span>{item.label}</span>
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Right: Notification Bell + User Info + Logout */}
            <div className="flex items-center space-x-4">
              {/* Notification Bell - Hidden for developers */}
              {user?.role !== 'developer' && (
                <div className="relative">
                  <button
                    onClick={handleNotificationClick}
                    className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Notifications"
                  >
                    <FiBell size={20} />
                    {notificationCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                        {notificationCount > 9 ? '9+' : notificationCount}
                      </span>
                    )}
                  </button>
                  
                  {/* Notification Popup */}
                  {showNotificationPopup && (
                    <>
                      <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-[9999]">
                        <div className="p-4 border-b border-gray-200">
                          <h3 className="font-semibold text-gray-900">Notifications</h3>
                        </div>
                        <div className="p-4">
                          <p className="text-sm text-gray-600 mb-3">
                            You have {notificationCount} new notification{notificationCount !== 1 ? 's' : ''}.
                          </p>
                          <button
                            onClick={() => {
                              navigate('/my-feedback')
                              setShowNotificationPopup(false)
                          }}
                          className="w-full text-sm text-blue-600 hover:text-blue-700 text-left font-medium"
                        >
                          View My Feedback →
                        </button>
                      </div>
                    </div>
                    <div 
                      className="fixed inset-0 z-[9998]"
                      onClick={() => setShowNotificationPopup(false)}
                    />
                  </>
                )}
                </div>
              )}

              <div className="hidden sm:block text-sm text-gray-600">
                <span className="font-medium">{user?.role || 'Guest'}</span>
                {user?.email && <span className="ml-2 text-gray-400">• {user.email}</span>}
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <FiLogOut size={18} />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 bg-white">
            <div className="px-4 py-2 space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <button
                    key={item.path}
                    onClick={() => {
                      navigate(item.path)
                      setMobileMenuOpen(false)
                    }}
                    className={`
                      w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm
                      ${isActive
                        ? 'bg-primary-50 text-primary-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </nav>

      {/* Main Content - Full width, no sidebar */}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  )
}

export default MapLayout
