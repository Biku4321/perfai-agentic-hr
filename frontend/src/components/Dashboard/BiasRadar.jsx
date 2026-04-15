import { useState, useEffect } from 'react'

export default function BiasRadar() {
  const [flags, setFlags] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('https://perfai-backend.onrender.com/api/hr/bias-flags')
      .then(r => r.json())
      .then(data => {
        setFlags(data.detected || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-sm text-[#6b7a8d] animate-pulse">Scanning for bias patterns...</div>

  return (
    <div className="space-y-3">
      {flags.length === 0 ? (
        <div className="p-4 rounded-lg bg-[#181c24] border border-[#2a3545] text-center text-[#6b7a8d]">
          ✅ No statistical bias patterns detected in this cycle.
        </div>
      ) : (
        flags.map((flag, idx) => (
          <div key={idx} className="p-3 rounded-lg bg-[#181c24] border border-[#2a3545] flex flex-col gap-2">
            <div className="flex justify-between items-start gap-2">
              <span className="text-sm font-medium text-white">{flag.employee_name}</span>
              <span className={`badge shrink-0 ${flag.severity === 'high' ? 'badge-red' : 'badge-yellow'}`}>
                {flag.type.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-xs text-[#6b7a8d] leading-relaxed">{flag.description}</p>
            {flag.recommendation && (
              <div className="text-xs text-[#00d4aa] bg-[#00d4aa]/10 p-2 rounded mt-1 border border-[#00d4aa]/20">
                💡 <strong>Action Required:</strong> {flag.recommendation}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}