import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api/api'

const DAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

function formatDuration(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h ${m}m`
}

function TrainCard({ train, date, onBook }) {
  const [coaches, setCoaches] = useState([])
  const [selectedClass, setSelectedClass] = useState(null)
  const [availability, setAvailability] = useState(null)

  useEffect(() => {
    const classesToCheck = ['SL', '3A', '2A', '1A', 'CC', '2S', 'EC']
    const found = []
    Promise.allSettled(
      classesToCheck.map(cls =>
        api.checkAvailability(train.number, cls, date)
          .then(a => found.push(a))
      )
    ).then(() => {
      setCoaches(found)
      if (found.length > 0) {
        setSelectedClass(found[0].class_code)
        setAvailability(found[0])
      }
    })
  }, [train.number, date])

  const handleClassSelect = (cls) => {
    setSelectedClass(cls.class_code)
    setAvailability(cls)
  }

  const statusClass = availability
    ? availability.status === 'AVAILABLE' ? 'available'
    : availability.status === 'RAC' ? 'rac' : 'wl'
    : ''

  return (
    <div className="train-card">
      <div className="train-card-header">
        <div className="train-number-name">
          <span className="train-number">({train.number})</span>
          <span className="train-name">{train.name}</span>
        </div>
        <div className="train-runs-on">
          {DAY_LABELS.map((d, i) => (
            <span key={i} className={`train-day ${train.runs_on[i] !== '-' ? '' : 'inactive'}`}>{d}</span>
          ))}
        </div>
      </div>

      <div className="train-card-journey">
        <div className="train-station">
          <div className="train-station-time">{train.departure_time}</div>
          <div className="train-station-code">{train.source_code}</div>
        </div>
        <div className="train-duration">
          <div className="train-duration-line"></div>
          <div className="train-duration-text">{formatDuration(train.duration_minutes)}</div>
        </div>
        <div className="train-station">
          <div className="train-station-time">{train.arrival_time}</div>
          <div className="train-station-code">{train.destination_code}</div>
        </div>
      </div>

      {coaches.length > 0 && (
        <>
          <div className="train-card-classes">
            {coaches.map(c => (
              <button
                key={c.class_code}
                className={`class-chip ${selectedClass === c.class_code ? 'selected' : ''}`}
                onClick={() => handleClassSelect(c)}
              >
                <span className="class-chip-code">{c.class_code}</span>
                <span className="class-chip-fare">&#8377; {c.fare.toLocaleString()}</span>
              </button>
            ))}
          </div>

          {availability && (
            <div className="train-card-availability">
              <div>
                <span className={`availability-status ${statusClass}`}>
                  {availability.status === 'AVAILABLE'
                    ? `Available ${availability.available}`
                    : availability.status}
                </span>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onBook(train, selectedClass, availability)}
              >
                Book Now
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function TrainList() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const source = searchParams.get('source') || ''
  const destination = searchParams.get('destination') || ''
  const date = searchParams.get('date') || ''

  const [trains, setTrains] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!source || !destination || !date) {
      navigate('/')
      return
    }
    setLoading(true)
    setError('')
    api.searchTrains(source, destination, date)
      .then(setTrains)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [source, destination, date, navigate])

  const handleBook = (train, classCode, availability) => {
    const params = new URLSearchParams({
      train_number: train.number,
      train_name: train.name,
      source: train.source_code,
      destination: train.destination_code,
      date,
      class_code: classCode,
      fare: availability.fare,
      departure: train.departure_time,
      arrival: train.arrival_time,
    })
    navigate(`/booking?${params}`)
  }

  const formattedDate = date ? new Date(date + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }) : ''

  return (
    <div className="page-container">
      {/* Search summary bar */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div>
              <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--irctc-blue)' }}>{source}</span>
              <span style={{ margin: '0 12px', color: '#aaa' }}>&#8594;</span>
              <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--irctc-blue)' }}>{destination}</span>
            </div>
            <span className="badge badge-confirmed">{formattedDate}</span>
          </div>
          <button className="btn btn-outline btn-sm" onClick={() => navigate('/')}>Modify Search</button>
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Searching trains...</p>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {!loading && !error && trains.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">&#128646;</div>
          <h3>No trains found</h3>
          <p>No trains available between {source} and {destination} on {formattedDate}</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/')}>Search Again</button>
        </div>
      )}

      {!loading && trains.length > 0 && (
        <>
          <p style={{ marginBottom: 16, color: 'var(--irctc-text-light)', fontSize: 14 }}>
            {trains.length} train{trains.length > 1 ? 's' : ''} found
          </p>
          {trains.map(train => (
            <TrainCard key={train.number} train={train} date={date} onBook={handleBook} />
          ))}
        </>
      )}
    </div>
  )
}
