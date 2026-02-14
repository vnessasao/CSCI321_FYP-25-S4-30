import { FiInbox } from 'react-icons/fi'

const EmptyState = ({ message = 'No data available', icon: Icon = FiInbox }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-500">
      <Icon size={48} className="mb-4 text-gray-400" />
      <p className="text-lg font-medium">{message}</p>
    </div>
  )
}

export default EmptyState

