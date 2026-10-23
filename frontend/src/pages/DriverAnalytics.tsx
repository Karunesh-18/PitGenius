import { Link, useParams } from 'react-router-dom'
import {
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useDriver, useDriverPointsHistory, useDrivers, useTeams } from '../api/hooks'
import { Panel } from '../components/Panel'
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews'
import { TeamTag } from '../components/TeamTag'

export default function DriverAnalytics() {
  const { driverRef } = useParams()
  return driverRef ? <DriverDetailView driverRef={driverRef} /> : <DriverListView />
}

function DriverListView() {
  const drivers = useDrivers()
  const teams = useTeams()
  const colorByTeamRef = new Map((teams.data ?? []).map((t) => [t.team_ref, t.color_primary]))

  if (drivers.isLoading) return <LoadingState label="Loading drivers" />
  if (drivers.isError) return <ErrorState message={(drivers.error as Error).message} />
  if (!drivers.data || drivers.data.length === 0) return <EmptyState message="No drivers loaded yet." />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {drivers.data.map((d) => (
        <Link key={d.driver_ref} to={`/drivers/${d.driver_ref}`}>
          <Panel accent={colorByTeamRef.get(d.team_ref ?? '') ?? undefined} className="h-full hover:bg-graphite-raised transition-colors">
            <div className="flex items-baseline justify-between mb-2">
              <h3 className="font-600">
                {d.given_name} {d.family_name}
              </h3>
              <span className="tabular text-lg font-700">{d.driver_rating.toFixed(1)}</span>
            </div>
            <TeamTag name={d.team_name ?? 'Unknown'} color={colorByTeamRef.get(d.team_ref ?? '')} />
            <div className="flex justify-between text-sm text-steel mt-3 tabular">
              <span>{d.points} pts</span>
              <span>{d.wins} wins</span>
            </div>
          </Panel>
        </Link>
      ))}
    </div>
  )
}

function DriverDetailView({ driverRef }: { driverRef: string }) {
  const driver = useDriver(driverRef)
  const teams = useTeams()
  const pointsHistory = useDriverPointsHistory(driverRef)
  const teamColor = teams.data?.find((t) => t.team_ref === driver.data?.team_ref)?.color_primary

  if (driver.isLoading) return <LoadingState label="Loading driver" />
  if (driver.isError) return <ErrorState message={(driver.error as Error).message} />
  if (!driver.data) return <EmptyState message="Driver not found." />

  const d = driver.data
  const radarData = [
    { metric: 'Qualifying', value: d.rating_breakdown.qualifying_pace },
    { metric: 'Race Pace', value: d.rating_breakdown.race_pace },
    { metric: 'Consistency', value: d.rating_breakdown.consistency },
    { metric: 'Finishes', value: d.rating_breakdown.finishes },
  ]
  const finishTrend = d.results.map((r) => ({ round: r.round, finish: r.finish_position ?? 21 }))

  return (
    <div className="space-y-6">
      <Link to="/drivers" className="text-sm text-steel hover:text-paper">
        ← All drivers
      </Link>

      <div className="border border-hairline bg-graphite px-5 py-4" style={{ borderTopWidth: 2, borderTopColor: teamColor ?? undefined }}>
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <div>
            <h1 className="text-2xl font-700">
              {d.given_name} {d.family_name}
            </h1>
            <TeamTag name={d.team_name ?? 'Unknown'} color={teamColor} />
            {d.nationality && <p className="text-steel text-sm mt-1">{d.nationality}</p>}
          </div>
          <div className="text-right">
            <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Driver Rating</p>
            <p className="text-3xl font-900 tabular">{d.driver_rating.toFixed(1)}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="Rating Breakdown">
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="var(--color-hairline)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: 'var(--color-steel)', fontSize: 12 }} />
              <Radar dataKey="value" stroke="var(--color-signal)" fill="var(--color-signal)" fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Finish Position by Round">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={finishTrend}>
              <XAxis dataKey="round" tick={{ fill: 'var(--color-steel)', fontSize: 12 }} />
              <YAxis reversed domain={[1, 20]} tick={{ fill: 'var(--color-steel)', fontSize: 12 }} width={24} />
              <Tooltip contentStyle={{ background: 'var(--color-graphite)', border: '1px solid var(--color-hairline)' }} />
              <Line type="monotone" dataKey="finish" stroke="var(--color-signal)" dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="Points Progression">
        {pointsHistory.isLoading && <LoadingState label="Loading points history" />}
        {pointsHistory.isError && <ErrorState message={(pointsHistory.error as Error).message} />}
        {pointsHistory.data && (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={pointsHistory.data}>
              <XAxis dataKey="round" tick={{ fill: 'var(--color-steel)', fontSize: 12 }} />
              <YAxis tick={{ fill: 'var(--color-steel)', fontSize: 12 }} width={32} />
              <Tooltip contentStyle={{ background: 'var(--color-graphite)', border: '1px solid var(--color-hairline)' }} />
              <Line type="monotone" dataKey="points" stroke={teamColor ?? 'var(--color-signal)'} dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Panel>

      <Panel title="Race Results">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-steel text-left border-b border-hairline">
              <th className="font-500 py-1.5 pr-3">Rnd</th>
              <th className="font-500 py-1.5 pr-3">Race</th>
              <th className="font-500 py-1.5 pr-3 text-right">Grid</th>
              <th className="font-500 py-1.5 pr-3 text-right">Finish</th>
              <th className="font-500 py-1.5 pr-3">Status</th>
              <th className="font-500 py-1.5 text-right">Points</th>
            </tr>
          </thead>
          <tbody>
            {d.results.map((r) => (
              <tr key={r.round} className="border-b border-hairline last:border-0 tabular">
                <td className="py-1.5 pr-3">{r.round}</td>
                <td className="py-1.5 pr-3">{r.race_name}</td>
                <td className="py-1.5 pr-3 text-right">{r.grid_position ?? '—'}</td>
                <td className="py-1.5 pr-3 text-right">{r.finish_position ?? '—'}</td>
                <td className="py-1.5 pr-3">{r.status}</td>
                <td className="py-1.5 text-right font-600">{r.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  )
}
