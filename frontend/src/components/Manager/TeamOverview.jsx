export default function TeamOverview({ team, generatingFor, onGenerateDraft, onViewDraft }) {
  if (!team || team.length === 0) return <div className="text-[#6b7a8d] italic">No team members found.</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {team.map(emp => (
        <div key={emp.id} className="card flex flex-col justify-between hover:border-[#2a3545] transition-colors bg-gradient-to-b from-[#181c24] to-[#111318]">
          <div>
            <div className="flex justify-between items-start mb-2 gap-2">
              <h3 className="font-semibold text-lg text-white truncate">{emp.name}</h3>
              {emp.review_status === 'completed' && <span className="badge badge-green shrink-0">Done</span>}
              {emp.review_status === 'draft_generated' && <span className="badge badge-blue shrink-0">Draft Ready</span>}
              {emp.review_status === 'pending' && <span className="badge badge-yellow shrink-0">Pending</span>}
              {emp.review_status === 'not_started' && <span className="badge badge-accent bg-[#2a3545] text-[#6b7a8d] shrink-0">Not Started</span>}
            </div>
            <p className="text-xs text-[#6b7a8d] mb-4">{emp.role}</p>
            
            <div className="flex gap-1.5 flex-wrap mb-4">
              {emp.signal_sources?.map(src => (
                <span key={src} className="text-[10px] px-2 py-1 rounded-md bg-[#0a0b0e] border border-[#2a3545] text-[#e8ecf0] capitalize">
                  {src}
                </span>
              ))}
            </div>
          </div>

          <div className="border-t border-[#1f2530] pt-4 mt-2">
            {emp.review_status === 'pending' || emp.review_status === 'not_started' ? (
              <button 
                onClick={() => onGenerateDraft(emp.id)}
                disabled={generatingFor === emp.id}
                className="w-full btn flex justify-center bg-[#0a0b0e] border-[#2a3545] hover:border-[#00d4aa] hover:text-[#00d4aa] disabled:opacity-50 transition-all"
              >
                {generatingFor === emp.id ? (
                  <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-[#00d4aa] border-t-transparent rounded-full animate-spin"></span> Analyzing...</span>
                ) : '✨ Auto-Draft Review'}
              </button>
            ) : (
              <button 
                onClick={() => onViewDraft(emp.id)}
                className="w-full btn flex justify-center bg-[#4a9eff]/10 border-[#4a9eff]/30 text-[#4a9eff] hover:bg-[#4a9eff]/20 hover:border-[#4a9eff]"
              >
                Review Generated Draft
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}