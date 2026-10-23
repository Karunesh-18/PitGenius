import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Panel } from '../components/Panel'
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews'
import { Track3DView } from '../three/Track3DView'
import { useTelemetryPlayback } from '../three/useTelemetryPlayback'
import { countryToFlag } from '../theme/countryToFlag'
import {
  useCircuitIntelligence,
  useCircuits,
  useDriverTelemetry,
  useDrivers,
  useRaces,
  useTeams,
  useTelemetryDrivers,
} from '../api/hooks'
import type { TelemetryPoint } from '../api/types'

/** Nearest-point sample for the live speed/gear/DRS readout at a given elapsedMs. */
function sampleTelemetryAt(points: TelemetryPoint[], elapsedMs: number): TelemetryPoint | null {
  if (points.length === 0) return null
  let closest = points[0]
  let bestDiff = Math.abs(points[0].time_ms - elapsedMs)
  for (const p of points) {
    const diff = Math.abs(p.time_ms - elapsedMs)
    if (diff < bestDiff) {
      bestDiff = diff
      closest = p
    }
  }
  return closest
}

/** FastF1 encodes the DRS channel as a small enum, not a boolean: 10/12/14 mean
 * the flap is open, while 0/1/8 mean closed (8 = in a detection zone / eligible,
 * but not yet activated). */
const DRS_OPEN_CODES = new Set([10, 12, 14])

function isDrsOpen(drs: number | null | undefined): boolean {
  return drs != null && DRS_OPEN_CODES.has(drs)
}

export default function CircuitIntelligence() {
  const { circuitRef } = useParams()
  // `key` remounts the detail view when the route param changes: React Router
  // reuses the component instance otherwise, leaking the selected driver (who
  // may not exist at the next circuit's round) across navigations.
  return circuitRef ? <CircuitDetailView key={circuitRef} circuitRef={circuitRef} /> : <CircuitListView />
}

function CircuitListView() {
  const circuits = useCircuits()

  if (circuits.isLoading) return <LoadingState label="Loading circuits" />
  if (circuits.isError) return <ErrorState message={(circuits.error as Error).message} />
  if (!circuits.data || circuits.data.length === 0) return <EmptyState message="No circuits loaded yet." />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {circuits.data.map((c) => (
        <Link key={c.circuit_ref} to={`/circuits/${c.circuit_ref}`}>
          <Panel className="h-full hover:bg-graphite-raised transition-colors">
            <h3 className="font-600 mb-2">{c.name}</h3>
            <p className="text-steel text-sm mb-3">
              {c.country ? `${countryToFlag[c.country] ?? ''} ${c.country}` : 'Unknown'}
            </p>
            <div className="text-sm tabular">
              <p className="text-steel text-xs">Length</p>
              <p className="font-600">{c.length_km != null ? `${c.length_km.toFixed(3)} km` : '—'}</p>
            </div>
          </Panel>
        </Link>
      ))}
    </div>
  )
}

function CircuitDetailView({ circuitRef }: { circuitRef: string }) {
  const circuits = useCircuits()
  const races = useRaces()
  const teams = useTeams()
  const drivers = useDrivers()
  const intelligence = useCircuitIntelligence(circuitRef)

  const circuit = circuits.data?.find((c) => c.circuit_ref === circuitRef)
  // Telemetry is keyed by round rather than circuit_ref — resolve the most
  // recent race actually run at this circuit this season.
  const roundsAtCircuit = (races.data ?? []).filter((r) => r.circuit_ref === circuitRef).map((r) => r.round)
  const round = roundsAtCircuit.at(-1)

  const availableDrivers = useTelemetryDrivers(round)
  const [driverRef, setDriverRef] = useState<string>('')
  const activeDriverRef = driverRef || availableDrivers.data?.[0]?.driver_ref || ''

  const telemetry = useDriverTelemetry(round, activeDriverRef || undefined)
  const lapDurationMs = telemetry.data?.lap_time_ms ?? 90000
  const playback = useTelemetryPlayback(lapDurationMs)
  const current = telemetry.data ? sampleTelemetryAt(telemetry.data.points, playback.elapsedMs) : null
  const activeDriverTeamRef = drivers.data?.find((d) => d.driver_ref === activeDriverRef)?.team_ref
  const driverColor = teams.data?.find((t) => t.team_ref === activeDriverTeamRef)?.color_primary ?? '#ff3b30'

  if (circuits.isLoading) return <LoadingState label="Loading circuit" />
  if (circuits.isError) return <ErrorState message={(circuits.error as Error).message} />
  if (!circuit) return <EmptyState message="Circuit not found." />

  return (
    <div className="space-y-6">
      <Link to="/circuits" className="text-sm text-steel hover:text-paper">
        ← All circuits
      </Link>

      <div className="border border-hairline bg-graphite px-5 py-4">
        <h1 className="text-2xl font-700">{circuit.name}</h1>
        <p className="text-steel text-sm mt-1">
          {circuit.country ? `${countryToFlag[circuit.country] ?? ''} ${circuit.country}` : 'Unknown'}
          {circuit.length_km != null ? ` · ${circuit.length_km.toFixed(3)} km` : ''}
        </p>
      </div>

      {intelligence.isError ? (
        <Panel title="Circuit Intelligence">
          <ErrorState message={(intelligence.error as Error).message} />
        </Panel>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Panel title="Overtaking Index">
            <p className="text-3xl font-900 tabular">
              {intelligence.data?.overtaking_index != null
                ? intelligence.data.overtaking_index.toFixed(1)
                : '—'}
            </p>
            <p className="text-steel text-sm mt-1">Relative ease of on-track passing, 0-100 (estimate).</p>
          </Panel>
          <Panel title="Safety Car Probability">
            <p className="text-3xl font-900 tabular">
              {intelligence.data?.safety_car_probability_pct != null
                ? `${intelligence.data.safety_car_probability_pct.toFixed(1)}%`
                : '—'}
            </p>
            <p className="text-steel text-sm mt-1">Historical likelihood of a safety car during the race.</p>
          </Panel>
          <Panel title="Avg Pit Loss">
            <p className="text-3xl font-900 tabular">
              {intelligence.data?.avg_pit_loss_s != null ? `${intelligence.data.avg_pit_loss_s.toFixed(1)}s` : '—'}
            </p>
            <p className="text-steel text-sm mt-1">Estimated time lost per pit stop at this circuit (estimate).</p>
          </Panel>
        </div>
      )}

      <Panel title="Lap Playback">
        {availableDrivers.isLoading && <LoadingState label="Loading telemetry" />}
        {!availableDrivers.isLoading && (!availableDrivers.data || availableDrivers.data.length === 0) && (
          <EmptyState message="No telemetry loaded yet for this circuit — run the telemetry ETL step for this round." />
        )}
        {availableDrivers.data && availableDrivers.data.length > 0 && (
          <>
            <div className="flex flex-wrap items-end gap-4 mb-4">
              <label className="block">
                <span className="text-steel text-xs block mb-1">Driver</span>
                <select
                  value={activeDriverRef}
                  onChange={(e) => {
                    playback.pause()
                    playback.scrubTo(0)
                    setDriverRef(e.target.value)
                  }}
                  className="bg-asphalt border border-hairline px-2 py-1.5 text-paper text-sm"
                >
                  {availableDrivers.data.map((d) => (
                    <option key={d.driver_ref} value={d.driver_ref}>
                      {d.code ?? d.driver_ref}
                    </option>
                  ))}
                </select>
              </label>

              <button
                onClick={() => (playback.isPlaying ? playback.pause() : playback.play())}
                className="px-3 py-1.5 text-sm border border-hairline hover:border-signal"
              >
                {playback.isPlaying ? 'Pause' : 'Play'}
              </button>

              <div className="flex-1 min-w-[160px]">
                <span className="text-steel text-xs block mb-1">Scrub</span>
                <input
                  type="range"
                  min={0}
                  max={lapDurationMs}
                  value={playback.elapsedMs}
                  onChange={(e) => playback.scrubTo(Number(e.target.value))}
                  onPointerDown={playback.beginScrub}
                  onPointerUp={playback.endScrub}
                  onPointerCancel={playback.endScrub}
                  className="w-full accent-signal"
                />
              </div>

              {current && (
                <div className="flex gap-4 text-sm">
                  <div>
                    <p className="text-steel text-xs">Speed</p>
                    <p className="font-700 tabular">{current.speed_kph?.toFixed(0) ?? '—'} kph</p>
                  </div>
                  <div>
                    <p className="text-steel text-xs">Gear</p>
                    <p className="font-700 tabular">{current.gear ?? '—'}</p>
                  </div>
                  <div>
                    <p className="text-steel text-xs">DRS</p>
                    <p className={`font-700 tabular ${isDrsOpen(current.drs) ? 'text-green-best' : ''}`}>
                      {isDrsOpen(current.drs) ? 'OPEN' : '—'}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {telemetry.isLoading && <LoadingState label="Loading lap" />}
            {telemetry.isError && <ErrorState message={(telemetry.error as Error).message} />}
            {telemetry.data && (
              <Track3DView
                circuitRef={circuitRef}
                accent={driverColor}
                telemetry={telemetry.data.points}
                elapsedMs={playback.elapsedMs}
                driverColor={driverColor}
              />
            )}
          </>
        )}
      </Panel>
    </div>
  )
}
