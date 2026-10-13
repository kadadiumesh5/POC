import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div className="footer-col">
          <h4>Quick Links</h4>
          <ul>
            <li><Link to="/">Book Ticket</Link></li>
            <li><Link to="/pnr-status">PNR Enquiry</Link></li>
            <li><Link to="/my-bookings">Booking History</Link></li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Travel Services</h4>
          <ul>
            <li><a href="#">Retiring Rooms</a></li>
            <li><a href="#">Tourism</a></li>
            <li><a href="#">E-Catering</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Information</h4>
          <ul>
            <li><a href="#">About Us</a></li>
            <li><a href="#">Terms of Service</a></li>
            <li><a href="#">Privacy Policy</a></li>
            <li><a href="#">FAQ</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Contact</h4>
          <ul>
            <li><a href="#">Helpline: 139</a></li>
            <li><a href="#">Email: care@irctc.co.in</a></li>
            <li><a href="#">Customer Support</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        IRCTC Booking Platform (Demo) &copy; {new Date().getFullYear()} &mdash; This is a demonstration project, not affiliated with Indian Railways.
      </div>
    </footer>
  )
}
