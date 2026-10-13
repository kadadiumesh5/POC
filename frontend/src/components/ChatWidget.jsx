import { useState, useRef, useEffect } from 'react'
import { api } from '../api/api'

const SESSION_KEY = 'irctc_chat_session'

function getSessionId() {
  let id = sessionStorage.getItem(SESSION_KEY)
  if (!id) {
    id = 'sess_' + Math.random().toString(36).slice(2) + Date.now().toString(36)
    sessionStorage.setItem(SESSION_KEY, id)
  }
  return id
}

function formatReply(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Namaste! I'm your IRCTC booking assistant. How can I help you today?\n\nTry: \"trains from Delhi to Mumbai tomorrow\" or say \"help\" for all options.",
      suggestions: ['Search trains', 'PNR status', 'Tatkal rules', 'Help'],
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [hasNewMessage, setHasNewMessage] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return

    const userMsg = { role: 'user', text: text.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text.trim(), session_id: getSessionId() }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Something went wrong')
      }

      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.reply,
        intent: data.intent,
        suggestions: data.suggestions || [],
        data: data.data,
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `Sorry, I encountered an error: ${err.message}. Please try again.`,
        suggestions: ['Help', 'Search trains'],
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion)
  }

  const toggleChat = () => {
    setIsOpen(!isOpen)
    if (!isOpen) setHasNewMessage(false)
  }

  return (
    <>
      {/* Chat FAB */}
      <button
        className="chat-fab"
        onClick={toggleChat}
        title="Chat with IRCTC Assistant"
      >
        {isOpen ? (
          <span style={{ fontSize: 20 }}>✕</span>
        ) : (
          <>
            <span style={{ fontSize: 22 }}>💬</span>
            {hasNewMessage && <span className="chat-fab-badge"></span>}
          </>
        )}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="chat-panel">
          {/* Header */}
          <div className="chat-panel-header">
            <div className="chat-panel-header-info">
              <div className="chat-avatar">🤖</div>
              <div>
                <div className="chat-agent-name">IRCTC Assistant</div>
                <div className="chat-agent-status">
                  <span className="chat-status-dot"></span> Online
                </div>
              </div>
            </div>
            <button className="chat-panel-close" onClick={() => setIsOpen(false)}>✕</button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                {msg.role === 'assistant' && <div className="chat-msg-avatar">🤖</div>}
                <div className={`chat-bubble ${msg.role}`}>
                  <div dangerouslySetInnerHTML={{ __html: formatReply(msg.text) }} />
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="chat-suggestions">
                      {msg.suggestions.map((s, i) => (
                        <button
                          key={i}
                          className="chat-suggestion-btn"
                          onClick={() => handleSuggestionClick(s)}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-message assistant">
                <div className="chat-msg-avatar">🤖</div>
                <div className="chat-bubble assistant">
                  <div className="chat-typing">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form className="chat-input-area" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || loading}
            >
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  )
}
