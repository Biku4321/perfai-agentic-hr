import { useState } from 'react'

export default function SelfAssistant({ employeeId }) {
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const res = await fetch(`https://perfai-backend.onrender.com/api/employees/${employeeId}/self-assessment-help`)
      const data = await res.json()
      setDraft(data)
    } catch (err) {
      console.error("Failed to generate help:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card h-full flex flex-col bg-gradient-to-b from-[#111318] to-[#181c24] border-[#2a3545]">
      <h2 className="text-lg font-semibold mb-2 flex items-center gap-2 text-white">
        <span className="text-xl">✨</span> AI Self-Assessment Coach
      </h2>
      <p className="text-sm text-[#6b7a8d] mb-4">
        Struggling with what to write? I'll analyze your Jira, GitHub, and Slack data to generate evidence-backed talking points.
      </p>

      {!draft ? (
        <div className="flex-1 flex items-center justify-center border-2 border-dashed border-[#2a3545] rounded-xl p-6 min-h-[250px]">
          <button 
            onClick={generate}
            disabled={loading}
            className="btn btn-primary shadow-lg shadow-[#00d4aa]/20"
          >
            {loading ? 'Analyzing Work Signals...' : 'Generate My Talking Points'}
          </button>
        </div>
      ) : (
        <div className="space-y-4 flex-1 flex flex-col justify-between">
          <div className="p-4 bg-[#0a0b0e] border border-[#2a3545] rounded-lg h-[300px] overflow-y-auto">
            <div className="text-[10px] text-[#00d4aa] mb-3 font-mono uppercase tracking-wider">Suggested Evidence-Backed Points</div>
            <div className="text-sm text-[#e8ecf0] whitespace-pre-wrap font-mono leading-relaxed">
              {draft.talking_points}
            </div>
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button className="btn" onClick={() => setDraft(null)}>Reset</button>
            <button className="btn btn-primary" onClick={() => navigator.clipboard.writeText(draft.talking_points)}>Copy to Clipboard</button>
          </div>
        </div>
      )}
    </div>
  )
}