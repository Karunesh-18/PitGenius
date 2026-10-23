import { Link } from 'react-router-dom'
import { useConstructorStandings, useDriverStandings, useDrivers, useRace, useRaces, useTeams } from '../api/hooks'
import { Panel } from '../components/Panel'
import { PodiumStrip } from '../components/PodiumStrip'
import { SeasonCalendar } from '../components/SeasonCalendar'
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews'
import { tireCompoundColor, tireCompoundLabel } from '../theme/tireCompound'

export default function Home() {
  const races = useRaces()
  const driverStandings = useDriverStandings()
  const constructorStandings = useConstructorStandings()
  const drivers = useDrivers()
  const teams = useTeams()
  const colorByTeamRef = new Map(teams.data?.map((t) => [t.team_ref, t.color_primary]) ?? [])

  const completedRounds = (races.data ?? []).filter((r) => r.status === 'completed')
  const latestRound = completedRounds.at(-1)
  const latestRace = useRace(latestRound?.round)
  const classifiedResults = (latestRace.data?.race_results ?? [])
    .filter((r) => r.finish_position != null)
    .sort((a, b) => (a.finish_position as number) - (b.finish_position as number))

  return (
    <div className="space-y-6">
      <div className="border border-hairline bg-graphite px-5 py-4">
        {races.isLoading ? (
          <LoadingState label="Loading season" />
        ) : latestRound ? (
          <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
            <div>
              <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">
                Round {latestRound.round} of {races.data?.length}
              </p>
              <h1 className="text-2xl font-700 leading-tight">{latestRound.name}</h1>
              <p className="text-steel text-sm mt-0.5">
                {/* race_date is a date-only string; `T00:00:00` forces local-time
                    parsing so the calendar date doesn't shift back a day west of UTC. */}
                {new Date(`${latestRound.race_date}T00:00:00`).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
            {classifiedResults.length > 0 && (
              <PodiumStrip results={classifiedResults} colorByTeamRef={colorByTeamRef} />
            )}
          </div>
        ) : (
          <EmptyState message="No races loaded yet — run the ETL pipeline to populate a season." />
        )}
      </div>

      <Panel title="Race Results">
        {latestRace.isLoading && <LoadingState label="Loading results" />}
        {latestRace.isError && <ErrorState message={(latestRace.error as Error).message} />}
        {classifiedResults.length === 0 && !latestRace.isLoading && (
          <EmptyState message="No classified results for this race yet." />
        )}
        {classifiedResults.length > 0 && (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-steel text-left border-b border-hairline">
                <th className="font-500 py-1.5 pr-3 w-10">Pos</th>
                <th className="font-500 py-1.5 pr-3">Driver</th>
                <th className="font-500 py-1.5 pr-3">Tire</th>
                <th className="font-500 py-1.5 text-right">Points</th>
              </tr>
            </thead>
            <tbody>
              {classifiedResults.map((r) => {
                const isFastestLap = r.fastest_lap_rank === 1
                return (
                  <tr
                    key={r.driver_ref}
                    className="border-b border-hairline last:border-0 tabular"
                    style={isFastestLap ? { borderLeft: '2px solid var(--color-purple-fastest)' } : undefined}
                  >
                    <td className={`py-1.5 pr-3 pl-2 ${isFastestLap ? 'text-purple-fastest font-700' : ''}`}>
                      {r.finish_position}
                    </td>
                    <td className={`py-1.5 pr-3 ${isFastestLap ? 'text-purple-fastest font-600' : ''}`}>
                      {r.code ?? r.driver_ref}
                    </td>
                    <td className="py-1.5 pr-3">
                      <span
                        className="inline-block px-1.5 py-0.5 text-[10px] font-700 tracking-[0.03em]"
                        style={{
                          color: tireCompoundColor(r.final_compound),
                          border: `1px solid ${tireCompoundColor(r.final_compound)}`,
                        }}
                      >
                        {tireCompoundLabel(r.final_compound)}
                      </span>
                    </td>
                    <td className="py-1.5 text-right font-600">{r.points}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </Panel>

      <SeasonCalendar />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="Driver Standings">
          {driverStandings.isLoading && <LoadingState />}
          {driverStandings.isError && <ErrorState message={(driverStandings.error as Error).message} />}
          {driverStandings.data && driverStandings.data.length === 0 && (
            <EmptyState message="No standings yet for this season." />
          )}
          {driverStandings.data && driverStandings.data.length > 0 && (
            <table className="w-full text-sm">
              <tbody>
                {driverStandings.data.slice(0, 10).map((row) => (
                  <tr key={row.driver_ref} className="border-b border-hairline last:border-0">
                    <td className="py-1.5 pr-3 text-steel tabular w-6">{row.position}</td>
                    <td className="py-1.5 pr-3">
                      <Link to={`/drivers/${row.driver_ref}`} className="hover:text-signal">
                        {row.given_name} {row.family_name}
                      </Link>
                    </td>
                    <td className="py-1.5 text-right tabular font-600">{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel title="Constructor Standings">
          {constructorStandings.isLoading && <LoadingState />}
          {constructorStandings.isError && <ErrorState message={(constructorStandings.error as Error).message} />}
          {constructorStandings.data && constructorStandings.data.length === 0 && (
            <EmptyState message="No standings yet for this season." />
          )}
          {constructorStandings.data && constructorStandings.data.length > 0 && (
            <table className="w-full text-sm">
              <tbody>
                {constructorStandings.data.map((row) => (
                  <tr key={row.team_ref} className="border-b border-hairline last:border-0">
                    <td className="py-1.5 pr-3 text-steel tabular w-6">{row.position}</td>
                    <td className="py-1.5 pr-3">
                      <Link to={`/teams/${row.team_ref}`} className="hover:text-signal">
                        {row.name}
                      </Link>
                    </td>
                    <td className="py-1.5 text-right tabular font-600">{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>

      <Panel title="Top Rated Drivers">
        {drivers.isLoading && <LoadingState />}
        {drivers.isError && <ErrorState message={(drivers.error as Error).message} />}
        {drivers.data && drivers.data.length > 0 && (
          <div className="space-y-2.5">
            {drivers.data.slice(0, 8).map((d) => (
              <div key={d.driver_ref} className="flex items-center gap-3 text-sm">
                <span className="w-32 shrink-0 truncate">
                  {d.given_name} {d.family_name}
                </span>
                <div className="flex-1 h-4 bg-asphalt relative">
                  <div
                    className="h-full"
                    style={{ width: `${d.driver_rating}%`, backgroundColor: 'var(--color-signal)' }}
                  />
                </div>
                <span className="w-10 text-right tabular font-600 shrink-0">{d.driver_rating.toFixed(1)}</span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
