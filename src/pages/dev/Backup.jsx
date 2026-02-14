import { useState, useEffect } from 'react'
import Card from '../../components/Card'
import Table from '../../components/Table'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Select from '../../components/Select'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import { toast, ToastContainer } from '../../components/Toast'
import ApiService from '../../api/apiService'
import { FiDownload, FiTrash2, FiUpload, FiRefreshCw, FiDatabase } from 'react-icons/fi'

const DevBackup = () => {
  const [backups, setBackups] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [stats, setStats] = useState(null)
  const [tables, setTables] = useState([])
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [restoreModalOpen, setRestoreModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [selectedBackup, setSelectedBackup] = useState(null)
  const [backupToDelete, setBackupToDelete] = useState(null)
  const [hardDelete, setHardDelete] = useState(false)
  const [formData, setFormData] = useState({
    type: 'full',
    tables: [],
    notes: '',
    compress: true
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      const [backupsRes, statsRes, tablesRes] = await Promise.all([
        ApiService.getBackups(token),
        ApiService.getBackupStats(token),
        ApiService.getBackupTables(token)
      ])

      if (backupsRes.success) {
        setBackups(backupsRes.data.backups || [])
      }
      if (statsRes.success) {
        setStats(statsRes.data)
      }
      if (tablesRes.success) {
        setTables(tablesRes.data.tables || [])
      }
    } catch (err) {
      toast.error('Failed to load backups')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBackup = async () => {
    setCreating(true)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.createBackup(formData, token)

      if (res.success) {
        toast.success('Backup created successfully')
        setCreateModalOpen(false)
        loadData()
      } else {
        toast.error(res.error || 'Failed to create backup')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to create backup')
    } finally {
      setCreating(false)
    }
  }

  const handleDownload = async (backup) => {
    try {
      const token = localStorage.getItem('auth_token')
      const blob = await ApiService.downloadBackup(backup.id, token)

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = backup.filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success('Download started')
    } catch (err) {
      toast.error('Failed to download backup')
    }
  }

  const handleRestore = async () => {
    if (!selectedBackup) return

    setRestoring(true)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.restoreBackup(selectedBackup.id, token)

      if (res.success) {
        toast.success('Restoration successful: Database restored successfully')
        setRestoreModalOpen(false)
        setSelectedBackup(null)
        loadData() // Reload backup list
      } else {
        toast.error('Restoration failed: ' + (res.error || 'Failed to restore backup'))
      }
    } catch (err) {
      toast.error('Restoration failed: ' + (err.message || 'Failed to restore backup'))
    } finally {
      setRestoring(false)
    }
  }

  const openDeleteModal = (backup, isHardDelete = false) => {
    setBackupToDelete(backup)
    setHardDelete(isHardDelete)
    setDeleteModalOpen(true)
  }

  const handleDelete = async () => {
    if (!backupToDelete) return

    setDeleting(true)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await ApiService.deleteBackup(backupToDelete.id, hardDelete, token)

      if (res.success) {
        toast.success(res.message)
        loadData()
        setDeleteModalOpen(false)
        setBackupToDelete(null)
      } else {
        toast.error(res.error || 'Failed to delete backup')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to delete backup')
    } finally {
      setDeleting(false)
    }
  }

  const openRestoreModal = (backup) => {
    setSelectedBackup(backup)
    setRestoreModalOpen(true)
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }

  const formatSize = (bytes) => {
    if (!bytes) return '-'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const columns = [
    {
      key: 'filename',
      label: 'Filename',
      render: (value) => (
        <span className="font-mono text-sm">{value}</span>
      )
    },
    {
      key: 'backup_type',
      label: 'Type',
      render: (value) => (
        <Badge variant={value === 'full' ? 'primary' : 'info'}>
          {value}
        </Badge>
      )
    },
    {
      key: 'file_size',
      label: 'Size',
      render: (value) => formatSize(value)
    },
    {
      key: 'status',
      label: 'Status',
      render: (value, row) => (
        <Badge variant={value === 'completed' ? 'success' : 'warning'}>
          {value}
          {!row.file_exists && ' (missing)'}
        </Badge>
      )
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (value) => formatDate(value)
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex space-x-2">
          {row.file_exists && (
            <>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => handleDownload(row)}
                title="Download"
              >
                <FiDownload className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={() => openRestoreModal(row)}
                title="Restore"
              >
                <FiUpload className="w-4 h-4" />
              </Button>
            </>
          )}
          <Button
            size="sm"
            variant="danger"
            onClick={() => openDeleteModal(row, true)}
            title="Delete"
          >
            <FiTrash2 className="w-4 h-4" />
          </Button>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Backup & Restore</h2>
            <p className="text-gray-600">Manage database backups and restore points</p>
          </div>
          <div className="flex space-x-2">
            <Button onClick={loadData} variant="secondary">
              <FiRefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setCreateModalOpen(true)}>
              <FiDatabase className="w-4 h-4 mr-2" />
              Create Backup
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-500">Total Backups</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.full_backups}</div>
              <div className="text-sm text-gray-500">Full Backups</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.total_size_mb} MB</div>
              <div className="text-sm text-gray-500">Total Size</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-sm font-medium text-gray-600">
                {stats.last_backup ? formatDate(stats.last_backup) : 'Never'}
              </div>
              <div className="text-sm text-gray-500">Last Backup</div>
            </div>
          </Card>
        </div>
      )}

      {/* Backups Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <Table columns={columns} data={backups} emptyMessage="No backups found" />
        )}
      </Card>

      {/* Create Backup Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create New Backup"
      >
        <div className="space-y-4">
          <Select
            label="Backup Type"
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            options={[
              { value: 'full', label: 'Full Backup (All Tables)' },
              { value: 'partial', label: 'Partial Backup (Select Tables)' }
            ]}
          />

          {formData.type === 'partial' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Tables
              </label>
              <div className="max-h-48 overflow-y-auto border rounded p-2 space-y-1">
                {tables.map((table) => (
                  <label key={table} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.tables.includes(table)}
                      onChange={(e) => {
                        const newTables = e.target.checked
                          ? [...formData.tables, table]
                          : formData.tables.filter(t => t !== table)
                        setFormData({ ...formData, tables: newTables })
                      }}
                      className="rounded"
                    />
                    <span className="text-sm font-mono">{table}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (Optional)
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full border rounded-md p-2 text-sm"
              rows={2}
              placeholder="Backup notes..."
            />
          </div>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.compress}
              onChange={(e) => setFormData({ ...formData, compress: e.target.checked })}
              className="rounded"
            />
            <span className="text-sm">Compress backup (gzip)</span>
          </label>

          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateBackup} disabled={creating}>
              {creating ? 'Creating...' : 'Create Backup'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Restore Confirmation Modal */}
      <Modal
        isOpen={restoreModalOpen}
        onClose={() => setRestoreModalOpen(false)}
        title="Restore Database"
      >
        <div className="space-y-4">
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-yellow-800 font-semibold">Warning</p>
            <p className="text-yellow-700 text-sm mt-1">
              Restoring from this backup will overwrite current data. This action cannot be undone.
            </p>
          </div>

          {selectedBackup && (
            <div className="p-3 bg-gray-50 rounded">
              <div className="text-sm">
                <strong>Backup:</strong> {selectedBackup.filename}
              </div>
              <div className="text-sm text-gray-600">
                <strong>Created:</strong> {formatDate(selectedBackup.created_at)}
              </div>
              <div className="text-sm text-gray-600">
                <strong>Size:</strong> {formatSize(selectedBackup.file_size)}
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button 
              variant="secondary" 
              onClick={() => setRestoreModalOpen(false)}
              disabled={restoring}
            >
              Cancel
            </Button>
            <Button 
              variant="danger" 
              onClick={handleRestore}
              disabled={restoring}
            >
              {restoring ? 'Restoring...' : 'Restore Database'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Backup"
      >
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded">
            <p className="text-red-800 font-semibold">Warning</p>
            <p className="text-red-700 text-sm mt-1">
              {hardDelete
                ? 'This will permanently delete the backup file from disk. This action cannot be undone.'
                : 'This will mark the backup as deleted. You can recover it later if needed.'}
            </p>
          </div>

          {backupToDelete && (
            <div className="p-3 bg-gray-50 rounded">
              <div className="text-sm">
                <strong>Backup:</strong> {backupToDelete.filename}
              </div>
              <div className="text-sm text-gray-600">
                <strong>Size:</strong> {formatSize(backupToDelete.file_size)}
              </div>
              <div className="text-sm text-gray-600">
                <strong>Created:</strong> {formatDate(backupToDelete.created_at)}
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button 
              variant="secondary" 
              onClick={() => setDeleteModalOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button 
              variant="danger" 
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : (hardDelete ? 'Delete Permanently' : 'Delete')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default DevBackup
