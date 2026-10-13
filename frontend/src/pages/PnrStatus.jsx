import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/api'

export default function PnrStatus() {
  const [searchParams] = useSearchParams()
  const [pnr, setPnr] = useState(searchParams.get('pnr') || '')
  const [booking, setBooking] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [cancelling, setCancelling] = useState(false)

  useEffect(() => {
    if (searchParams.get('pnr')) {
      handleCheck()
    }
  }, [])

  const handleCheck = async (e) => {
    if (e) e.preventDefault()
    if (!pnr.trim()) return
    setLoading(true)
    setError('')
    setBooking(null)
    try {
      const data = await api.getBooking(pnr.trim())
      setBooking(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!booking) return
    if (!confirm('Are you sure you want to cancel this booking? Refund will be processed based on cancellation policy.')) return
    setCancelling(true)
    try {
      const result = await api.cancelBooking(booking.pnr)
      const updated = await api.getBooking(booking.pnr)
      setBooking(updated)
      alert(`Booking cancelled. Refund amount: ₹${result.refund_amount}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setCancelling(false)
    }
  }

  const formattedDate = booking
    ? new Date(booking.travel_date + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
    : ''

  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      {/* Search */}
      <div className="card" style={{ marginBottom: 32 }}>
        <div className="card-header">PNR Status Enquiry</div>
        <div className="card-body">
          <form onSubmit={handleCheck} style={{ display: 'flex', gap: 12 }}>
            <input
              type="text"
              className="form-control"
              placeholder="Enter 10-digit PNR Number"
              value={pnr}
              onChange={(e) => setPnr(e.target.value)}
              style={{ flex: 1 }}
              maxLength={15}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !pnr.trim()}>
              {loading ? 'Checking...' : 'Check Status'}
            </button>
          </form>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Fetching PNR status...</p>
        </div>
      )}

      {booking && (
        <div className="pnr-result">
          {/* Status Header */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-body" style={{ textAlign: 'center', padding: 32 }}>
              <div style={{ fontSize: 14, color: 'var(--irctc-text-light)', marginBottom: 4 }}>PNR Number</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--irctc-blue)', marginBottom: 12 }}>{booking.pnr}</div>
              <span className={`badge badge-${booking.status.toLowerCase()}`} style={{ fontSize: 14, padding: '6px 20px' }}>
                {booking.status}
              </span>
            </div>
          </div>

          {/* Journey */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">Journey Information</div>
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
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, textAlign: 'center' }}>
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
                <div>
                  <div style={{ fontSize: 12, color: 'var(--irctc-text-light)' }}>Fare</div>
                  <div style={{ fontWeight: 600 }}>&#8377;{booking.total_fare.toLocaleString()}</div>
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
                    <th>Age/Gender</th>
                    <th>Booking Status</th>
                    <th>Seat</th>
                  </tr>
                </thead>
                <tbody>
                  {booking.passengers.map((p, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td style={{ fontWeight: 500 }}>{p.name}</td>
                      <td>{p.age} / {p.gender === 'M' ? 'Male' : p.gender === 'F' ? 'Female' : 'Other'}</td>
                      <td><span className={`badge badge-${p.status === 'CNF' ? 'confirmed' : p.status === 'CAN' ? 'cancelled' : 'rac'}`}>{p.status}</span></td>
                      <td>{p.seat_number || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cancel */}
          {booking.status !== 'CANCELLED' && (
            <div style={{ textAlign: 'center' }}>
              <button className="btn btn-danger" onClick={handleCancel} disabled={cancelling}>
                {cancelling ? 'Cancelling...' : 'Cancel Booking'}
              </button>
              <p style={{ fontSize: 12, color: 'var(--irctc-text-light)', marginTop: 8 }}>
                Refund policy: 90% (48h+), 50% (12-48h), 25% (4-12h), 0% (less than 4h before departure)
              </p>
            </div>
          )}
        </div>
      )}

      {/* No result placeholder */}
      {!booking && !loading && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">&#128270;</div>
          <h3>Check Your PNR Status</h3>
          <p>Enter your 10-digit PNR number above to check your booking status, seat allocation, and journey details.</p>
        </div>
      )}
    </div>
  )
}
