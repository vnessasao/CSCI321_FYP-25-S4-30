import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import AppRouter from './router/AppRouter'
import { ToastContainer } from './components/Toast'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter />
        <ToastContainer />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App

