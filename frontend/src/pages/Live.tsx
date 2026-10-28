import { useLive } from '../api/hooks'
import { Panel } from '../components/Panel'
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews'

const fmt = (v: number | string | null | undefined) =>
  v == null ? '—' : typeof v === 'number' ? `+${v.toFixed(3)}` : v

export default function Live() {
  const { data, isLoading, error } = useLive()
  if (isLoading) return <LoadingState label="Connecting to OpenF1" />
  if (error) return <ErrorState message={(error as Error).message} />
  if (!data?.session) return <EmptyState message="No OpenF1 session available." />
  const s = data.session
  const live = new Date(s.date_start) <= new Date() && new Date() <= new Date(s.date_end)
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Panel
        className="lg:col-span-2"
        title={`${s.year} ${s.country_name} · ${s.session_name}`}
        action={
          <span className={`text-xs font-600 ${live ? 'text-signal' : 'text-steel'}`}>
            {live ? '● LIVE' : 'Last session'}
          </span>
        }
      >
        {data.tower?.length ? (
          <table className="w-full text-sm tabular">
            <thead className="text-steel text-xs text-left">
              <tr><th className="w-10">Pos</th><th>Driver</th><th className="text-right">Gap</th><th className="text-right">Int</th></tr>
            </thead>
            <tbody>
              {data.tower.map((r) => (
                <tr key={r.driver_number} className="border-t border-hairline">
                  <td className="py-1.5">{r.position}</td>
                  <td>
                    <span className="inline-block w-1 h-3 mr-2 align-middle" style={{ background: `#${r.team_colour ?? '888'}` }} />
                    {r.code ?? r.driver_number} <span className="text-steel">{r.team}</span>
                  </td>
                  <td className="text-right">{r.position === 1 ? 'Leader' : fmt(r.gap_to_leader)}</td>
                  <td className="text-right">{r.position === 1 ? '' : fmt(r.interval)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState message="No timing data for this session yet." />
        )}
      </Panel>
      <div className="grid gap-4 content-start">
        <Panel title="Weather">
          {data.weather ? (
            <dl className="grid grid-cols-2 gap-y-1 text-sm tabular">
              <dt className="text-steel">Air</dt><dd>{data.weather.air_temperature}°C</dd>
              <dt className="text-steel">Track</dt><dd>{data.weather.track_temperature}°C</dd>
              <dt className="text-steel">Humidity</dt><dd>{data.weather.humidity}%</dd>
              <dt className="text-steel">Wind</dt><dd>{data.weather.wind_speed} m/s</dd>
              <dt className="text-steel">Rain</dt><dd>{data.weather.rainfall ? 'Yes' : 'No'}</dd>
            </dl>
          ) : (
            <EmptyState message="No weather data." />
          )}
        </Panel>
        <Panel title="Race control">
          <ul className="text-sm space-y-2">
            {(data.race_control ?? []).map((m, i) => (
              <li key={i}><span className="text-steel tabular">{m.date.slice(11, 16)}</span> {m.message}</li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  )
}
