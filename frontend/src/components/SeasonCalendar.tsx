import { useRaces, useTeams } from '../api/hooks'
import { Panel } from './Panel'
import { EmptyState, ErrorState, LoadingState } from './StateViews'
import { countryToFlag } from '../theme/countryToFlag'

export function SeasonCalendar() {
  const races = useRaces()
  const teams = useTeams()
  const colorByTeamRef = new Map((teams.data ?? []).map((t) => [t.team_ref, t.color_primary]))

  return (
    <Panel title="Season Calendar">
      {races.isLoading && <LoadingState label="Loading calendar" />}
      {races.isError && <ErrorState message={(races.error as Error).message} />}
      {races.data && races.data.length === 0 && <EmptyState message="No races loaded yet." />}
      {races.data && races.data.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-steel text-left border-b border-hairline">
              <th className="font-500 py-1.5 pr-3 w-10">Rnd</th>
              <th className="font-500 py-1.5 pr-3">Race</th>
              <th className="font-500 py-1.5 pr-3">Country</th>
              <th className="font-500 py-1.5 pr-3">Date</th>
              <th className="font-500 py-1.5 text-right">Winner</th>
            </tr>
          </thead>
          <tbody>
            {races.data.map((r) => {
              const winnerColor = colorByTeamRef.get(r.winner_team_ref ?? '') ?? null
              return (
                <tr key={r.round} className="border-b border-hairline last:border-0 tabular">
                  <td className="py-1.5 pr-3 text-steel">{r.round}</td>
                  <td className="py-1.5 pr-3">{r.name}</td>
                  <td className="py-1.5 pr-3 text-steel">
                    {r.country ? `${countryToFlag[r.country] ?? ''} ${r.country}` : '—'}
                  </td>
                  <td className="py-1.5 pr-3 text-steel">
                    {/* race_date is a date-only string; `T00:00:00` forces local-time
                        parsing so the calendar date doesn't shift back a day west of UTC. */}
                    {new Date(`${r.race_date}T00:00:00`).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="py-1.5 text-right">
                    {r.winner_code ? (
                      <span
                        className="inline-block px-2 py-0.5 text-xs font-600"
                        style={{
                          backgroundColor: winnerColor ? `${winnerColor}26` : 'transparent',
                          color: winnerColor ?? 'var(--color-paper)',
                          border: `1px solid ${winnerColor ?? 'var(--color-hairline)'}`,
                        }}
                      >
                        {r.winner_code}
                      </span>
                    ) : (
                      <span className="text-steel">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
