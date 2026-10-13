import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(!!localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      api.getMe()
        .then(setUser)
        .catch(() => { localStorage.removeItem('token'); setToken(null) })
        .finally(() => setLoading(false))
    }
  }, [token])

  const login = async (username, password) => {
    const res = await api.login({ username, password })
    localStorage.setItem('token', res.access_token)
    setToken(res.access_token)
    setUser(res.user)
    return res
  }

  const register = async (data) => {
    const res = await api.register(data)
    localStorage.setItem('token', res.access_token)
    setToken(res.access_token)
    setUser(res.user)
    return res
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() { return useContext(AuthContext) }
