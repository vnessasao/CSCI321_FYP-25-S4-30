import { useState, useEffect } from 'react'
import { FiCheckCircle, FiAlertCircle, FiX } from 'react-icons/fi'

let toastId = 0
const toasts = []
const listeners = []

export const toast = {
  success: (message) => addToast('success', message),
  error: (message) => addToast('error', message),
  info: (message) => addToast('info', message),
  warning: (message) => addToast('warning', message),
}

const addToast = (type, message) => {
  const id = toastId++
  toasts.push({ id, type, message })
  listeners.forEach((listener) => listener([...toasts]))
  
  setTimeout(() => {
    removeToast(id)
  }, 5000)
}

const removeToast = (id) => {
  const index = toasts.findIndex((t) => t.id === id)
  if (index > -1) {
    toasts.splice(index, 1)
    listeners.forEach((listener) => listener([...toasts]))
  }
}

export const ToastContainer = () => {
  const [toastList, setToastList] = useState([])

  useEffect(() => {
    listeners.push(setToastList)
    return () => {
      const index = listeners.indexOf(setToastList)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [])

  const icons = {
    success: FiCheckCircle,
    error: FiAlertCircle,
    info: FiAlertCircle,
    warning: FiAlertCircle,
  }

  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toastList.map((toast) => {
        const Icon = icons[toast.type]
        return (
          <div
            key={toast.id}
            className={`flex items-center space-x-3 px-4 py-3 rounded-lg border shadow-lg min-w-[300px] ${colors[toast.type]}`}
          >
            <Icon size={20} />
            <p className="flex-1 text-sm font-medium">{toast.message}</p>
            <button
              onClick={() => removeToast(toast.id)}
              className="hover:opacity-70"
            >
              <FiX size={18} />
            </button>
          </div>
        )
      })}
    </div>
  )
}

