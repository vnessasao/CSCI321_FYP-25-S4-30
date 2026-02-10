import { useState, useEffect } from 'react'
import LoadingSpinner from '../../components/LoadingSpinner'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Input from '../../components/Input'
import Badge from '../../components/Badge'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import { FiPlus, FiRefreshCw, FiEdit2, FiTrash2, FiShield } from 'react-icons/fi'

// Pre-defined permissions that match backend permission checks
const PREDEFINED_PERMISSIONS = [
  // Traffic & Analytics
  { name: 'view_traffic_map', display_name: 'View Traffic Map', category: 'Traffic & Analytics', description: 'Access live traffic congestion map' },
  { name: 'view_analytics', display_name: 'View Analytics', category: 'Traffic & Analytics', description: 'View traffic analytics and reports' },
  { name: 'upload_traffic_data', display_name: 'Upload Traffic Data', category: 'Traffic & Analytics', description: 'Upload GPS and traffic data files' },
  { name: 'download_traffic_data', display_name: 'Download Traffic Data', category: 'Traffic & Analytics', description: 'Download traffic datasets' },
  
  // Algorithms
  { name: 'view_algorithms', display_name: 'View Algorithms', category: 'Algorithms', description: 'View algorithm modules and status' },
  { name: 'manage_algorithms', display_name: 'Manage Algorithms', category: 'Algorithms', description: 'Edit algorithm settings and parameters' },
  { name: 'activate_algorithm', display_name: 'Activate Algorithm', category: 'Algorithms', description: 'Activate algorithm modules' },
  { name: 'suspend_algorithm', display_name: 'Suspend Algorithm', category: 'Algorithms', description: 'Suspend algorithm modules' },
  
  // Bottlenecks
  { name: 'view_bottlenecks', display_name: 'View Bottlenecks', category: 'Bottlenecks', description: 'View bottleneck analysis results' },
  { name: 'analyze_bottlenecks', display_name: 'Analyze Bottlenecks', category: 'Bottlenecks', description: 'Run bottleneck analysis' },
  { name: 'schedule_analysis', display_name: 'Schedule Analysis', category: 'Bottlenecks', description: 'Schedule automated analysis runs' },
  
  // Predictions
  { name: 'view_predictions', display_name: 'View Predictions', category: 'Predictions', description: 'View traffic jam predictions' },
  { name: 'create_predictions', display_name: 'Create Predictions', category: 'Predictions', description: 'Generate traffic predictions' },
  
  // Incidents
  { name: 'view_incidents', display_name: 'View Incidents', category: 'Incidents', description: 'View reported incidents' },
  { name: 'report_incident', display_name: 'Report Incident', category: 'Incidents', description: 'Report road incidents' },
  { name: 'manage_incidents', display_name: 'Manage Incidents', category: 'Incidents', description: 'Edit and delete incidents' },
  
  // Users
  { name: 'view_users', display_name: 'View Users', category: 'User Management', description: 'View user accounts' },
  { name: 'create_user', display_name: 'Create User', category: 'User Management', description: 'Create new user accounts' },
  { name: 'edit_user', display_name: 'Edit User', category: 'User Management', description: 'Edit user account details' },
  { name: 'delete_user', display_name: 'Delete User', category: 'User Management', description: 'Delete user accounts' },
  { name: 'suspend_user', display_name: 'Suspend User', category: 'User Management', description: 'Suspend user accounts' },
  
  // Backups
  { name: 'view_backups', display_name: 'View Backups', category: 'System', description: 'View backup list and details' },
  { name: 'create_backup', display_name: 'Create Backup', category: 'System', description: 'Create database backups' },
  { name: 'restore_backup', display_name: 'Restore Backup', category: 'System', description: 'Restore database from backup' },
  { name: 'delete_backup', display_name: 'Delete Backup', category: 'System', description: 'Delete backup files' },
  { name: 'download_backup', display_name: 'Download Backup', category: 'System', description: 'Download backup files' },
  
  // System
  { name: 'view_logs', display_name: 'View System Logs', category: 'System', description: 'View system logs and audit trails' },
  { name: 'view_performance', display_name: 'View Performance', category: 'System', description: 'View system performance metrics' },
  { name: 'manage_permissions', display_name: 'Manage Permissions', category: 'System', description: 'Create and edit permissions' },
  { name: 'manage_roles', display_name: 'Manage Roles', category: 'System', description: 'Assign permissions to roles' },
  
  // Feedback
  { name: 'submit_feedback', display_name: 'Submit Feedback', category: 'Feedback', description: 'Submit feedback and suggestions' },
  { name: 'view_own_feedback', display_name: 'View Own Feedback', category: 'Feedback', description: 'View own submitted feedback' },
  { name: 'view_all_feedback', display_name: 'View All Feedback', category: 'Feedback', description: 'View all user feedback' },
  { name: 'manage_feedback', display_name: 'Manage Feedback', category: 'Feedback', description: 'Respond to and manage feedback' },
  
  // Routes
  { name: 'save_route', display_name: 'Save Route', category: 'Routes', description: 'Save favorite routes' },
  { name: 'view_saved_routes', display_name: 'View Saved Routes', category: 'Routes', description: 'View saved route bookmarks' },
]

const DevAccessRoles = () => {
  const [roles, setRoles] = useState([])
  const [permissions, setPermissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [permissionModalOpen, setPermissionModalOpen] = useState(false)
  const [editingRole, setEditingRole] = useState(null)
  const [editingPermission, setEditingPermission] = useState(null)
  const [activeTab, setActiveTab] = useState('roles')
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: []
  })
  const [permissionFormData, setPermissionFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: ''
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      const [rolesRes, permissionsRes] = await Promise.all([
        ApiService.getRolesWithPermissions(token),
        ApiService.getPermissions(token)
      ])

      if (rolesRes.success) {
        // Convert roles object to array format for display
        const rolesData = rolesRes.data.roles || {}
        const rolesArray = Object.entries(rolesData).map(([name, permissions]) => ({
          name,
          description: `${name.charAt(0).toUpperCase() + name.slice(1)} role`,
          permissions: permissions || [],
          user_count: 0 // TODO: Get actual user count
        }))
        setRoles(rolesArray)
      }
      if (permissionsRes.success) {
        setPermissions(permissionsRes.data.permissions || [])
      }
    } catch (err) {
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRole = () => {
    setEditingRole(null)
    setFormData({ name: '', description: '', permissions: [] })
    setModalOpen(true)
  }

  const handleEditRole = (role) => {
    setEditingRole(role)
    setFormData({
      name: role.name,
      description: role.description || '',
      permissions: role.permissions || []
    })
    setModalOpen(true)
  }

  const handleSaveRole = async () => {
    if (!formData.name || !formData.description) {
      toast.error('Please fill in all required fields')
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      let res

      if (editingRole) {
        // Update role permissions
        res = await ApiService.updateRolePermissions(
          editingRole.name,
          formData.permissions.map(p => p.id || p),
          token
        )
      } else {
        // Create new role (using permission API to add role)
        // Note: In a real system, you'd have a separate endpoint for creating roles
        toast.info('Role creation through API requires admin setup')
        setModalOpen(false)
        return
      }

      if (res.success) {
        toast.success(editingRole ? 'Role updated successfully' : 'Role created successfully')
        setModalOpen(false)
        loadData()
      } else {
        toast.error(res.error || 'Failed to save role')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to save role')
    }
  }

  const handleCreatePermission = () => {
    setEditingPermission(null)
    const firstPerm = PREDEFINED_PERMISSIONS[0]
    setPermissionFormData({ 
      name: firstPerm.name, 
      display_name: firstPerm.display_name, 
      description: firstPerm.description, 
      category: firstPerm.category 
    })
    setPermissionModalOpen(true)
  }

  const handleEditPermission = (permission) => {
    setEditingPermission(permission)
    setPermissionFormData({
      name: permission.name,
      display_name: permission.display_name || '',
      description: permission.description || '',
      category: permission.category || ''
    })
    setPermissionModalOpen(true)
  }

  const handlePermissionSelect = (permName) => {
    const selected = PREDEFINED_PERMISSIONS.find(p => p.name === permName)
    if (selected) {
      setPermissionFormData({
        name: selected.name,
        display_name: selected.display_name,
        description: selected.description,
        category: selected.category
      })
    }
  }

  const handleSavePermission = async () => {
    if (!permissionFormData.name) {
      toast.error('Please enter a permission name')
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      let res

      if (editingPermission) {
        res = await ApiService.updatePermission(editingPermission.id, permissionFormData, token)
      } else {
        res = await ApiService.createPermission(permissionFormData, token)
      }

      if (res.success) {
        toast.success(editingPermission ? 'Permission updated' : 'Permission created')
        setPermissionModalOpen(false)
        loadData()
      } else {
        toast.error(res.error || 'Failed to save permission')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to save permission')
    }
  }

  const handleDeletePermission = async (permissionId) => {
    if (!confirm('Are you sure you want to delete this permission?')) return

    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.deletePermission(permissionId, token)

      if (res.success) {
        toast.success('Permission deleted')
        loadData()
      } else {
        toast.error(res.error || 'Failed to delete permission')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to delete permission')
    }
  }

  const togglePermissionInRole = (permission) => {
    const permId = permission.id
    const hasPermission = formData.permissions.some(p => (p.id || p) === permId)

    if (hasPermission) {
      setFormData({
        ...formData,
        permissions: formData.permissions.filter(p => (p.id || p) !== permId)
      })
    } else {
      setFormData({
        ...formData,
        permissions: [...formData.permissions, permission]
      })
    }
  }

  const roleColumns = [
    {
      key: 'name',
      label: 'Role Name',
      render: (value) => (
        <div className="flex items-center space-x-2">
          <FiShield className="w-4 h-4 text-blue-500" />
          <span className="font-medium capitalize">{value}</span>
        </div>
      )
    },
    {
      key: 'description',
      label: 'Description',
      render: (value) => <span className="text-gray-600">{value || '-'}</span>
    },
    {
      key: 'permissions',
      label: 'Permissions',
      render: (value) => (
        <div className="flex flex-wrap gap-1 max-w-md">
          {value && value.length > 0 ? (
            value.slice(0, 5).map((perm, idx) => (
              <Badge key={idx} variant="info">
                {typeof perm === 'string' ? perm : perm.name}
              </Badge>
            ))
          ) : (
            <span className="text-gray-400">No permissions</span>
          )}
          {value && value.length > 5 && (
            <Badge variant="default">+{value.length - 5} more</Badge>
          )}
        </div>
      )
    },
    {
      key: 'user_count',
      label: 'Users',
      render: (value) => (
        <Badge variant="default">{value || 0}</Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="secondary" onClick={() => handleEditRole(row)}>
            <FiEdit2 className="w-4 h-4" />
          </Button>
        </div>
      )
    }
  ]

  const permissionColumns = [
    {
      key: 'name',
      label: 'Permission',
      render: (value) => <span className="font-mono text-sm">{value}</span>
    },
    {
      key: 'description',
      label: 'Description',
      render: (value) => <span className="text-gray-600">{value || '-'}</span>
    },
    {
      key: 'category',
      label: 'Category',
      render: (value) => value ? <Badge variant="info">{value}</Badge> : '-'
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="secondary" onClick={() => handleEditPermission(row)}>
            <FiEdit2 className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="danger" onClick={() => handleDeletePermission(row.id)}>
            <FiTrash2 className="w-4 h-4" />
          </Button>
        </div>
      )
    }
  ]

  // Group permissions by category for the role edit modal
  const groupedPermissions = permissions.reduce((acc, perm) => {
    const category = perm.category || 'General'
    if (!acc[category]) acc[category] = []
    acc[category].push(perm)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Roles & Permissions</h2>
            <p className="text-gray-600">Manage user roles and system permissions</p>
          </div>
          <div className="flex space-x-2">
            <Button onClick={loadData} variant="secondary">
              <FiRefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            {activeTab === 'permissions' && (
              <Button onClick={handleCreatePermission}>
                <FiPlus className="w-4 h-4 mr-2" />
                Add Permission
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{roles.length}</div>
            <div className="text-sm text-gray-500">Total Roles</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{permissions.length}</div>
            <div className="text-sm text-gray-500">Total Permissions</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {Object.keys(groupedPermissions).length}
            </div>
            <div className="text-sm text-gray-500">Permission Categories</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {roles.reduce((sum, r) => sum + (r.user_count || 0), 0)}
            </div>
            <div className="text-sm text-gray-500">Total Users</div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Card>
        <div className="flex space-x-4 border-b">
          <button
            className={`pb-2 px-1 ${activeTab === 'roles' ? 'border-b-2 border-blue-500 text-blue-600 font-medium' : 'text-gray-500'}`}
            onClick={() => setActiveTab('roles')}
          >
            Roles
          </button>
          <button
            className={`pb-2 px-1 ${activeTab === 'permissions' ? 'border-b-2 border-blue-500 text-blue-600 font-medium' : 'text-gray-500'}`}
            onClick={() => setActiveTab('permissions')}
          >
            Permissions
          </button>
        </div>
      </Card>

      {/* Content Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <Table
            columns={activeTab === 'roles' ? roleColumns : permissionColumns}
            data={activeTab === 'roles' ? roles : permissions}
            emptyMessage={activeTab === 'roles' ? 'No roles found' : 'No permissions found'}
          />
        )}
      </Card>

      {/* Role Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingRole ? `Edit Role: ${editingRole.name}` : 'Create Role'}
      >
        <div className="space-y-4">
          <Input
            label="Role Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            disabled={!!editingRole}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full border rounded-md p-2 text-sm"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Permissions
            </label>
            <div className="max-h-64 overflow-y-auto border rounded p-3 space-y-4">
              {Object.entries(groupedPermissions).map(([category, perms]) => (
                <div key={category}>
                  <div className="text-sm font-semibold text-gray-600 mb-2">{category}</div>
                  <div className="space-y-1">
                    {perms.map((perm) => (
                      <label key={perm.id} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.permissions.some(p => (p.id || p) === perm.id)}
                          onChange={() => togglePermissionInRole(perm)}
                          className="rounded"
                        />
                        <span className="text-sm font-mono">{perm.name}</span>
                        {perm.description && (
                          <span className="text-xs text-gray-400">- {perm.description}</span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveRole}>Save</Button>
          </div>
        </div>
      </Modal>

      {/* Permission Edit Modal */}
      <Modal
        isOpen={permissionModalOpen}
        onClose={() => setPermissionModalOpen(false)}
        title={editingPermission ? 'Edit Permission' : 'Create Permission'}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Permission *
            </label>
            <select
              value={permissionFormData.name}
              onChange={(e) => handlePermissionSelect(e.target.value)}
              disabled={!!editingPermission}
              className="w-full border border-gray-300 rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PREDEFINED_PERMISSIONS.map(perm => (
                <option key={perm.name} value={perm.name}>
                  {perm.display_name}
                </option>
              ))}
            </select>
            {editingPermission && (
              <p className="text-xs text-gray-500 mt-1">Permission name cannot be changed after creation</p>
            )}
          </div>
          
          <Input
            label="Display Name"
            value={permissionFormData.display_name}
            onChange={(e) => setPermissionFormData({ ...permissionFormData, display_name: e.target.value })}
            disabled={true}
            placeholder="Auto-filled from selection"
          />
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={permissionFormData.description}
              onChange={(e) => setPermissionFormData({ ...permissionFormData, description: e.target.value })}
              className="w-full border rounded-md p-2 text-sm"
              rows={2}
              placeholder="What this permission allows..."
            />
          </div>
          
          <Input
            label="Category"
            value={permissionFormData.category}
            onChange={(e) => setPermissionFormData({ ...permissionFormData, category: e.target.value })}
            disabled={true}
            placeholder="Auto-filled from selection"
          />
          
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setPermissionModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSavePermission}>Save</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default DevAccessRoles
