const API = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `Error ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Auth
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // Stations
  getStations: () => request('/trains/stations'),

  // Trains
  searchTrains: (source, destination, date) =>
    request(`/trains/search?source=${source}&destination=${destination}&travel_date=${date}`),

  // Availability
  checkAvailability: (trainNumber, classCode, date) =>
    request(`/trains/${trainNumber}/availability?class_code=${classCode}&travel_date=${date}`),

  // Bookings
  createBooking: (data) => request('/bookings', { method: 'POST', body: JSON.stringify(data) }),
  getBooking: (pnr) => request(`/bookings/${pnr}`),
  cancelBooking: (pnr) => request(`/bookings/${pnr}/cancel`, { method: 'POST' }),
  listBookings: (limit = 50) => request(`/bookings?limit=${limit}`),
}
