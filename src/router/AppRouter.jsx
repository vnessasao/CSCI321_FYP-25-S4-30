import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import LandingPage from '../pages/LandingPage'
import LandingPageMap from '../pages/LandingPageMap'
import Login from '../pages/Login'
import SignupPage from '../pages/SignupPage'
import GuestDashboard from '../pages/GuestDashboard'
import DashboardLayout from '../layouts/DashboardLayout'
import MapLayout from '../layouts/MapLayout'

// Public pages
import PublicDashboard from '../pages/publicPages/Dashboard'
import PublicMap from '../pages/publicPages/Map'
import PublicRouteStatus from '../pages/publicPages/RouteStatus'
import PublicHotspots from '../pages/publicPages/Hotspots'
import PublicReportIncident from '../pages/publicPages/ReportIncident'
import PublicFeedback from '../pages/publicPages/Feedback'
import MyFeedback from '../pages/publicPages/MyFeedback'

// Government pages
import GovDashboard from '../pages/gov/Dashboard'
import GovRoadwork from '../pages/gov/Roadwork'
import GovEMAS from '../pages/gov/EMAS'
import GovAlerts from '../pages/gov/Alerts'
import GovHeatmap from '../pages/gov/Heatmap'
import GovReports from '../pages/gov/Reports'
import GovSimulation from '../pages/gov/Simulation'
import GovWeather from '../pages/gov/Weather'
import GovTransport from '../pages/gov/Transport'
import GovManageUsers from '../pages/gov/ManageUsers'
import DataUpload from '../pages/gov/DataUpload'
import Bottlenecks from '../pages/gov/Bottlenecks'
import JamPrediction from '../pages/gov/JamPrediction'

// Developer pages
import DevAlgorithms from '../pages/dev/Algorithms'
import DevPerformance from '../pages/dev/Performance'
import DevAccessRoles from '../pages/dev/AccessRoles'
import DevFeedback from '../pages/dev/Feedback'
import DevLogs from '../pages/dev/Logs'
import DevVisualization from '../pages/dev/Visualization'
import DevBackup from '../pages/dev/Backup'
import DevIntegrations from '../pages/dev/Integrations'
import DevDeployments from '../pages/dev/Deployments'

// Analyst pages
import AnalystPreprocess from '../pages/analyst/Preprocess'
import AnalystRunModel from '../pages/analyst/RunModel'
import AnalystTrends from '../pages/analyst/Trends'
import AnalystSchedule from '../pages/analyst/Schedule'
import AnalystAnomalies from '../pages/analyst/Anomalies'

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/" replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return children
}

const GuestOrPublicRoute = ({ children }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/guest" replace />
  }

  // Allow guest, public, and any authenticated user
  return children
}

const AppRouter = () => {
  return (
    <Routes>
      {/* Landing page with full-screen map */}
      <Route path="/" element={<LandingPageMap />} />
      <Route path="/landingpage/map" element={<LandingPageMap />} />
      <Route path="/about" element={<LandingPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/guest" element={<GuestDashboard />} />
      
      {/* Public routes at root level - accessible by guest and authenticated users */}
      <Route
        path="/dashboard"
        element={
          <GuestOrPublicRoute>
            <MapLayout />
          </GuestOrPublicRoute>
        }
      >
        <Route index element={<PublicDashboard />} />
      </Route>

      <Route
        path="/map"
        element={
          <GuestOrPublicRoute>
            <MapLayout />
          </GuestOrPublicRoute>
        }
      >
        <Route index element={<PublicMap />} />
      </Route>

      <Route
        path="/route-status"
        element={
          <GuestOrPublicRoute>
            <MapLayout />
          </GuestOrPublicRoute>
        }
      >
        <Route index element={<PublicRouteStatus />} />
      </Route>

      <Route
        path="/hotspots"
        element={
          <GuestOrPublicRoute>
            <MapLayout />
          </GuestOrPublicRoute>
        }
      >
        <Route index element={<PublicHotspots />} />
      </Route>

      <Route
        path="/report-incident"
        element={
          <GuestOrPublicRoute>
            <MapLayout />
          </GuestOrPublicRoute>
        }
      >
        <Route index element={<PublicReportIncident />} />
      </Route>

      <Route
        path="/feedback"
        element={
          <GuestOrPublicRoute>
            <MapLayout />
          </GuestOrPublicRoute>
        }
      >
        <Route index element={<PublicFeedback />} />
      </Route>

      <Route
        path="/my-feedback"
        element={
          <ProtectedRoute allowedRoles={['public', 'analyst', 'government', 'developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<MyFeedback />} />
      </Route>

      {/* Legacy public routes - redirect to root level */}
      <Route
        path="/public/*"
        element={
          <ProtectedRoute allowedRoles={['public', 'guest']}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Navigate to="/dashboard" replace />} />
        <Route path="map" element={<Navigate to="/map" replace />} />
        <Route path="route-status" element={<Navigate to="/route-status" replace />} />
        <Route path="hotspots" element={<Navigate to="/hotspots" replace />} />
        <Route path="report-incident" element={<Navigate to="/report-incident" replace />} />
        <Route path="feedback" element={<Navigate to="/feedback" replace />} />
      </Route>

      {/* Government routes */}
      <Route
        path="/gov/*"
        element={
          <ProtectedRoute allowedRoles={['government']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<GovDashboard />} />
        <Route path="roadwork" element={<GovRoadwork />} />
        <Route path="emas" element={<GovEMAS />} />
        <Route path="alerts" element={<GovAlerts />} />
        <Route path="heatmap" element={<GovHeatmap />} />
        <Route path="reports" element={<GovReports />} />
        <Route path="simulation" element={<GovSimulation />} />
        <Route path="weather" element={<GovWeather />} />
        <Route path="transport" element={<GovTransport />} />
        <Route path="manage-users" element={<GovManageUsers />} />
        <Route path="data-upload" element={<DataUpload />} />
        <Route path="bottlenecks" element={<Bottlenecks />} />
        <Route path="jam-prediction" element={<JamPrediction />} />
        <Route path="trends" element={<AnalystTrends />} />
      </Route>

      {/* Developer routes with MapLayout (top nav only, no sidebar) */}
      <Route
        path="/dev/algorithms"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DevAlgorithms />} />
      </Route>

      {/* Performance route - kept for future use
      <Route
        path="/dev/performance"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DevPerformance />} />
      </Route>
      */}

      {/* Logs route - kept for future use
      <Route
        path="/dev/logs"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DevLogs />} />
      </Route>
      */}

      <Route
        path="/dev/backup"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DevBackup />} />
      </Route>

      <Route
        path="/dev/access-roles"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DevAccessRoles />} />
      </Route>

      <Route
        path="/dev/feedback"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DevFeedback />} />
      </Route>

      {/* Developer routes - uses DashboardLayout with sidebar (for other pages) */}
      <Route
        path="/dev/*"
        element={
          <ProtectedRoute allowedRoles={['developer']}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="algorithms" replace />} />
        <Route path="visualization" element={<DevVisualization />} />
        <Route path="integrations" element={<DevIntegrations />} />
        <Route path="deployments" element={<DevDeployments />} />
      </Route>

      {/* Analyst routes - uses MapLayout with top navigation */}
      <Route
        path="/analyst/*"
        element={
          <ProtectedRoute allowedRoles={['analyst']}>
            <MapLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="data-upload" replace />} />
        <Route path="data-upload" element={<DataUpload />} />
        <Route path="bottlenecks" element={<Bottlenecks />} />
        <Route path="jam-prediction" element={<JamPrediction />} />
        <Route path="preprocess" element={<AnalystPreprocess />} />
        <Route path="run-model" element={<AnalystRunModel />} />
        <Route path="trends" element={<AnalystTrends />} />
        <Route path="schedule" element={<AnalystSchedule />} />
        <Route path="anomalies" element={<AnalystAnomalies />} />
      </Route>
    </Routes>
  )
}

export default AppRouter

