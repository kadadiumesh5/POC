import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Header from './components/Header'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import TrainList from './pages/TrainList'
import BookingPage from './pages/BookingPage'
import BookingConfirmation from './pages/BookingConfirmation'
import PnrStatus from './pages/PnrStatus'
import MyBookings from './pages/MyBookings'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Header />
        <main style={{ minHeight: 'calc(100vh - 160px)' }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/trains" element={<TrainList />} />
            <Route path="/booking" element={<BookingPage />} />
            <Route path="/booking/confirmation/:pnr" element={<BookingConfirmation />} />
            <Route path="/pnr-status" element={<PnrStatus />} />
            <Route path="/my-bookings" element={<MyBookings />} />
          </Routes>
        </main>
        <Footer />
        <ChatWidget />
      </BrowserRouter>
    </AuthProvider>
  )
}
