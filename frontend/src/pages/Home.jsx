import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api/api'

const CLASS_OPTIONS = [
  { value: '', label: 'All Classes' },
  { value: 'SL', label: 'Sleeper (SL)' },
  { value: '3A', label: 'AC 3 Tier (3A)' },
  { value: '2A', label: 'AC 2 Tier (2A)' },
  { value: '1A', label: 'AC First Class (1A)' },
  { value: 'CC', label: 'Chair Car (CC)' },
  { value: '2S', label: 'Second Sitting (2S)' },
]

const QUOTA_OPTIONS = [
  { value: 'GN', label: 'General' },
  { value: 'TQ', label: 'Tatkal' },
  { value: 'PT', label: 'Premium Tatkal' },
  { value: 'LD', label: 'Ladies' },
]

export default function Home() {
  const navigate = useNavigate()
  const [stations, setStations] = useState([])
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [date, setDate] = useState(getDefaultDate())
  const [classFilter, setClassFilter] = useState('')
  const [quota, setQuota] = useState('GN')
  const [sourceQuery, setSourceQuery] = useState('')
  const [destQuery, setDestQuery] = useState('')
  const [showSourceDropdown, setShowSourceDropdown] = useState(false)
  const [showDestDropdown, setShowDestDropdown] = useState(false)

  useEffect(() => {
    api.getStations().then(setStations).catch(() => {})
  }, [])

  function getDefaultDate() {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  }

  const filteredStations = (query) => {
    if (!query) return stations.slice(0, 10)
    const q = query.toLowerCase()
    return stations.filter(s =>
      s.code.toLowerCase().includes(q) ||
      s.name.toLowerCase().includes(q) ||
      s.city.toLowerCase().includes(q)
    ).slice(0, 8)
  }

  const handleSwap = () => {
    setSource(destination)
    setDestination(source)
    setSourceQuery(destQuery)
    setDestQuery(sourceQuery)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (!source || !destination || !date) return
    const params = new URLSearchParams({ source, destination, date })
    if (classFilter) params.set('class', classFilter)
    if (quota) params.set('quota', quota)
    navigate(`/trains?${params}`)
  }

  const selectStation = (station, type) => {
    if (type === 'source') {
      setSource(station.code)
      setSourceQuery(`${station.code} - ${station.name}`)
      setShowSourceDropdown(false)
    } else {
      setDestination(station.code)
      setDestQuery(`${station.code} - ${station.name}`)
      setShowDestDropdown(false)
    }
  }

  return (
    <div>
      {/* Hero with Search */}
      <section className="hero">
        <div className="hero-content">
          <h1>Book Train Tickets</h1>
          <p>Search and book Indian Railway tickets online with ease</p>

          <div className="search-card">
            <div className="search-tabs">
              <button className="search-tab active">BOOK TICKET</button>
              <button className="search-tab" onClick={() => navigate('/pnr-status')}>PNR STATUS</button>
            </div>

            <form onSubmit={handleSearch}>
              <div className="search-row">
                {/* From Station */}
                <div className="search-field">
                  <label>From</label>
                  <div className="autocomplete-wrapper">
                    <input
                      type="text"
                      placeholder="Station name or code"
                      value={sourceQuery}
                      onChange={(e) => { setSourceQuery(e.target.value); setShowSourceDropdown(true); setSource('') }}
                      onFocus={() => setShowSourceDropdown(true)}
                      onBlur={() => setTimeout(() => setShowSourceDropdown(false), 200)}
                    />
                    {showSourceDropdown && (
                      <div className="autocomplete-dropdown">
                        {filteredStations(sourceQuery).map(s => (
                          <div key={s.code} className="autocomplete-item" onMouseDown={() => selectStation(s, 'source')}>
                            <span className="code">{s.code}</span>
                            <span className="name">{s.name}, {s.city}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Swap */}
                <button type="button" className="swap-btn" onClick={handleSwap} title="Swap stations">
                  &#8646;
                </button>

                {/* To Station */}
                <div className="search-field">
                  <label>To</label>
                  <div className="autocomplete-wrapper">
                    <input
                      type="text"
                      placeholder="Station name or code"
                      value={destQuery}
                      onChange={(e) => { setDestQuery(e.target.value); setShowDestDropdown(true); setDestination('') }}
                      onFocus={() => setShowDestDropdown(true)}
                      onBlur={() => setTimeout(() => setShowDestDropdown(false), 200)}
                    />
                    {showDestDropdown && (
                      <div className="autocomplete-dropdown">
                        {filteredStations(destQuery).map(s => (
                          <div key={s.code} className="autocomplete-item" onMouseDown={() => selectStation(s, 'dest')}>
                            <span className="code">{s.code}</span>
                            <span className="name">{s.name}, {s.city}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Date */}
                <div className="search-field">
                  <label>Travel Date</label>
                  <input type="date" value={date} onChange={(e) => setDate(e.target.value)} min={new Date().toISOString().split('T')[0]} />
                </div>

                {/* Class */}
                <div className="search-field">
                  <label>Class</label>
                  <select value={classFilter} onChange={(e) => setClassFilter(e.target.value)}>
                    {CLASS_OPTIONS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
              </div>

              {/* Quota Options */}
              <div className="search-options">
                {QUOTA_OPTIONS.map(q => (
                  <label key={q.value} className="search-option">
                    <input type="radio" name="quota" value={q.value} checked={quota === q.value} onChange={(e) => setQuota(e.target.value)} />
                    {q.label}
                  </label>
                ))}
                <label className="search-option">
                  <input type="checkbox" /> Person with Disability
                </label>
                <label className="search-option">
                  <input type="checkbox" /> Flexible with Date
                </label>
              </div>

              <div className="search-submit">
                <button type="submit" className="btn btn-primary btn-lg" disabled={!source || !destination}>
                  Search Trains
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Quick Services */}
      <div className="quick-services">
        <Link to="/pnr-status" className="service-card">
          <div className="service-icon" style={{ background: '#e3f2fd', color: '#1565c0' }}>&#128269;</div>
          <h4>PNR Status</h4>
          <p>Check your booking status</p>
        </Link>
        <Link to="/my-bookings" className="service-card">
          <div className="service-icon" style={{ background: '#e8f5e9', color: '#2e7d32' }}>&#128196;</div>
          <h4>My Bookings</h4>
          <p>View booking history</p>
        </Link>
        <div className="service-card">
          <div className="service-icon" style={{ background: '#fff3e0', color: '#e65100' }}>&#128652;</div>
          <h4>Train Schedule</h4>
          <p>Check train timings</p>
        </div>
        <div className="service-card">
          <div className="service-icon" style={{ background: '#fce4ec', color: '#c62828' }}>&#127860;</div>
          <h4>E-Catering</h4>
          <p>Order food on train</p>
        </div>
        <div className="service-card">
          <div className="service-icon" style={{ background: '#f3e5f5', color: '#6a1b9a' }}>&#128716;</div>
          <h4>Retiring Rooms</h4>
          <p>Book rooms at stations</p>
        </div>
        <div className="service-card">
          <div className="service-icon" style={{ background: '#e0f2f1', color: '#00695c' }}>&#9992;</div>
          <h4>Tourism</h4>
          <p>Tour packages</p>
        </div>
      </div>

      {/* Info Section */}
      <section className="info-section">
        <h2>Why Book with IRCTC?</h2>
        <div className="info-grid">
          <div className="info-card">
            <h3>Instant Confirmation</h3>
            <p>Get immediate booking confirmation with PNR number. Check your ticket status anytime with our PNR enquiry feature.</p>
          </div>
          <div className="info-card">
            <h3>Secure Payments</h3>
            <p>Multiple secure payment options including UPI, Net Banking, Credit/Debit cards, and mobile wallets.</p>
          </div>
          <div className="info-card">
            <h3>Easy Cancellation</h3>
            <p>Cancel tickets online with instant refund processing. Time-based refund policy ensures fair refunds.</p>
          </div>
        </div>
      </section>

      {/* Popular Routes */}
      <section className="info-section">
        <h2>Popular Routes</h2>
        <div className="info-grid">
          {[
            { from: 'NDLS', to: 'BCT', name: 'New Delhi to Mumbai' },
            { from: 'NDLS', to: 'HWH', name: 'New Delhi to Howrah' },
            { from: 'NDLS', to: 'SBC', name: 'New Delhi to Bengaluru' },
            { from: 'MAS', to: 'SBC', name: 'Chennai to Bengaluru' },
            { from: 'NDLS', to: 'MAS', name: 'New Delhi to Chennai' },
            { from: 'HWH', to: 'MAS', name: 'Howrah to Chennai' },
          ].map(route => (
            <div
              key={`${route.from}-${route.to}`}
              className="info-card"
              style={{ cursor: 'pointer' }}
              onClick={() => {
                setSource(route.from)
                setDestination(route.to)
                setSourceQuery(route.from)
                setDestQuery(route.to)
                window.scrollTo({ top: 0, behavior: 'smooth' })
              }}
            >
              <h3>{route.name}</h3>
              <p>{route.from} &#8594; {route.to} &middot; Multiple daily trains available</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
