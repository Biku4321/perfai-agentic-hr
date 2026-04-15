import { useState, useEffect } from 'react'

const STATUS_CONFIG = {
  completed: { label: 'Completed', color: 'var(--green)', bg: 'rgba(16,185,129,0.1)' },
  draft_generated: { label: 'Draft Ready', color: 'var(--blue)', bg: 'rgba(74,158,255,0.1)' },
  pending: { label: 'Pending', color: 'var(--yellow)', bg: 'rgba(251,191,36,0.1)' },
  not_started: { label: 'Not Started', color: 'var(--text-muted)', bg: 'rgba(255,255,255,0.05)' },
}

export default function CycleTracker() {
  const [cycle, setCycle] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/cycle').then(r => r.json()),
      fetch('/api/cycle/health').then(r => r.json()),
    ]).then(([c, h]) => {
      setCycle(c)
      setHealth(h)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ padding: 24 }}>
      <div style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>Loading cycle data...</div>
    </div>
  )

  const reviews = cycle?.reviews || []
  const completionPct = health?.completion_rate || 0
  const aiAssistPct = health?.ai_assist_rate || 0

  return (
    <div>
      {/* Progress bar */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Overall completion</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 500, color: 'var(--text)' }}>
            {completionPct}<span style={{ fontSize: 12, color: 'var(--text-muted)' }}>%</span>
          </div>
        </div>
        <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${aiAssistPct}%`,
            background: 'linear-gradient(90deg, var(--accent), var(--blue))',
            borderRadius: 3, transition: 'width 0.6s ease'
          }} />
        </div>
        <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-muted)' }}>
          {aiAssistPct}% with AI assist · Deadline: {cycle?.deadline}
        </div>
      </div>

      {/* Review list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {reviews.map(r => {
          const cfg = STATUS_CONFIG[r.status] || STATUS_CONFIG.not_started
          return (
            <div key={r.employee_id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', background: 'var(--surface2)',
              borderRadius: 8, border: '1px solid var(--border)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: cfg.bg, color: cfg.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 700
                }}>
                  {r.employee_id.replace('E', '')}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{r.employee_id}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>→ {r.manager_id}</div>
                </div>
              </div>
              <div style={{
                padding: '3px 10px', borderRadius: 100,
                background: cfg.bg, color: cfg.color,
                fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-mono)'
              }}>
                {cfg.label}
              </div>
            </div>
          )
        })}
      </div>

      {/* Stats row */}
      {health && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 16 }}>
          {[
            { label: 'Completed', value: health.completed, color: 'var(--green)' },
            { label: 'AI Draft', value: health.draft_generated, color: 'var(--blue)' },
            { label: 'Pending', value: health.pending, color: 'var(--yellow)' },
          ].map(s => (
            <div key={s.label} style={{
              textAlign: 'center', padding: '10px 8px',
              background: 'var(--surface2)', borderRadius: 8, border: '1px solid var(--border)'
            }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 22, fontWeight: 500, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}