import { useState, useEffect } from 'react'
import CycleTracker from '../components/Dashboard/CycleTracker'

export default function HRView() {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/hr/dashboard')
      .then(res => res.json())
      .then(data => {
        setDashboard(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to fetch HR dashboard", err)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="animate-pulse flex space-x-4">Loading HR Data...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-display">HR Orchestration Dashboard</h1>
        <p className="text-[#6b7a8d]">H1 2024 Performance Cycle Overview</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Tracker */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4 border-b border-[#1f2530] pb-2">Cycle Health</h2>
            <CycleTracker />
          </div>
        </div>

        {/* Right Column: AI Insights & Bias Radar */}
        <div className="lg:col-span-2 space-y-6">
          {dashboard?.ai_summary && (
            <div className="card bg-gradient-to-br from-[#181c24] to-[#111318] border-[#2a3545]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">✨</span>
                <h2 className="text-lg font-semibold text-[#00d4aa]">AI Executive Summary</h2>
              </div>
              <p className="text-sm text-[#e8ecf0] leading-relaxed whitespace-pre-wrap">
                {dashboard.ai_summary}
              </p>
            </div>
          )}

          <div className="card">
            <h2 className="text-lg font-semibold mb-4 border-b border-[#1f2530] pb-2 flex justify-between items-center">
              <span>Fairness & Bias Radar</span>
              <span className="badge badge-red">{dashboard?.bias_flags?.length || 0} Risks Detected</span>
            </h2>
            
            <div className="space-y-3">
              {dashboard?.bias_flags?.length === 0 ? (
                <p className="text-sm text-[#6b7a8d]">No bias patterns detected currently.</p>
              ) : (
                dashboard?.bias_flags?.map((flag, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-[#181c24] border border-[#2a3545] flex flex-col gap-2">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-white">{flag.employee_name}</span>
                      <span className="badge badge-yellow">{flag.type.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="text-xs text-[#6b7a8d]">{flag.description}</p>
                    <div className="text-xs text-[#a855f7] bg-[#a855f7]/10 p-2 rounded mt-1">
                      💡 <strong>AI Recommendation:</strong> {flag.recommendation}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}