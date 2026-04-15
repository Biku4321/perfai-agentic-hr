import { useState } from 'react'

export default function AgentChat({ currentContext }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hi! I'm PerfAI. I can help you analyze cycle health, write reviews, or check on employee goals. What do you need?" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg = input
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('https://perfai-backend.onrender.com/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg, 
          context: { current_view: currentContext } 
        })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', text: data.response }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: "Sorry, I'm having trouble connecting to my brain right now." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Floating Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-[#00d4aa] rounded-full flex items-center justify-center shadow-lg shadow-[#00d4aa]/20 hover:scale-105 transition-transform z-50"
      >
        <span className="text-2xl">✨</span>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 bg-[#111318] border border-[#2a3545] rounded-xl shadow-2xl flex flex-col overflow-hidden z-50">
          <div className="bg-[#181c24] border-b border-[#2a3545] p-3 flex justify-between items-center">
            <div className="font-semibold text-sm flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00d4aa] animate-pulse"></span>
              PerfAI Assistant
            </div>
            <button onClick={() => setIsOpen(false)} className="text-[#6b7a8d] hover:text-white">&times;</button>
          </div>
          
          <div className="flex-1 p-4 h-80 overflow-y-auto flex flex-col gap-3 text-sm">
            {messages.map((msg, i) => (
              <div key={i} className={`p-2.5 rounded-lg max-w-[85%] ${msg.role === 'user' ? 'bg-[#2a3545] text-white self-end rounded-tr-none' : 'bg-[#181c24] border border-[#1f2530] text-[#e8ecf0] self-start rounded-tl-none'}`}>
                {msg.text}
              </div>
            ))}
            {loading && <div className="text-xs text-[#6b7a8d] italic ml-2">PerfAI is thinking...</div>}
          </div>

          <form onSubmit={sendMessage} className="p-3 border-t border-[#2a3545] bg-[#181c24] flex gap-2">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about team performance..."
              className="flex-1 bg-[#0a0b0e] border border-[#2a3545] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#00d4aa]"
            />
            <button type="submit" className="bg-[#00d4aa] text-black px-3 py-2 rounded-md font-medium text-sm">
              Send
            </button>
          </form>
        </div>
      )}
    </>
  )
}