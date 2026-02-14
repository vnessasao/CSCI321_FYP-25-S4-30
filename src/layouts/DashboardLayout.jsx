import { useState, useEffect } from 'react'
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
  FiMessageSquare,
  FiSettings,
  FiBarChart2,
  FiCalendar,
  FiTrendingUp,
  FiDatabase,
  FiShield,
  FiUsers,
  FiCloud,
  FiActivity,
  FiLayers,
  FiServer,
  FiCode,
  FiZap,
  FiChevronDown,
  FiBell
} from 'react-icons/fi'

const DashboardLayout = () => {
  const { user, logout, token } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [moreDropdownOpen, setMoreDropdownOpen] = useState(false)
  const [notificationCount, setNotificationCount] = useState(0)
  const [showNotificationPopup, setShowNotificationPopup] = useState(false)

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

  // Debug: Log user role
  useEffect(() => {
    if (user) {
      console.log('Current user role:', user.role)
    }
  }, [user])

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
          { path: '/feedback', label: 'Submit Feedback', icon: FiHeart },
          { path: '/my-feedback', label: 'My Feedback', icon: FiMessageSquare },
        ]
      case 'government':
        return [
          { path: '/gov/dashboard', label: 'Dashboard', icon: FiBarChart2 },
          // { path: '/gov/heatmap', label: 'Congestion Heatmap', icon: FiMap }, // Hidden per user request
          { path: '/gov/roadwork', label: 'Input Roadwork Event', icon: FiCalendar },
          { path: '/gov/emas', label: 'EMAS Incident Status', icon: FiAlertCircle },
          // { path: '/gov/reports', label: 'Time-based Reports', icon: FiFileText }, // Hidden - not working
          { path: '/gov/data-upload', label: 'Upload & Analyze', icon: FiDatabase },
          { path: '/gov/bottlenecks', label: 'Bottleneck Finder', icon: FiAlertCircle },
          // { path: '/gov/jam-prediction', label: 'Jam Spread Prediction', icon: FiTrendingUp }, // Hidden - has errors
          { path: '/gov/trends', label: 'View Historical Trends', icon: FiBarChart2 },
          // { path: '/gov/simulation', label: 'Event Simulation', icon: FiZap }, // Hidden - not working
          { path: '/gov/weather', label: 'Weather Overlay', icon: FiCloud },
          // { path: '/gov/transport', label: 'Public Transport Overlay', icon: FiNavigation }, // Hidden per user request
          // { path: '/gov/alerts', label: 'Critical Alerts', icon: FiAlertCircle }, // Hidden per user request
          { path: '/gov/manage-users', label: 'Manage User Accounts', icon: FiUsers },
        ]
      case 'developer':
        return [
          { path: '/dev/algorithms', label: 'Algorithm Modules', icon: FiCode },
          { path: '/dev/performance', label: 'System Performance', icon: FiActivity },
          { path: '/dev/logs', label: 'Maintenance & Logs', icon: FiFileText },
          { path: '/dev/access-roles', label: 'Access Roles', icon: FiShield },
          { path: '/dev/backup', label: 'Backup & Restore', icon: FiDatabase },
          { path: '/dev/feedback', label: 'Feedback Management', icon: FiHeart },
        ]
      case 'analyst':
        return [
          { path: '/analyst/data-upload', label: 'Upload & Analyze', icon: FiDatabase },
          { path: '/analyst/bottlenecks', label: 'Bottleneck Finder', icon: FiAlertCircle },
          { path: '/analyst/jam-prediction', label: 'Jam Spread Prediction', icon: FiTrendingUp },
          { path: '/analyst/preprocess', label: 'Data Preprocessing', icon: FiSettings },
          { path: '/analyst/run-model', label: 'Run Traffic Flow Model', icon: FiActivity },
          { path: '/analyst/trends', label: 'View Historical Trends', icon: FiBarChart2 },
          { path: '/analyst/schedule', label: 'Schedule Automated Runs', icon: FiCalendar },
          { path: '/analyst/anomalies', label: 'Detect Anomalies', icon: FiZap },
        ]
      default:
        return []
    }
  }

  const menuItems = getMenuItems()
  const isPublicUser = user?.role === 'public' || user?.role === 'guest'
  const isGovernmentUser = user?.role === 'government'

  // For public and government users, use top navigation
  if (isPublicUser || isGovernmentUser) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Top Navigation Bar */}
        <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-[9999] relative" style={{ position: 'sticky', zIndex: 9999 }}>
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo and Menu Items */}
              <div className="flex items-center space-x-8">
                <h1 className="text-xl font-bold text-primary-600">Flow Radar</h1>
                
                {/* Desktop Navigation */}
                <div className="hidden md:flex items-center space-x-1">
                  {menuItems.slice(0, 4).map((item) => {
                    const Icon = item.icon
                    const isActive = location.pathname === item.path
                    return (
                      <button
                        key={item.path}
                        onClick={() => navigate(item.path)}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                          isActive
                            ? 'bg-primary-50 text-primary-700 font-medium'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <Icon size={18} />
                        <span>{item.label}</span>
                      </button>
                    )
                  })}
                  
                  {/* More Dropdown */}
                  {menuItems.length > 4 && (
                    <div className="relative">
                      <button
                        onClick={() => setMoreDropdownOpen(!moreDropdownOpen)}
                        className="flex items-center space-x-2 px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        <span>More</span>
                        <FiChevronDown size={16} />
                      </button>
                      
                      {moreDropdownOpen && (
                        <>
                          <div
                            className="fixed inset-0 z-[110]"
                            onClick={() => setMoreDropdownOpen(false)}
                          />
                          <div className="absolute top-full right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-[120]">
                            {menuItems.slice(4).map((item) => {
                              const Icon = item.icon
                              const isActive = location.pathname === item.path
                              return (
                                <button
                                  key={item.path}
                                  onClick={() => {
                                    navigate(item.path)
                                    setMoreDropdownOpen(false)
                                  }}
                                  className={`w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-50 transition-colors ${
                                    isActive ? 'text-primary-700 bg-primary-50' : 'text-gray-700'
                                  }`}
                                >
                                  <Icon size={18} />
                                  <span>{item.label}</span>
                                </button>
                              )
                            })}
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Mobile Menu Button */}
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="md:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
                >
                  {sidebarOpen ? <FiX size={24} /> : <FiMenu size={24} />}
                </button>
              </div>

              {/* User Info and Logout */}
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
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </nav>

        {/* Mobile Menu Overlay */}
        {sidebarOpen && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setSidebarOpen(false)} />
            <div className="fixed top-16 left-0 right-0 bg-white shadow-lg z-50 max-h-[calc(100vh-4rem)] overflow-y-auto">
              <nav className="py-4">
                {menuItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <button
                      key={item.path}
                      onClick={() => {
                        navigate(item.path)
                        setSidebarOpen(false)
                      }}
                      className={`w-full flex items-center space-x-3 px-6 py-3 transition-colors ${
                        isActive
                          ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <Icon size={20} />
                      <span>{item.label}</span>
                    </button>
                  )
                })}
              </nav>
            </div>
          </>
        )}

        {/* Main Content */}
        <main className="w-full">
          <div className="p-4 sm:p-6 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    )
  }

  // For admin users (government, analyst, developer), keep sidebar layout
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navbar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
              >
                {sidebarOpen ? <FiX size={24} /> : <FiMenu size={24} />}
              </button>
              <div className="ml-4 lg:ml-0">
                <h1 className="text-xl font-bold text-primary-600">Flow Radar</h1>
              </div>
            </div>
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
      </nav>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-50
            w-64 bg-white shadow-lg lg:shadow-none
            transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            transition-transform duration-200 ease-in-out
            lg:block
            pt-16 lg:pt-0
          `}
        >
          <nav className="h-full overflow-y-auto py-6">
            <ul className="space-y-1 px-3">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <li key={item.path}>
                    <button
                      onClick={() => {
                        navigate(item.path)
                        setSidebarOpen(false)
                      }}
                      className={`
                        w-full flex items-center space-x-3 px-4 py-3 rounded-lg
                        transition-colors
                        ${isActive
                          ? 'bg-primary-50 text-primary-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                        }
                      `}
                    >
                      <Icon size={20} />
                      <span>{item.label}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </nav>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 lg:ml-0">
          <div className="p-4 sm:p-6 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout

