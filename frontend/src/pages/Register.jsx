import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', phone: '', full_name: '', password: '', confirmPassword: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    try {
      const { confirmPassword, ...data } = form
      await register(data)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card" style={{ maxWidth: 520 }}>
        <h2>Create IRCTC Account</h2>
        <p className="subtitle">Register to book train tickets online</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Full Name *</label>
              <input type="text" className="form-control" placeholder="Your full name" value={form.full_name} onChange={update('full_name')} required />
            </div>
            <div className="form-group">
              <label>Username *</label>
              <input type="text" className="form-control" placeholder="Choose a username" value={form.username} onChange={update('username')} required minLength={3} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Email *</label>
              <input type="email" className="form-control" placeholder="Your email address" value={form.email} onChange={update('email')} required />
            </div>
            <div className="form-group">
              <label>Mobile Number</label>
              <input type="tel" className="form-control" placeholder="10-digit mobile" value={form.phone} onChange={update('phone')} maxLength={15} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Password *</label>
              <input type="password" className="form-control" placeholder="Min. 6 characters" value={form.password} onChange={update('password')} required minLength={6} />
            </div>
            <div className="form-group">
              <label>Confirm Password *</label>
              <input type="password" className="form-control" placeholder="Re-enter password" value={form.confirmPassword} onChange={update('confirmPassword')} required />
            </div>
          </div>

          <label className="search-option" style={{ marginBottom: 20 }}>
            <input type="checkbox" required /> I agree to the Terms of Service and Privacy Policy
          </label>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="auth-link">
          Already have an account? <Link to="/login">Login here</Link>
        </div>
      </div>
    </div>
  )
}
