import { useState, useEffect } from 'react'
import GoalTracker from '../components/Employee/GoalTracker'
import SelfAssistant from '../components/Employee/SelfAssistant'

export default function EmployeeView() {
  const [employee, setEmployee] = useState(null)
  const [loading, setLoading] = useState(true)
  
  // Hardcoded for hackathon demo purposes
  const EMP_ID = 'E001'

  useEffect(() => {
    fetch(`/api/employees/${EMP_ID}`)
      .then(res => res.json())
      .then(data => {
        setEmployee(data)
        setLoading(false)
      })
      .catch(err => console.error(err))
  }, [])

  if (loading) return <div className="animate-pulse">Loading Your Profile...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-display text-white">Welcome back, {employee?.name}</h1>
        <p className="text-[#6b7a8d]">{employee?.role} · H1 2024 Appraisal Cycle</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <GoalTracker goals={employee?.goals} />
          
          {/* Quick Stats Widget */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card bg-[#181c24] border-[#2a3545]">
              <div className="text-xs text-[#6b7a8d] mb-1">Jira Velocity</div>
              <div className="text-xl font-mono text-[#4a9eff]">{employee?.work_signals?.jira?.sprint_velocity || 0} pts</div>
            </div>
            <div className="card bg-[#181c24] border-[#2a3545]">
              <div className="text-xs text-[#6b7a8d] mb-1">GitHub PRs</div>
              <div className="text-xl font-mono text-[#a855f7]">{employee?.work_signals?.github?.prs_merged || 0} merged</div>
            </div>
          </div>
        </div>
        
        <div>
          <SelfAssistant employeeId={EMP_ID} />
        </div>
      </div>
    </div>
  )
}