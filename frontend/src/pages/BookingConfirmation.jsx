import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/api'

export default function BookingConfirmation() {
  const { pnr } = useParams()
  const [booking, setBooking] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getBooking(pnr)
      .then(setBooking)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [pnr])

  if (loading) return <div className="loading"><div className="loading-spinner"></div><p>Loading booking details...</p></div>
  if (error) return <div className="page-container"><div className="error-message">{error}</div></div>
  if (!booking) return null

  const isCancelled = booking.status === 'CANCELLED'
  const formattedDate = new Date(booking.travel_date + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <div className="confirmation-page">
      <div className="confirmation-header">
        <div className={`confirmation-icon ${isCancelled ? 'cancelled' : ''}`}>
          {isCancelled ? '✕' : '✓'}
        </div>
        <h2 style={{ color: isCancelled ? 'var(--irctc-red)' : 'var(--irctc-green)', marginBottom: 4 }}>
          {isCancelled ? 'Booking Cancelled' : 'Booking Confirmed!'}
        </h2>
        <p style={{ color: 'var(--irctc-text-light)' }}>
          PNR: <strong style={{ color: 'var(--irctc-blue)', fontSize: 18 }}>{booking.pnr}</strong>
        </p>
      </div>

      {/* Journey */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span>Journey Details</span>
          <span className={`badge badge-${booking.status.toLowerCase()}`}>{booking.status}</span>
        </div>
        <div className="card-body">
          <div className="pnr-journey">
            <div className="pnr-station">
              <div className="pnr-station-code">{booking.source_code}</div>
            </div>
            <div className="pnr-arrow">&#8594;</div>
            <div className="pnr-station">
              <div className="pnr-station-code">{booking.destination_code}</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: 12, color: 'var(--irctc-text-light)' }}>Train</div>
              <div style={{ fontWeight: 600 }}>{booking.train_number}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--irctc-text-light)' }}>Date</div>
              <div style={{ fontWeight: 600 }}>{formattedDate}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--irctc-text-light)' }}>Class</div>
              <div style={{ fontWeight: 600 }}>{booking.class_code}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Passengers */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">Passenger Details</div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Berth</th>
                <th>Seat</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {booking.passengers.map((p, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td style={{ fontWeight: 500 }}>{p.name}</td>
                  <td>{p.age}</td>
                  <td>{p.gender === 'M' ? 'Male' : p.gender === 'F' ? 'Female' : 'Other'}</td>
                  <td>{p.berth_preference}</td>
                  <td>{p.seat_number || '-'}</td>
                  <td><span className={`badge badge-${p.status === 'CNF' ? 'confirmed' : p.status === 'CAN' ? 'cancelled' : 'rac'}`}>{p.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Fare */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body">
          <div className="summary-row total" style={{ margin: 0, padding: 0, border: 'none' }}>
            <span className="label">Total Fare</span>
            <span className="value" style={{ color: 'var(--irctc-blue)', fontSize: 20 }}>&#8377;{booking.total_fare.toLocaleString()}</span>
          </div>
          <div className="summary-row" style={{ marginTop: 8 }}>
            <span className="label">Payment Status</span>
            <span className={`badge badge-${booking.payment_status.toLowerCase()}`}>{booking.payment_status}</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link to="/" className="btn btn-primary">Book Another Ticket</Link>
        <Link to="/my-bookings" className="btn btn-outline">View All Bookings</Link>
        {!isCancelled && (
          <Link to={`/pnr-status?pnr=${booking.pnr}`} className="btn btn-outline">Check PNR Status</Link>
        )}
      </div>
    </div>
  )
}
