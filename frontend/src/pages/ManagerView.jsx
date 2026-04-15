import { useState, useEffect } from 'react'

export default function ManagerView() {
  const [team, setTeam] = useState([])
  const [loading, setLoading] = useState(true)
  const [generatingFor, setGeneratingFor] = useState(null)

  const MANAGER_ID = 'M001'

  useEffect(() => {
    fetch(`https://perfai-backend.onrender.com/api/managers/${MANAGER_ID}/team`)
      .then(r => r.json())
      .then(data => {
        setTeam(data)
        setLoading(false)
      })
  }, [])

  const generateDraft = async (employeeId) => {
    setGeneratingFor(employeeId)
    try {
      await fetch('https://perfai-backend.onrender.com/api/reviews/generate-draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: employeeId, cycle_id: 'CYC-2024-H1' })
      })
      const updatedTeam = await fetch(`/api/managers/${MANAGER_ID}/team`).then(r => r.json())
      setTeam(updatedTeam)
    } catch (err) {
      console.error(err)
    } finally {
      setGeneratingFor(null)
    }
  }

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-[50vh] gap-4">
      <div className="w-12 h-12 border-4 border-white/10 border-t-[#00d4aa] rounded-full animate-spin"></div>
      <p className="font-mono text-[#8b9bb4] animate-pulse">Syncing organizational data...</p>
    </div>
  )

  return (
    <div className="space-y-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-4xl font-bold font-display tracking-tight text-white mb-2">My Direct Reports</h1>
          <p className="text-[#8b9bb4] text-lg flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00d4aa] animate-pulse"></span>
            Active Appraisal Cycle: H1 2024
          </p>
        </div>
        <button className="btn-modern px-6 py-3 rounded-xl font-bold tracking-wide shadow-lg">
          Auto-Draft All Pending
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {team.map((emp, index) => (
          <div 
            key={emp.id} 
            className="glass-card p-6 flex flex-col justify-between animate-fade-in-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div>
              <div className="flex justify-between items-start mb-4 gap-3">
                <div>
                  <h3 className="font-display font-bold text-xl text-white truncate">{emp.name}</h3>
                  <p className="text-sm text-[#8b9bb4] mt-1">{emp.role}</p>
                </div>
                {emp.review_status === 'completed' && <span className="px-3 py-1 bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20 rounded-full text-xs font-bold shrink-0">Done</span>}
                {emp.review_status === 'draft_generated' && <span className="px-3 py-1 bg-[#4a9eff]/10 text-[#4a9eff] border border-[#4a9eff]/20 rounded-full text-xs font-bold shrink-0 shadow-[0_0_10px_rgba(74,158,255,0.2)]">Draft Ready</span>}
                {emp.review_status === 'pending' && <span className="px-3 py-1 bg-[#fbbf24]/10 text-[#fbbf24] border border-[#fbbf24]/20 rounded-full text-xs font-bold shrink-0">Pending</span>}
              </div>
              
              <div className="space-y-2 mb-6">
                <p className="text-xs text-[#8b9bb4] uppercase tracking-wider font-mono">Aggregated Signals</p>
                <div className="flex gap-2 flex-wrap">
                  {emp.signal_sources.map(src => (
                    <span key={src} className="text-xs px-2.5 py-1 rounded bg-black/40 border border-white/5 text-[#e8ecf0] capitalize flex items-center gap-1">
                      {src === 'github' && '🐙'} {src === 'jira' && '🎫'} {src === 'slack' && '💬'} {src === 'confluence' && '📄'}
                      {src}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-white/5">
              {emp.review_status === 'pending' ? (
                <button 
                  onClick={() => generateDraft(emp.id)}
                  disabled={generatingFor === emp.id}
                  className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium transition-all duration-300 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generatingFor === emp.id ? (
                    <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span> Processing...</>
                  ) : (
                    <>✨ Generate AI Review</>
                  )}
                </button>
              ) : (
                <button className="w-full py-3 rounded-xl bg-[#4a9eff]/10 hover:bg-[#4a9eff]/20 border border-[#4a9eff]/30 text-[#4a9eff] font-medium transition-all shadow-[0_0_15px_rgba(74,158,255,0.1)]">
                  Review Generated Draft
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}