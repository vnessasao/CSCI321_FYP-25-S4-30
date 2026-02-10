import { useState, useEffect, useContext } from 'react'
import { AuthContext } from '../../context/AuthContext'
import ApiService from '../../api/apiService'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Badge from '../../components/Badge'
import { toast, ToastContainer } from '../../components/Toast'
import { FiRefreshCw, FiUserPlus, FiUsers, FiShield } from 'react-icons/fi'

const GovManageUsers = () => {
  const { token } = useContext(AuthContext)
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [suspendModalOpen, setSuspendModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [suspendingUser, setSuspendingUser] = useState(null)
  const [suspendReason, setSuspendReason] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: '',
  })

  useEffect(() => {
    loadUsers()
    loadStats()
  }, [roleFilter, statusFilter])

  const loadUsers = async () => {
    if (!token) {
      setError('Authentication required')
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await ApiService.getUsers(token, {
        role: roleFilter || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined
      })

      if (response.success) {
        setUsers(response.users)
      } else {
        setError('Failed to load users')
      }
    } catch (err) {
      console.error('Error loading users:', err)
      setError(err.message || 'Failed to load users. Admin access required.')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    if (!token) return
    try {
      const response = await ApiService.getUserStats(token)
      if (response.success) {
        setStats(response.stats)
      }
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  const handleAdd = () => {
    setEditingUser(null)
    setFormData({ name: '', email: '', password: '', role: '' })
    setModalOpen(true)
  }

  const handleEdit = (user) => {
    setEditingUser(user)
    setFormData({
      name: user.name || '',
      email: user.email,
      password: '',
      role: user.role
    })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!formData.email || !formData.role) {
      toast.error('Email and role are required')
      return
    }

    if (!editingUser && !formData.password) {
      toast.error('Password is required for new users')
      return
    }

    try {
      if (editingUser) {
        const updateData = {
          name: formData.name,
          role: formData.role
        }
        await ApiService.updateUser(editingUser.id, updateData, token)
        toast.success('User updated successfully')
      } else {
        await ApiService.createUser({
          email: formData.email,
          password: formData.password,
          role: formData.role,
          name: formData.name
        }, token)
        toast.success('User created successfully')
      }
      setModalOpen(false)
      loadUsers()
      loadStats()
    } catch (err) {
      toast.error(err.message || 'Failed to save user')
    }
  }

  const handleSuspendClick = (user) => {
    setSuspendingUser(user)
    setSuspendReason('')
    setSuspendModalOpen(true)
  }

  const handleSuspend = async () => {
    if (!suspendingUser) return

    const isSuspending = !suspendingUser.is_suspended
    if (isSuspending && !suspendReason.trim()) {
      toast.error('Please provide a reason for suspension')
      return
    }

    try {
      await ApiService.suspendUser(
        suspendingUser.id,
        isSuspending,
        suspendReason,
        token
      )
      toast.success(isSuspending ? 'User suspended' : 'User unsuspended')
      setSuspendModalOpen(false)
      loadUsers()
      loadStats()
    } catch (err) {
      toast.error(err.message || 'Failed to update user status')
    }
  }

  const handleDeactivate = async (userId) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return

    try {
      await ApiService.deleteUser(userId, token)
      toast.success('User deactivated')
      loadUsers()
      loadStats()
    } catch (err) {
      toast.error(err.message || 'Failed to deactivate user')
    }
  }

  const columns = [
    { key: 'id', label: 'ID' },
    {
      key: 'name',
      label: 'Name',
      render: (value, row) => (
        <div className="flex items-center gap-2">
          {value || '-'}
          {row.is_super_admin && (
            <FiShield className="text-yellow-500" title="Super Admin" />
          )}
        </div>
      )
    },
    { key: 'email', label: 'Email' },
    {
      key: 'role',
      label: 'Role',
      render: (value) => (
        <Badge variant={
          value === 'developer' ? 'primary' :
          value === 'government' ? 'success' :
          value === 'analyst' ? 'warning' : 'default'
        }>
          {value}
        </Badge>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (_, row) => (
        <Badge variant={
          row.is_suspended ? 'danger' :
          row.is_active ? 'success' : 'default'
        }>
          {row.is_suspended ? 'Suspended' : row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="secondary" onClick={() => handleEdit(row)}>
            Edit
          </Button>
          {!row.is_super_admin && (
            <>
              <Button
                size="sm"
                variant={row.is_suspended ? 'primary' : 'warning'}
                onClick={() => handleSuspendClick(row)}
              >
                {row.is_suspended ? 'Unsuspend' : 'Suspend'}
              </Button>
              {row.is_active && (
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleDeactivate(row.id)}
                >
                  Deactivate
                </Button>
              )}
            </>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />

      {/* Header */}
      <Card>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Manage User Accounts</h2>
            <p className="text-gray-600">Add, edit, suspend and manage user accounts (GA-10)</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={loadUsers}>
              <FiRefreshCw className={loading ? 'animate-spin' : ''} />
              Refresh
            </Button>
            <Button onClick={handleAdd}>
              <FiUserPlus />
              Add User
            </Button>
          </div>
        </div>
      </Card>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <FiUsers className="text-blue-500 text-xl" />
              <div>
                <p className="text-sm text-gray-500">Total Users</p>
                <p className="text-xl font-bold">{stats.total_users}</p>
              </div>
            </div>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Active</p>
            <p className="text-xl font-bold text-green-600">{stats.total_active}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Suspended</p>
            <p className="text-xl font-bold text-red-600">{stats.total_suspended}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">By Role</p>
            <div className="text-xs text-gray-600">
              {stats.by_role && Object.entries(stats.by_role).map(([role, data]) => (
                <span key={role} className="mr-2">{role}: {data.total}</span>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap gap-4">
          <Select
            label="Filter by Role"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            options={[
              { value: '', label: 'All Roles' },
              { value: 'public', label: 'Public' },
              { value: 'government', label: 'Government' },
              { value: 'analyst', label: 'Analyst' },
              { value: 'developer', label: 'Developer' },
            ]}
            className="w-40"
          />
          <Select
            label="Filter by Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            options={[
              { value: 'all', label: 'All Status' },
              { value: 'active', label: 'Active' },
              { value: 'suspended', label: 'Suspended' },
            ]}
            className="w-40"
          />
        </div>
      </Card>

      {/* Users Table */}
      <Card>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-4">
            <div className="font-semibold mb-2">⚠️ {error}</div>
            <div className="text-sm">
              <p className="mb-2">To access user management, you need super admin privileges.</p>
              <p className="mb-2">Run this SQL command to grant super admin access to your government account:</p>
              <div className="bg-white border border-red-300 p-3 rounded font-mono text-xs overflow-x-auto">
                UPDATE users SET is_super_admin = TRUE WHERE email = 'government@gmail.com';
              </div>
              <p className="mt-2 text-xs italic">Replace 'government@gmail.com' with your actual email address.</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : !error && (
          <Table
            columns={columns}
            data={users}
            emptyMessage="No users found. You need admin privileges to view users."
          />
        )}
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingUser ? 'Edit User' : 'Add User'}
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter user's name"
          />
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="Enter email address"
            disabled={!!editingUser}
          />
          {!editingUser && (
            <Input
              label="Password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Enter password (min 6 characters)"
            />
          )}
          <Select
            label="Role"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            options={[
              { value: '', label: 'Select role' },
              { value: 'public', label: 'Public User' },
              { value: 'government', label: 'Government User' },
              { value: 'analyst', label: 'Traffic Analyst' },
              { value: 'developer', label: 'System Developer' },
            ]}
          />
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>
              {editingUser ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Suspend Modal */}
      <Modal
        isOpen={suspendModalOpen}
        onClose={() => setSuspendModalOpen(false)}
        title={suspendingUser?.is_suspended ? 'Unsuspend User' : 'Suspend User'}
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            {suspendingUser?.is_suspended
              ? `Are you sure you want to unsuspend ${suspendingUser?.email}?`
              : `Are you sure you want to suspend ${suspendingUser?.email}?`
            }
          </p>
          {!suspendingUser?.is_suspended && (
            <Input
              label="Reason for Suspension"
              value={suspendReason}
              onChange={(e) => setSuspendReason(e.target.value)}
              placeholder="Enter reason..."
              required
            />
          )}
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="secondary" onClick={() => setSuspendModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={suspendingUser?.is_suspended ? 'primary' : 'danger'}
              onClick={handleSuspend}
            >
              {suspendingUser?.is_suspended ? 'Unsuspend' : 'Suspend'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default GovManageUsers
