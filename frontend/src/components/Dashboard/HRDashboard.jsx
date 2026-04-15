import { useState, useEffect } from 'react'

export default function HRDashboard() {
  const [report, setReport] = useState(null)
  
  useEffect(() => {
    fetch('https://perfai-backend.onrender.com/api/hr/dashboard')
      .then(r => r.json())
      .then(setReport)
  }, [])

  if (!report) return <div className="animate-pulse h-24 bg-[#181c24] rounded-xl border border-[#2a3545]"></div>

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="card text-center bg-[#111318] border-[#2a3545]">
        <div className="text-3xl font-mono text-white mb-1">{report.health?.total_reviews || 0}</div>
        <div className="text-xs text-[#6b7a8d] uppercase tracking-wide">Total Reviews</div>
      </div>
      <div className="card text-center bg-[#111318] border-[#2a3545]">
        <div className="text-3xl font-mono text-[#00d4aa] mb-1">{report.health?.completion_rate || 0}%</div>
        <div className="text-xs text-[#6b7a8d] uppercase tracking-wide">Completion Rate</div>
      </div>
      <div className="card text-center bg-[#111318] border-[#2a3545]">
        <div className="text-3xl font-mono text-[#4a9eff] mb-1">{report.health?.ai_assist_rate || 0}%</div>
        <div className="text-xs text-[#6b7a8d] uppercase tracking-wide">AI Assist Rate</div>
      </div>
      <div className="card text-center bg-[#111318] border-[#ef4444]/30">
        <div className="text-3xl font-mono text-[#ef4444] mb-1">{report.health?.at_risk_managers?.length || 0}</div>
        <div className="text-xs text-[#ef4444]/70 uppercase tracking-wide">At-Risk Managers</div>
      </div>
    </div>
  )
}