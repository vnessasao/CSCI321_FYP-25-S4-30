import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import Select from '../../components/Select'
import Input from '../../components/Input'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import { FiSend, FiMessageSquare, FiRefreshCw, FiCheck, FiX, FiEdit } from 'react-icons/fi'

const DevFeedback = () => {
  const { token } = useAuth()
  const [feedback, setFeedback] = useState([])
  const [broadcasts, setBroadcasts] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [categories, setCategories] = useState([])
  const [statuses, setStatuses] = useState([])
  const [respondModalOpen, setRespondModalOpen] = useState(false)
  const [broadcastModalOpen, setBroadcastModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedFeedback, setSelectedFeedback] = useState(null)
  const [responseText, setResponseText] = useState('')
  const [editData, setEditData] = useState({
    subject: '',
    message: '',
    category: '',
    broadcast: false
  })
  const [broadcastData, setBroadcastData] = useState({
    title: '',
    message: '',
    priority: 'normal',
    target_roles: []
  })
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0, pages: 1 })
  const [filters, setFilters] = useState({
    category: '',
    status: ''
  })
  const [activeTab, setActiveTab] = useState('pending')

  useEffect(() => {
    if (token) {
      loadInitialData()
    }
  }, [token])

  useEffect(() => {
    if (token) {
      if (activeTab === 'pending' || activeTab === 'resolved') {
        loadFeedback()
      } else if (activeTab === 'broadcasts') {
        loadBroadcasts()
      }
    }
  }, [filters, pagination.page, activeTab, token])

  const loadInitialData = async () => {
    try {
      const [categoriesRes, statusesRes, statsRes] = await Promise.all([
        ApiService.getFeedbackCategories(token),
        ApiService.getFeedbackStatuses(token),
        ApiService.getFeedbackStats(token)
      ])

      if (categoriesRes.success) setCategories(categoriesRes.data || [])
      if (statusesRes.success) setStatuses(statusesRes.data || [])
      if (statsRes.success) setStats(statsRes.data)
    } catch (err) {
      console.error('Failed to load initial data:', err)
    }
  }

  const loadFeedback = async () => {
    setLoading(true)
    try {
      // Filter by status based on active tab
      const statusFilter = activeTab === 'pending' ? 'pending' : activeTab === 'resolved' ? 'resolved' : filters.status
      
      const res = await ApiService.getAllFeedback(token, {
        page: pagination.page,
        limit: pagination.limit,
        ...filters,
        status: statusFilter
      })

      if (res.success) {
        setFeedback(res.data.feedback || [])
        setPagination(prev => ({
          ...prev,
          total: res.data.pagination?.total || 0,
          pages: res.data.pagination?.pages || 1
        }))
      }
    } catch (err) {
      toast.error('Failed to load feedback')
    } finally {
      setLoading(false)
    }
  }

  const loadBroadcasts = async () => {
    setLoading(true)
    try {
      const res = await ApiService.getBroadcasts(token)

      if (res.success) {
        setBroadcasts(res.data.broadcasts || [])
      }
    } catch (err) {
      toast.error('Failed to load broadcasts')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await ApiService.getFeedbackStats(token)
      if (res.success) setStats(res.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const openRespondModal = (fb) => {
    setSelectedFeedback(fb)
    setResponseText('')
    setRespondModalOpen(true)
  }

  const handleRespond = async () => {
    if (!selectedFeedback || !responseText.trim()) {
      toast.error('Please enter a response')
      return
    }

    if (!token) {
      toast.error('Authentication required. Please log in again.')
      return
    }

    try {
      console.log('Responding to feedback:', selectedFeedback.id, 'with token:', token ? 'present' : 'missing')
      const res = await ApiService.respondToFeedback(selectedFeedback.id, responseText, token)
      console.log('Response from API:', res)

      if (res.success) {
        toast.success('Response sent successfully - Status updated to resolved')
        setRespondModalOpen(false)
        setSelectedFeedback(null)
        setResponseText('')
        await loadFeedback()
        await loadStats()
      } else {
        console.error('Failed to respond:', res)
        toast.error(res.error || 'Failed to send response')
      }
    } catch (err) {
      console.error('Error responding to feedback:', err)
      toast.error(err.message || 'Failed to send response')
    }
  }

  const handleUpdateStatus = async (feedbackId, newStatus) => {
    try {
      const res = await ApiService.updateFeedbackStatus(feedbackId, newStatus, token)

      if (res.success) {
        toast.success(`Status updated to ${newStatus}`)
        loadFeedback()
        loadStats()
      } else {
        toast.error(res.error || 'Failed to update status')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to update status')
    }
  }

  const handleBroadcast = async () => {
    if (!broadcastData.title.trim() || !broadcastData.message.trim()) {
      toast.error('Please fill in title and message')
      return
    }

    try {
      const res = await ApiService.broadcastFeedback(broadcastData, token)

      if (res.success) {
        toast.success('Broadcast sent successfully')
        setBroadcastModalOpen(false)
        setBroadcastData({ title: '', message: '', priority: 'normal', target_roles: [] })
        loadBroadcasts()
      } else {
        toast.error(res.error || 'Failed to send broadcast')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to send broadcast')
    }
  }

  const openEditModal = (fb) => {
    setSelectedFeedback(fb)
    setEditData({
      subject: fb.subject || '',
      message: fb.message || '',
      category: fb.category || '',
      broadcast: false
    })
    setEditModalOpen(true)
  }

  const handleUpdateFeedback = async () => {
    if (!editData.message.trim()) {
      toast.error('Message cannot be empty')
      return
    }

    try {
      // Use respondToFeedback which automatically sets status to 'resolved'
      const res = await ApiService.respondToFeedback(selectedFeedback.id, editData.message, token)

      if (res.success) {
        // If broadcast is checked, also send broadcast
        if (editData.broadcast) {
          try {
            const broadcastRes = await ApiService.broadcastExistingFeedback(
              selectedFeedback.id,
              editData.message,
              token
            )
            if (broadcastRes.success) {
              toast.success('Response sent and broadcast successfully!')
            } else {
              toast.warning('Response sent but broadcast failed')
            }
          } catch (broadcastErr) {
            console.error('Broadcast error:', broadcastErr)
            toast.warning('Response sent but broadcast failed')
          }
        } else {
          toast.success('Response sent successfully - Status updated to resolved')
        }
        
        setEditModalOpen(false)
        setSelectedFeedback(null)
        setEditData({ subject: '', message: '', category: '', broadcast: false })
        await loadFeedback()
        await loadStats()
        if (editData.broadcast) {
          await loadBroadcasts()
        }
      } else {
        toast.error(res.error || 'Failed to send response')
      }
    } catch (err) {
      console.error('Error sending response:', err)
      toast.error(err.message || 'Failed to send response')
    }
  }

  const getStatusVariant = (status) => {
    switch (status) {
      case 'new': return 'info'
      case 'in_progress': return 'warning'
      case 'resolved': return 'success'
      case 'closed': return 'default'
      default: return 'default'
    }
  }

  const getPriorityVariant = (priority) => {
    switch (priority) {
      case 'high': return 'danger'
      case 'normal': return 'info'
      case 'low': return 'default'
      default: return 'default'
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }

  const feedbackColumns = [
    {
      key: 'category',
      label: 'Category',
      render: (value) => <Badge variant="info">{value}</Badge>
    },
    {
      key: 'subject',
      label: 'Subject',
      render: (value) => <div className="font-medium">{value || '-'}</div>
    },
    {
      key: 'message',
      label: 'Message',
      render: (value) => <div className="max-w-md truncate">{value}</div>
    },
    {
      key: 'user_email',
      label: 'From',
      render: (value) => <span className="text-sm">{value || 'Anonymous'}</span>
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => (
        <Badge variant={getStatusVariant(value)}>{value}</Badge>
      )
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (value) => <span className="text-sm">{formatDate(value)}</span>
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          <Button
            size="sm"
            variant="info"
            onClick={() => openEditModal(row)}
            title="Send Response to User"
          >
            <FiMessageSquare className="w-4 h-4" />
          </Button>
          {row.status === 'new' && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => handleUpdateStatus(row.id, 'in_progress')}
              title="Mark In Progress"
            >
              <FiCheck className="w-4 h-4" />
            </Button>
          )}
          {row.status === 'in_progress' && (
            <Button
              size="sm"
              variant="success"
              onClick={() => handleUpdateStatus(row.id, 'resolved')}
              title="Mark Resolved"
            >
              <FiCheck className="w-4 h-4" />
            </Button>
          )}
        </div>
      )
    }
  ]

  const broadcastColumns = [
    {
      key: 'title',
      label: 'Title',
      render: (value) => <div className="font-medium">{value}</div>
    },
    {
      key: 'message',
      label: 'Message',
      render: (value) => <div className="max-w-md truncate">{value}</div>
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (value) => <Badge variant={getPriorityVariant(value)}>{value}</Badge>
    },
    {
      key: 'target_roles',
      label: 'Target',
      render: (value) => (
        <div className="flex flex-wrap gap-1">
          {value && value.length > 0 ? (
            value.map((role, idx) => (
              <Badge key={idx} variant="default">{role}</Badge>
            ))
          ) : (
            <span className="text-sm text-gray-500">All users</span>
          )}
        </div>
      )
    },
    {
      key: 'created_at',
      label: 'Sent',
      render: (value) => <span className="text-sm">{formatDate(value)}</span>
    }
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Feedback Management</h2>
            <p className="text-gray-600">View and manage user feedback and broadcasts</p>
          </div>
          <div className="flex space-x-2">
            <Button onClick={() => activeTab === 'feedback' ? loadFeedback() : loadBroadcasts()} variant="secondary">
              <FiRefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setBroadcastModalOpen(true)}>
              <FiSend className="w-4 h-4 mr-2" />
              New Broadcast
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total || 0}</div>
              <div className="text-sm text-gray-500">Total Feedback</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.by_status?.pending || 0}</div>
              <div className="text-sm text-gray-500">Pending</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.by_status?.resolved || 0}</div>
              <div className="text-sm text-gray-500">Resolved</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.by_status?.broadcast || 0}</div>
              <div className="text-sm text-gray-500">Broadcasts</div>
            </div>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Card>
        <div className="flex space-x-4 border-b">
          <button
            className={`pb-2 px-1 ${activeTab === 'pending' ? 'border-b-2 border-blue-500 text-blue-600 font-medium' : 'text-gray-500'}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending Feedback
          </button>
          <button
            className={`pb-2 px-1 ${activeTab === 'resolved' ? 'border-b-2 border-green-500 text-green-600 font-medium' : 'text-gray-500'}`}
            onClick={() => setActiveTab('resolved')}
          >
            Resolved Feedback
          </button>
          <button
            className={`pb-2 px-1 ${activeTab === 'broadcasts' ? 'border-b-2 border-purple-500 text-purple-600 font-medium' : 'text-gray-500'}`}
            onClick={() => setActiveTab('broadcasts')}
          >
            Broadcasts
          </button>
        </div>
      </Card>

      {/* Filters (only for feedback tabs) */}
      {(activeTab === 'pending' || activeTab === 'resolved') && (
        <Card>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="w-40">
              <Select
                label="Category"
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                options={[
                  { value: '', label: 'All Categories' },
                  ...categories.map(c => ({ value: c, label: c }))
                ]}
              />
            </div>
            <div className="w-40">
              <Select
                label="Status"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                options={[
                  { value: '', label: 'All Statuses' },
                  ...statuses.map(s => ({ value: s, label: s }))
                ]}
              />
            </div>
          </div>
        </Card>
      )}

      {/* Content Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <Table
              columns={(activeTab === 'pending' || activeTab === 'resolved') ? feedbackColumns : broadcastColumns}
              data={(activeTab === 'pending' || activeTab === 'resolved') ? feedback : broadcasts}
              emptyMessage={(activeTab === 'pending' || activeTab === 'resolved') ? `No ${activeTab} feedback found` : 'No broadcasts found'}
            />

            {/* Pagination (only for feedback) */}
            {(activeTab === 'pending' || activeTab === 'resolved') && pagination.pages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="text-sm text-gray-500">
                  Showing {((pagination.page - 1) * pagination.limit) + 1} to{' '}
                  {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                  {pagination.total} entries
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pagination.page === 1}
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 text-sm">
                    Page {pagination.page} of {pagination.pages}
                  </span>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pagination.page === pagination.pages}
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Respond Modal */}
      <Modal
        isOpen={respondModalOpen}
        onClose={() => setRespondModalOpen(false)}
        title="Respond to Feedback"
      >
        <div className="space-y-4">
          {selectedFeedback && (
            <div className="p-3 bg-gray-50 rounded">
              <div className="text-sm text-gray-500 mb-1">Original Message:</div>
              <div className="text-sm">{selectedFeedback.message}</div>
              <div className="text-xs text-gray-400 mt-2">
                From: {selectedFeedback.user_email || 'Anonymous'} | {formatDate(selectedFeedback.created_at)}
              </div>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Your Response
            </label>
            <textarea
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              className="w-full border rounded-md p-2 text-sm"
              rows={4}
              placeholder="Type your response..."
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setRespondModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRespond}>Send Response</Button>
          </div>
        </div>
      </Modal>

      {/* Edit Feedback Modal (SD-19) - Now Response Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Send Response to User"
      >
        <div className="space-y-4">
          {selectedFeedback && (
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <div className="text-sm font-semibold text-gray-700 mb-2">
                Original User Feedback:
              </div>
              <div className="text-sm text-gray-600 mb-2">
                <strong>Subject:</strong> {selectedFeedback.subject || 'No subject'}
              </div>
              <div className="text-sm text-gray-600 mb-2">
                <strong>Category:</strong> {selectedFeedback.category}
              </div>
              <div className="p-2 bg-white rounded border border-gray-200 mb-2">
                <div className="text-sm text-gray-800 whitespace-pre-wrap">{selectedFeedback.message}</div>
              </div>
              <div className="text-xs text-gray-500">
                From: {selectedFeedback.user_email || 'Anonymous'} | {formatDate(selectedFeedback.created_at)}
              </div>
            </div>
          )}
          <div className="border-t pt-4">
            <div className="text-sm font-semibold text-gray-700 mb-3">
              Your Response:
            </div>
            <Input
              label="Response Subject"
              value={editData.subject}
              onChange={(e) => setEditData({ ...editData, subject: e.target.value })}
              placeholder="Response subject..."
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Response Message <span className="text-red-500">*</span>
              </label>
              <textarea
                value={editData.message}
                onChange={(e) => setEditData({ ...editData, message: e.target.value })}
                className="w-full border rounded-md p-2 text-sm"
                rows={5}
                placeholder="Type your response to this user..."
              />
            </div>
            <div className="flex items-center space-x-2 p-3 bg-yellow-50 rounded">
              <input
                type="checkbox"
                id="broadcast-check"
                checked={editData.broadcast}
                onChange={(e) => setEditData({ ...editData, broadcast: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="broadcast-check" className="text-sm font-medium text-gray-700 cursor-pointer">
                Also broadcast this response as a system-wide alert to all users
              </label>
            </div>
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateFeedback}>
              <FiSend className="w-4 h-4 mr-2" />
              Send Response {editData.broadcast ? '& Broadcast' : ''}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Broadcast Modal */}
      <Modal
        isOpen={broadcastModalOpen}
        onClose={() => setBroadcastModalOpen(false)}
        title="Send Broadcast"
      >
        <div className="space-y-4">
          <Input
            label="Title"
            value={broadcastData.title}
            onChange={(e) => setBroadcastData({ ...broadcastData, title: e.target.value })}
            placeholder="Broadcast title..."
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message
            </label>
            <textarea
              value={broadcastData.message}
              onChange={(e) => setBroadcastData({ ...broadcastData, message: e.target.value })}
              className="w-full border rounded-md p-2 text-sm"
              rows={4}
              placeholder="Broadcast message..."
            />
          </div>
          <Select
            label="Priority"
            value={broadcastData.priority}
            onChange={(e) => setBroadcastData({ ...broadcastData, priority: e.target.value })}
            options={[
              { value: 'low', label: 'Low' },
              { value: 'normal', label: 'Normal' },
              { value: 'high', label: 'High' }
            ]}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Roles (leave empty for all users)
            </label>
            <div className="flex flex-wrap gap-2">
              {['public', 'government', 'analyst', 'developer'].map((role) => (
                <label key={role} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={broadcastData.target_roles.includes(role)}
                    onChange={(e) => {
                      const newRoles = e.target.checked
                        ? [...broadcastData.target_roles, role]
                        : broadcastData.target_roles.filter(r => r !== role)
                      setBroadcastData({ ...broadcastData, target_roles: newRoles })
                    }}
                    className="rounded"
                  />
                  <span className="text-sm capitalize">{role}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setBroadcastModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleBroadcast}>
              <FiSend className="w-4 h-4 mr-2" />
              Send Broadcast
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default DevFeedback
