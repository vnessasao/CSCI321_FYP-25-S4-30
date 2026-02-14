import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import ApiService from '../../api/apiService'
import Card from '../../components/Card'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import { toast, ToastContainer } from '../../components/Toast'
import { FiMessageSquare, FiClock, FiCheckCircle, FiTrash2 } from 'react-icons/fi'

const MyFeedback = () => {
  const { user } = useAuth()
  const [feedback, setFeedback] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [selectedFeedbackId, setSelectedFeedbackId] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadMyFeedback()
  }, [])

  const loadMyFeedback = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        toast.error('Please login to view your feedback')
        navigate('/login')
        return
      }

      const res = await ApiService.getMyFeedback(token)

      if (res.success) {
        setFeedback(res.data.feedback || [])
      } else {
        toast.error(res.error || 'Failed to load feedback')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to load feedback')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = (feedbackId) => {
    setSelectedFeedbackId(feedbackId)
    setDeleteModalOpen(true)
  }

  const confirmDelete = async () => {
    if (!selectedFeedbackId) return

    setDeleting(true)
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        toast.error('Please login to delete feedback')
        setDeleting(false)
        return
      }

      const res = await ApiService.deleteFeedback(selectedFeedbackId, token)

      if (res.success) {
        toast.success('Feedback deleted successfully')
        setDeleteModalOpen(false)
        setSelectedFeedbackId(null)
        loadMyFeedback() // Reload the list
      } else {
        toast.error(res.error || 'Failed to delete feedback')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to delete feedback')
    } finally {
      setDeleting(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning'
      case 'in_review':
        return 'info'
      case 'resolved':
        return 'success'
      case 'broadcast':
        return 'primary'
      default:
        return 'default'
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <ToastContainer />

      {/* Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">My Feedback</h2>
            <p className="text-gray-600">View your submitted feedback and responses from our team</p>
          </div>
          <Button onClick={() => navigate('/feedback')}>
            <FiMessageSquare className="w-4 h-4 mr-2" />
            Submit New Feedback
          </Button>
        </div>
      </Card>

      {/* Feedback List */}
      {feedback.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <FiMessageSquare className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Feedback Yet</h3>
            <p className="text-gray-600 mb-4">You haven't submitted any feedback yet.</p>
            <Button onClick={() => navigate('/feedback')}>
              Submit Your First Feedback
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {feedback.map((item) => (
            <Card key={item.id}>
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant={getStatusColor(item.status)}>
                        {item.status}
                      </Badge>
                      <Badge variant="info">{item.category}</Badge>
                      {item.rating && (
                        <span className="text-yellow-400 text-sm">
                          {'★'.repeat(item.rating)}
                          {'☆'.repeat(5 - item.rating)}
                        </span>
                      )}
                    </div>
                    {item.subject && (
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {item.subject}
                      </h3>
                    )}
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      <FiClock className="w-4 h-4" />
                      {user?.id === item.user_id ? 'Submitted' : 'Announced'}: {formatDate(item.created_at)}
                    </p>
                  </div>
                  {/* Delete Button - Only for user's own feedback */}
                  {user?.id === item.user_id && (
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="group relative p-2.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200 hover:shadow-md"
                      title="Delete feedback"
                    >
                      <FiTrash2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                      <span className="absolute -bottom-8 right-0 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                        Delete
                      </span>
                    </button>
                  )}
                </div>

                {/* Your Message */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    {user?.id === item.user_id ? 'Your Feedback:' : (item.is_broadcast ? 'System Announcement Message:' : 'Feedback:')}
                  </div>
                  <p className="text-gray-900">{item.message}</p>
                </div>

                {/* Admin Response */}
                {item.admin_response && (
                  <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FiCheckCircle className="w-5 h-5 text-blue-600" />
                      <div className="text-sm font-medium text-blue-900">
                        Response from Team
                        {item.responded_by_email && (
                          <span className="text-blue-700 ml-1">
                            ({item.responded_by_email})
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-blue-900">{item.admin_response}</p>
                    {item.responded_at && (
                      <p className="text-xs text-blue-600 mt-2">
                        Responded: {formatDate(item.responded_at)}
                      </p>
                    )}
                  </div>
                )}

                {/* Broadcast Message */}
                {item.is_broadcast && item.broadcast_message && (
                  <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-4">
                    <div className="text-sm font-medium text-yellow-900 mb-2">
                      📢 System-wide Announcement
                    </div>
                    <p className="text-yellow-900">{item.broadcast_message}</p>
                    {item.broadcast_at && (
                      <p className="text-xs text-yellow-600 mt-2">
                        Broadcast: {formatDate(item.broadcast_at)}
                      </p>
                    )}
                  </div>
                )}

                {/* Waiting Message */}
                {user?.id === item.user_id && !item.admin_response && item.status === 'pending' && (
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-sm text-gray-600">
                      ⏳ Your feedback is pending review. We'll respond soon!
                    </p>
                  </div>
                )}
                
                {user?.id === item.user_id && !item.admin_response && item.status === 'in_review' && (
                  <div className="bg-blue-50 rounded-lg p-3 text-center">
                    <p className="text-sm text-blue-700">
                      👀 Your feedback is currently being reviewed by our team
                    </p>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Summary */}
      {feedback.length > 0 && (
        <Card>
          <div className="text-center text-sm text-gray-600">
            Total Feedback Submitted: <span className="font-semibold">{feedback.length}</span>
          </div>
        </Card>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Feedback"
      >
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full">
                <FiTrash2 className="w-6 h-6 text-red-600" />
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-700">
                Are you sure you want to delete this feedback? This action cannot be undone.
              </p>
            </div>
          </div>
          <div className="flex justify-end space-x-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setDeleteModalOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={confirmDelete}
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Deleting...
                </>
              ) : (
                <>
                  <FiTrash2 className="w-4 h-4 mr-2" />
                  Delete
                </>
              )}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default MyFeedback
