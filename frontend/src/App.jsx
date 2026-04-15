import { useState } from 'react'
import HRView from './pages/HRView'
import ManagerView from './pages/ManagerView'
import EmployeeView from './pages/EmployeeView'
import AgentChat from './components/Chat/AgentChat'

function App() {
  const [activeTab, setActiveTab] = useState('manager')

  return (
    <div className="min-h-screen pb-20 selection:bg-[#00d4aa] selection:text-black">
      {/* Frosted Glass Navigation */}
      <nav className="sticky top-0 z-40 glass-panel border-b-0 border-white/5">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center h-auto md:h-20 py-4 md:py-0">
          <div className="flex items-center gap-3 mb-4 md:mb-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00d4aa] to-[#4a9eff] p-[1px] shadow-[0_0_15px_rgba(0,212,170,0.4)]">
              <div className="w-full h-full bg-[#050507] rounded-xl flex items-center justify-center text-white font-display font-bold text-xl">
                P
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-display font-bold text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                PerfAI
              </span>
              <span className="text-[10px] text-[#00d4aa] uppercase tracking-widest font-mono">
                Agentic Layer on effiHR
              </span>
            </div>
          </div>
          
          <div className="flex gap-2 p-1.5 rounded-full bg-black/40 border border-white/5 backdrop-blur-xl">
            {['hr', 'manager', 'employee'].map((tab) => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 capitalize ${
                  activeTab === tab 
                    ? 'bg-gradient-to-r from-[#2a3545] to-[#1f2530] text-white shadow-lg border border-white/10' 
                    : 'text-[#8b9bb4] hover:text-white hover:bg-white/5'
                }`}
              >
                {tab === 'hr' ? 'HR Admin' : `${tab} View`}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content Area with Entrance Animation */}
      <main className="max-w-7xl mx-auto px-6 py-10 animate-fade-in-up">
        {activeTab === 'hr' && <HRView />}
        {activeTab === 'manager' && <ManagerView />}
        {activeTab === 'employee' && <EmployeeView />}
      </main>

      <AgentChat currentContext={activeTab} />

      {/* Signature Footer */}
      <footer className="mt-20 text-center py-8 border-t border-white/5 glass-panel">
        <p className="text-xs text-[#8b9bb4] font-mono tracking-wider">
          ENGINEERED FOR EXCELLENCE BY <span className="text-white font-semibold">BIKASHDEV</span>
        </p>
      </footer>
    </div>
  )
}

export default App