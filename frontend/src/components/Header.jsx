import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <>
      <div className="alert-banner">
        Indian Railways -- Book your tickets with ease. Tatkal booking available from 10:00 AM (AC) & 11:00 AM (Non-AC)
      </div>
      <header className="header">
        <Link to="/" className="header-logo">
          <div className="header-logo-icon">IR</div>
          <div>
            IRCTC
            <span className="header-subtitle">Indian Railway Catering & Tourism Corp.</span>
          </div>
        </Link>

        <nav className="header-nav">
          <Link to="/">Home</Link>
          <Link to="/pnr-status">PNR Status</Link>
          <Link to="/my-bookings">My Bookings</Link>

          {user ? (
            <div className="header-user">
              <div className="header-user-avatar">{user.full_name.charAt(0).toUpperCase()}</div>
              <span>{user.full_name.split(' ')[0]}</span>
              <button onClick={handleLogout}>Logout</button>
            </div>
          ) : (
            <Link to="/login" className="nav-login">Login / Register</Link>
          )}
        </nav>
      </header>
    </>
  )
}
