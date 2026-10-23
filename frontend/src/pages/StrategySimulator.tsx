import { useMemo, useState } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useRaces, useStrategySimulation, useTeams } from '../api/hooks'
import { Panel } from '../components/Panel'
import { ErrorState, LoadingState } from '../components/StateViews'
import { Track3DView } from '../three/Track3DView'
import { TireDegradationPanel } from '../components/TireDegradationPanel'
import type { StrategySimulateRequest } from '../api/types'

const COMPOUNDS: StrategySimulateRequest['tire_compound'][] = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']

export default function StrategySimulator() {
  const races = useRaces()
  const teams = useTeams()
  const circuits = useMemo(
    () => Array.from(new Map((races.data ?? []).map((r) => [r.circuit_ref, r.name])).entries()),
    [races.data],
  )

  const [circuitRef, setCircuitRef] = useState<string>('')
  const [startingPosition, setStartingPosition] = useState(10)
  const [tireCompound, setTireCompound] = useState<StrategySimulateRequest['tire_compound']>('MEDIUM')
  const [numLaps, setNumLaps] = useState(55)
  const [pitLap, setPitLap] = useState(27)

  const effectiveCircuit = circuitRef || circuits[0]?.[0] || ''
  const request: StrategySimulateRequest | null = effectiveCircuit
    ? { circuit_ref: effectiveCircuit, starting_position: startingPosition, tire_compound: tireCompound, pit_lap: Math.min(pitLap, numLaps - 1), num_laps: numLaps }
    : null

  const sim = useStrategySimulation(request)
  const accent = teams.data?.[0]?.color_primary ?? '#ff3b30'

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <Panel title="Strategy Controls">
          <div className="space-y-4 text-sm">
            <label className="block">
              <span className="text-steel text-xs block mb-1">Circuit</span>
              <select
                value={effectiveCircuit}
                onChange={(e) => setCircuitRef(e.target.value)}
                className="w-full bg-asphalt border border-hairline px-2 py-1.5 text-paper"
              >
                {circuits.map(([ref, name]) => (
                  <option key={ref} value={ref}>
                    {name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-steel text-xs block mb-1">Starting Position: P{startingPosition}</span>
              <input
                type="range"
                min={1}
                max={20}
                value={startingPosition}
                onChange={(e) => setStartingPosition(Number(e.target.value))}
                className="w-full accent-signal"
              />
            </label>

            <label className="block">
              <span className="text-steel text-xs block mb-1">Tire Compound</span>
              <div className="grid grid-cols-3 gap-1.5">
                {COMPOUNDS.map((c) => (
                  <button
                    key={c}
                    onClick={() => setTireCompound(c)}
                    className={`px-2 py-1.5 text-xs border ${
                      tireCompound === c ? 'border-signal text-paper' : 'border-hairline text-steel'
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </label>

            <label className="block">
              <span className="text-steel text-xs block mb-1">Race Laps: {numLaps}</span>
              <input
                type="range"
                min={20}
                max={70}
                value={numLaps}
                onChange={(e) => {
                  const v = Number(e.target.value)
                  setNumLaps(v)
                  if (pitLap >= v) setPitLap(v - 1)
                }}
                className="w-full accent-signal"
              />
            </label>

            <label className="block">
              <span className="text-steel text-xs block mb-1">Pit Lap: {pitLap}</span>
              <input
                type="range"
                min={1}
                max={numLaps - 1}
                value={pitLap}
                onChange={(e) => setPitLap(Number(e.target.value))}
                className="w-full accent-signal"
              />
            </label>
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel title="Result">
            {sim.isLoading && <LoadingState label="Simulating" />}
            {sim.isError && <ErrorState message={(sim.error as Error).message} />}
            {sim.data && (
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Predicted Finish</p>
                  <p className="text-3xl font-900 tabular">P{sim.data.predicted_finish_position}</p>
                </div>
                <div>
                  <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Race Time</p>
                  <p className="text-3xl font-900 tabular">
                    {Math.floor(sim.data.total_time_estimate_s / 60)}:
                    {String(Math.round(sim.data.total_time_estimate_s % 60)).padStart(2, '0')}
                  </p>
                </div>
                <div>
                  <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Optimal Pit Lap</p>
                  <p className="text-3xl font-900 tabular">{sim.data.optimal_pit_lap}</p>
                </div>
              </div>
            )}
            {sim.data && <p className="text-sm text-steel leading-relaxed">{sim.data.explanation}</p>}
          </Panel>

          {sim.data && (
            <Panel title="Lap Time Curve">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={sim.data.lap_time_curve}>
                  <XAxis dataKey="lap" tick={{ fill: 'var(--color-steel)', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'var(--color-steel)', fontSize: 12 }} width={40} domain={['dataMin - 1', 'dataMax + 1']} />
                  <Tooltip contentStyle={{ background: 'var(--color-graphite)', border: '1px solid var(--color-hairline)' }} />
                  <Line type="monotone" dataKey="lap_time_s" stroke={accent} dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Panel>
          )}

          {effectiveCircuit && <TireDegradationPanel circuitRef={effectiveCircuit} />}
        </div>
      </div>

      <Panel title="Circuit">
        {effectiveCircuit && <Track3DView circuitRef={effectiveCircuit} accent={accent} />}
      </Panel>
    </div>
  )
}
