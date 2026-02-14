import { useState } from 'react'
import ApiService from '../../api/apiService'
import Card from '../../components/Card'
import Select from '../../components/Select'
import Button from '../../components/Button'
import { toast, ToastContainer } from '../../components/Toast'

const PublicFeedback = () => {
  const [category, setCategory] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [rating, setRating] = useState(null)
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!category || !message.trim()) {
      toast.error('Please fill in category and message')
      return
    }

    setSubmitting(true)
    try {
      const token = localStorage.getItem('auth_token')
      const feedbackData = {
        category,
        subject,
        message,
        rating: rating ? parseInt(rating) : null
      }
      
      const res = await ApiService.submitFeedback(feedbackData, token)
      
      if (res.success) {
        setSubmitted(true)
        setCategory('')
        setSubject('')
        setMessage('')
        setRating(null)
        toast.success('Thank you for your feedback!')
      } else {
        toast.error(res.error || 'Failed to submit feedback')
      }
    } catch (error) {
      toast.error('Failed to submit feedback: ' + (error.message || 'Network error'))
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <Card>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h2>
          <p className="text-gray-600">
            Your feedback has been received. We appreciate your input.
          </p>
          <Button
            onClick={() => setSubmitted(false)}
            className="mt-6"
            variant="secondary"
          >
            Submit Another Feedback
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <ToastContainer />
      <Card>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Submit Feedback</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Category *"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={[
              { value: '', label: 'Select category' },
              { value: 'bug_report', label: 'Bug Report' },
              { value: 'feature_request', label: 'Feature Request' },
              { value: 'usability', label: 'Usability Issue' },
              { value: 'performance', label: 'Performance Issue' },
              { value: 'data_quality', label: 'Data Quality' },
              { value: 'general', label: 'General Feedback' },
              { value: 'other', label: 'Other' },
            ]}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject (Optional)
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="input-field"
              placeholder="Brief subject of your feedback"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message *
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="input-field"
              rows={5}
              placeholder="Please provide your detailed feedback..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rating (Optional)
            </label>
            <div className="flex space-x-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className={`text-2xl ${
                    rating && rating >= star ? 'text-yellow-400' : 'text-gray-300'
                  } hover:text-yellow-400 transition-colors`}
                  title={`${star} star${star > 1 ? 's' : ''}`}
                >
                  ★
                </button>
              ))}
              {rating && (
                <button
                  type="button"
                  onClick={() => setRating(null)}
                  className="text-sm text-gray-500 ml-2 hover:text-gray-700"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <Button type="submit" disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit Feedback'}
          </Button>
        </form>
      </Card>
    </div>
  )
}

export default PublicFeedback
