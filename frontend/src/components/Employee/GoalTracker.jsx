export default function GoalTracker({ goals = [] }) {
  if (!goals.length) return <div className="card text-[#6b7a8d]">No goals tracked for this cycle.</div>

  return (
    <div className="card space-y-4 border-[#2a3545]">
      <h2 className="text-lg font-semibold border-b border-[#1f2530] pb-2 text-white flex justify-between">
        <span>Active Goals</span>
        <span className="text-xs text-[#6b7a8d] font-normal self-end">{goals.length} Tracked</span>
      </h2>
      <div className="space-y-5">
        {goals.map(g => (
          <div key={g.id} className="space-y-1.5">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-[#e8ecf0] truncate pr-4">{g.title}</span>
              <span className="text-[#00d4aa] font-mono shrink-0">{g.progress}%</span>
            </div>
            <div className="h-2 w-full bg-[#0a0b0e] rounded-full overflow-hidden border border-[#1f2530]">
              <div 
                className="h-full bg-gradient-to-r from-[#00d4aa] to-[#4a9eff] transition-all duration-1000 ease-out"
                style={{ width: `${g.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}