import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/api'

const BERTH_OPTIONS = ['NO_PREF', 'LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER']

function emptyPassenger() {
  return { name: '', age: '', gender: 'M', berth_preference: 'NO_PREF' }
}

export default function BookingPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const trainNumber = searchParams.get('train_number') || ''
  const trainName = searchParams.get('train_name') || ''
  const source = searchParams.get('source') || ''
  const destination = searchParams.get('destination') || ''
  const date = searchParams.get('date') || ''
  const classCode = searchParams.get('class_code') || ''
  const fare = parseFloat(searchParams.get('fare') || '0')
  const departure = searchParams.get('departure') || ''
  const arrival = searchParams.get('arrival') || ''

  const [step, setStep] = useState(1)
  const [passengers, setPassengers] = useState([emptyPassenger()])
  const [paymentMethod, setPaymentMethod] = useState('upi')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!trainNumber || !source || !destination || !date || !classCode) {
    return (
      <div className="page-container">
        <div className="error-message">Invalid booking parameters. Please search for trains first.</div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>Go to Search</button>
      </div>
    )
  }

  const addPassenger = () => {
    if (passengers.length < 6) setPassengers([...passengers, emptyPassenger()])
  }

  const removePassenger = (idx) => {
    if (passengers.length > 1) setPassengers(passengers.filter((_, i) => i !== idx))
  }

  const updatePassenger = (idx, field, value) => {
    const updated = [...passengers]
    updated[idx] = { ...updated[idx], [field]: value }
    setPassengers(updated)
  }

  const calculateFare = (p) => {
    let f = fare
    const age = parseInt(p.age) || 0
    if (age > 0 && age < 12) f *= 0.5
    if (age >= 60) f *= 0.6
    return f
  }

  const totalFare = passengers.reduce((sum, p) => sum + calculateFare(p), 0)

  const isPassengersValid = passengers.every(p => p.name.trim() && p.age && parseInt(p.age) > 0 && parseInt(p.age) <= 120)

  const handleBook = async () => {
    setError('')
    setLoading(true)
    try {
      const booking = await api.createBooking({
        train_number: trainNumber,
        source,
        destination,
        travel_date: date,
        class_code: classCode,
        passengers: passengers.map(p => ({
          name: p.name,
          age: parseInt(p.age),
          gender: p.gender,
          berth_preference: p.berth_preference,
        })),
      })
      navigate(`/booking/confirmation/${booking.pnr}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formattedDate = new Date(date + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <div className="page-container">
      {/* Steps indicator */}
      <div className="steps">
        <div className={`step ${step >= 1 ? (step > 1 ? 'completed' : 'active') : ''}`}>
          <div className="step-number">{step > 1 ? '✓' : '1'}</div>
          <span>Passenger Details</span>
        </div>
        <div className={`step-line ${step > 1 ? 'completed' : ''}`}></div>
        <div className={`step ${step >= 2 ? (step > 2 ? 'completed' : 'active') : ''}`}>
          <div className="step-number">{step > 2 ? '✓' : '2'}</div>
          <span>Review & Pay</span>
        </div>
        <div className={`step-line ${step > 2 ? 'completed' : ''}`}></div>
        <div className={`step ${step >= 3 ? 'active' : ''}`}>
          <div className="step-number">3</div>
          <span>Confirmation</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>
        {/* Main Content */}
        <div>
          {/* Train Info */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <span>Train Details</span>
              <span className="badge badge-confirmed">{classCode}</span>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--irctc-blue)' }}>{trainName}</div>
                  <div style={{ fontSize: 13, color: 'var(--irctc-text-light)' }}>#{trainNumber}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 13, color: 'var(--irctc-text-light)' }}>{formattedDate}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 16 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{departure}</div>
                  <div style={{ fontSize: 13, color: 'var(--irctc-text-light)' }}>{source}</div>
                </div>
                <div style={{ color: '#aaa', fontSize: 20 }}>&#8594;</div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{arrival}</div>
                  <div style={{ fontSize: 13, color: 'var(--irctc-text-light)' }}>{destination}</div>
                </div>
              </div>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {/* Step 1: Passengers */}
          {step === 1 && (
            <div className="card">
              <div className="card-header">
                <span>Passenger Details</span>
                <button className="btn btn-outline btn-sm" onClick={addPassenger} disabled={passengers.length >= 6}>
                  + Add Passenger
                </button>
              </div>
              <div className="card-body">
                {!user && (
                  <div className="success-message" style={{ marginBottom: 16 }}>
                    You can book without logging in, but we recommend <a href="/login">logging in</a> to track your bookings.
                  </div>
                )}

                {passengers.map((p, idx) => (
                  <div key={idx} className="passenger-form">
                    <div className="passenger-form-header">
                      <h4>Passenger {idx + 1}</h4>
                      {passengers.length > 1 && (
                        <button className="passenger-remove" onClick={() => removePassenger(idx)}>Remove</button>
                      )}
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Full Name *</label>
                        <input type="text" className="form-control" placeholder="As on ID proof" value={p.name} onChange={(e) => updatePassenger(idx, 'name', e.target.value)} required />
                      </div>
                      <div className="form-group">
                        <label>Age *</label>
                        <input type="number" className="form-control" placeholder="Age" value={p.age} onChange={(e) => updatePassenger(idx, 'age', e.target.value)} min="1" max="120" required />
                      </div>
                      <div className="form-group">
                        <label>Gender *</label>
                        <select className="form-control" value={p.gender} onChange={(e) => updatePassenger(idx, 'gender', e.target.value)}>
                          <option value="M">Male</option>
                          <option value="F">Female</option>
                          <option value="O">Other</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Berth Preference</label>
                        <select className="form-control" value={p.berth_preference} onChange={(e) => updatePassenger(idx, 'berth_preference', e.target.value)}>
                          {BERTH_OPTIONS.map(b => <option key={b} value={b}>{b.replace(/_/g, ' ')}</option>)}
                        </select>
                      </div>
                    </div>
                    {parseInt(p.age) > 0 && parseInt(p.age) < 12 && (
                      <div style={{ fontSize: 12, color: 'var(--irctc-green)', marginTop: 4 }}>Child discount: 50% off</div>
                    )}
                    {parseInt(p.age) >= 60 && (
                      <div style={{ fontSize: 12, color: 'var(--irctc-green)', marginTop: 4 }}>Senior citizen discount: 40% off</div>
                    )}
                  </div>
                ))}

                <div style={{ textAlign: 'right', marginTop: 20 }}>
                  <button className="btn btn-primary" onClick={() => setStep(2)} disabled={!isPassengersValid}>
                    Continue to Review
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Review & Payment */}
          {step === 2 && (
            <div className="card">
              <div className="card-header">Payment Method</div>
              <div className="card-body">
                {[
                  { id: 'upi', icon: '₹', title: 'UPI / BHIM', desc: 'Pay using UPI apps' },
                  { id: 'card', icon: '💳', title: 'Credit / Debit Card', desc: 'Visa, Mastercard, RuPay' },
                  { id: 'nb', icon: '🏦', title: 'Net Banking', desc: 'All major banks' },
                  { id: 'wallet', icon: '📱', title: 'Mobile Wallet', desc: 'Paytm, PhonePe, Amazon Pay' },
                ].map(m => (
                  <div
                    key={m.id}
                    className={`payment-method ${paymentMethod === m.id ? 'selected' : ''}`}
                    onClick={() => setPaymentMethod(m.id)}
                  >
                    <div className="payment-method-icon">{m.icon}</div>
                    <div>
                      <h4>{m.title}</h4>
                      <p>{m.desc}</p>
                    </div>
                  </div>
                ))}

                <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
                  <button className="btn btn-outline" onClick={() => setStep(1)}>Back</button>
                  <button className="btn btn-success" onClick={handleBook} disabled={loading} style={{ flex: 1 }}>
                    {loading ? 'Processing Payment...' : `Pay ₹${totalFare.toLocaleString()} & Book`}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: Booking Summary */}
        <div className="booking-summary">
          <h3>Booking Summary</h3>
          <div className="summary-row">
            <span className="label">Train</span>
            <span className="value">{trainNumber}</span>
          </div>
          <div className="summary-row">
            <span className="label">Route</span>
            <span className="value">{source} &#8594; {destination}</span>
          </div>
          <div className="summary-row">
            <span className="label">Date</span>
            <span className="value">{formattedDate}</span>
          </div>
          <div className="summary-row">
            <span className="label">Class</span>
            <span className="value">{classCode}</span>
          </div>
          <div className="summary-row">
            <span className="label">Passengers</span>
            <span className="value">{passengers.length}</span>
          </div>

          {passengers.map((p, idx) => (
            p.name && (
              <div key={idx} className="summary-row" style={{ fontSize: 12 }}>
                <span className="label">{p.name} ({p.age || '?'}y, {p.gender})</span>
                <span className="value">&#8377;{calculateFare(p).toLocaleString()}</span>
              </div>
            )
          ))}

          <div className="summary-row total">
            <span className="label">Total Fare</span>
            <span className="value" style={{ color: 'var(--irctc-blue)' }}>&#8377;{totalFare.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
