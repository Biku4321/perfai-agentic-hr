export default function ReviewDraft({ review, onClose, onApprove }) {
  if (!review) return null;

  const content = review.draft || review.ai_draft || "No draft content available.";

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
      <div className="bg-[#111318] border border-[#2a3545] rounded-xl flex flex-col max-w-3xl w-full max-h-[90vh] shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-[#1f2530] flex justify-between items-start bg-[#181c24] rounded-t-xl">
          <div>
            <h2 className="text-xl font-bold font-display text-white flex items-center gap-2">
              <span className="text-2xl">✨</span> Review Draft
            </h2>
            <div className="text-sm text-[#6b7a8d] mt-1">
              Employee: <span className="text-[#e8ecf0] font-medium">{review.employee_name || review.employee_id}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-[#6b7a8d] hover:text-white transition-colors bg-[#0a0b0e] p-2 rounded-lg border border-[#1f2530]">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>
        
        {/* Editor Area */}
        <div className="p-5 overflow-y-auto flex-1 bg-[#0a0b0e]">
          <div className="flex gap-2 mb-4 items-center flex-wrap">
            <span className="text-xs text-[#6b7a8d]">Evidence pulled from:</span>
            {review.evidence_sources?.map(src => (
              <span key={src} className="badge badge-blue capitalize text-[10px]">{src}</span>
            ))}
          </div>
          
          <textarea 
            className="w-full h-[450px] bg-[#181c24] border border-[#2a3545] rounded-lg p-4 text-sm text-[#e8ecf0] font-mono leading-relaxed focus:outline-none focus:border-[#00d4aa] resize-none shadow-inner"
            defaultValue={content}
          />
        </div>
        
        {/* Footer actions */}
        <div className="p-5 border-t border-[#1f2530] flex flex-col sm:flex-row justify-between items-center gap-4 bg-[#181c24] rounded-b-xl">
          <span className="text-xs text-[#6b7a8d] flex items-center gap-2">
             <span className="text-yellow-500">⚠️</span> AI drafts should be reviewed and edited before submission.
          </span>
          <div className="flex gap-3 w-full sm:w-auto">
            <button className="btn flex-1 sm:flex-none justify-center" onClick={onClose}>Save as Draft</button>
            <button className="btn btn-primary flex-1 sm:flex-none justify-center" onClick={onApprove}>Approve & Finalize</button>
          </div>
        </div>
      </div>
    </div>
  )
}