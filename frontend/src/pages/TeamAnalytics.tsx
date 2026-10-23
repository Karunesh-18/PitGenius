import { Link, useParams } from 'react-router-dom'
import { useTeam, useTeams } from '../api/hooks'
import { Panel } from '../components/Panel'
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews'

export default function TeamAnalytics() {
  const { teamRef } = useParams()
  return teamRef ? <TeamDetailView teamRef={teamRef} /> : <TeamListView />
}

function TeamListView() {
  const teams = useTeams()

  if (teams.isLoading) return <LoadingState label="Loading teams" />
  if (teams.isError) return <ErrorState message={(teams.error as Error).message} />
  if (!teams.data || teams.data.length === 0) return <EmptyState message="No teams loaded yet." />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {teams.data.map((t) => (
        <Link key={t.team_ref} to={`/teams/${t.team_ref}`}>
          <Panel accent={t.color_primary ?? undefined} className="h-full hover:bg-graphite-raised transition-colors">
            <h3 className="font-600 mb-2">{t.name}</h3>
            <div className="grid grid-cols-3 gap-2 text-sm tabular">
              <div>
                <p className="text-steel text-xs">Points</p>
                <p className="font-600">{t.points}</p>
              </div>
              <div>
                <p className="text-steel text-xs">Reliability</p>
                <p className="font-600">{t.reliability_pct != null ? `${t.reliability_pct}%` : '—'}</p>
              </div>
              <div>
                <p className="text-steel text-xs">Wins</p>
                <p className="font-600">{t.wins}</p>
              </div>
            </div>
          </Panel>
        </Link>
      ))}
    </div>
  )
}

function TeamDetailView({ teamRef }: { teamRef: string }) {
  const team = useTeam(teamRef)

  if (team.isLoading) return <LoadingState label="Loading team" />
  if (team.isError) return <ErrorState message={(team.error as Error).message} />
  if (!team.data) return <EmptyState message="Team not found." />

  const t = team.data
  const maxPoints = Math.max(...t.drivers.map((d) => d.points), 1)

  return (
    <div className="space-y-6">
      <Link to="/teams" className="text-sm text-steel hover:text-paper">
        ← All teams
      </Link>

      <div className="border border-hairline bg-graphite px-5 py-4" style={{ borderTopWidth: 2, borderTopColor: t.color_primary ?? undefined }}>
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <h1 className="text-2xl font-700">{t.name}</h1>
          <div className="flex gap-6 text-right">
            <div>
              <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Points</p>
              <p className="text-xl font-700 tabular">{t.points}</p>
            </div>
            <div>
              <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Wins</p>
              <p className="text-xl font-700 tabular">{t.wins}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="Reliability">
          <p className="text-3xl font-900 tabular">{t.reliability_pct != null ? `${t.reliability_pct}%` : '—'}</p>
          <p className="text-steel text-sm mt-1">Share of race starts classified at the finish this season.</p>
        </Panel>
        <Panel title="Pit Efficiency (estimate)">
          <p className="text-3xl font-900 tabular">
            {t.pit_efficiency_estimate_s != null ? `+${t.pit_efficiency_estimate_s.toFixed(1)}s` : '—'}
          </p>
          <p className="text-steel text-sm mt-1">
            Estimated time lost on pit-in/out laps vs. normal pace — approximated from lap data, not measured
            pit-lane time.
          </p>
        </Panel>
      </div>

      <Panel title="Driver vs. Teammate">
        <div className="space-y-4">
          {t.drivers.map((d) => (
            <div key={d.driver_ref} className="text-sm">
              <div className="flex justify-between mb-1">
                <span className="font-600">
                  {d.given_name} {d.family_name}
                </span>
                <span className="tabular text-steel">
                  avg finish {d.avg_finish_position?.toFixed(1) ?? '—'} · avg quali{' '}
                  {d.avg_qualifying_position?.toFixed(1) ?? '—'}
                </span>
              </div>
              <div className="h-4 bg-asphalt relative">
                <div
                  className="h-full"
                  style={{ width: `${(d.points / maxPoints) * 100}%`, backgroundColor: t.color_primary ?? 'var(--color-signal)' }}
                />
              </div>
              <span className="text-xs text-steel tabular">{d.points} pts</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
