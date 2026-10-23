import { Route, Routes } from 'react-router-dom'
import { NavRail } from './components/NavRail'
import { SEASON } from './api/hooks'
import CircuitIntelligence from './pages/CircuitIntelligence'
import DriverAnalytics from './pages/DriverAnalytics'
import Home from './pages/Home'
import StrategySimulator from './pages/StrategySimulator'
import TeamAnalytics from './pages/TeamAnalytics'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-4 h-12 border-b border-hairline shrink-0">
        <span className="text-sm font-700 tracking-[0.02em]">PitGenius</span>
        <span className="text-xs text-steel tabular">{SEASON} Season</span>
      </header>
      <div className="flex flex-1 min-h-0">
        <NavRail />
        <main className="flex-1 min-w-0 p-6 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/drivers" element={<DriverAnalytics />} />
            <Route path="/drivers/:driverRef" element={<DriverAnalytics />} />
            <Route path="/teams" element={<TeamAnalytics />} />
            <Route path="/teams/:teamRef" element={<TeamAnalytics />} />
            <Route path="/strategy" element={<StrategySimulator />} />
            <Route path="/circuits" element={<CircuitIntelligence />} />
            <Route path="/circuits/:circuitRef" element={<CircuitIntelligence />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
