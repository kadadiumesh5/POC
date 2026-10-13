import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/api'

export default function MyBookings() {
  const navigate = useNavigate()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    api.listBookings(100)
      .then(setBookings)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all'
    ? bookings
    : bookings.filter(b => b.status === filter.toUpperCase())

  return (
    <div className="page-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <h2 style={{ color: 'var(--irctc-blue)', fontSize: 22 }}>Booking History</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {['all', 'confirmed', 'cancelled'].map(f => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-secondary' : 'btn-outline'}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading bookings...</p>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {!loading && filtered.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">&#128196;</div>
          <h3>No Bookings Found</h3>
          <p>You haven't made any bookings yet. Start by searching for trains!</p>
          <Link to="/" className="btn btn-primary" style={{ marginTop: 16 }}>Book a Ticket</Link>
        </div>
      )}

      {filtered.map(booking => {
        const formattedDate = new Date(booking.travel_date + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
        return (
          <div
            key={booking.pnr}
            className="booking-list-item"
            onClick={() => navigate(`/booking/confirmation/${booking.pnr}`)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 48, height: 48, borderRadius: 8,
                background: booking.status === 'CANCELLED' ? '#ffebee' : 'var(--irctc-light-blue)',
                color: booking.status === 'CANCELLED' ? 'var(--irctc-red)' : 'var(--irctc-blue)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 20, fontWeight: 700, flexShrink: 0,
              }}>
                &#128646;
              </div>
              <div className="booking-item-train">
                <div className="booking-item-pnr">PNR: {booking.pnr}</div>
                <div className="booking-item-name">Train #{booking.train_number}</div>
                <div className="booking-item-route">
                  {booking.source_code} &#8594; {booking.destination_code}
                  <span style={{ margin: '0 8px', color: '#ddd' }}>|</span>
                  {booking.class_code}
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <div className="booking-item-date">{formattedDate}</div>
              <span className={`badge badge-${booking.status.toLowerCase()}`} style={{ marginTop: 4 }}>
                {booking.status}
              </span>
            </div>

            <div className="booking-item-fare">
              &#8377;{booking.total_fare.toLocaleString()}
            </div>
          </div>
        )
      })}

      {bookings.length > 0 && (
        <div style={{ textAlign: 'center', marginTop: 24, fontSize: 13, color: 'var(--irctc-text-light)' }}>
          Showing {filtered.length} of {bookings.length} bookings
        </div>
      )}
    </div>
  )
}
