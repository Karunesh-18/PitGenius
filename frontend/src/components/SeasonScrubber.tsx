import { useSeasons } from '../api/hooks'
import { useSeasonState } from '../api/season'

/** Header timeline: one tick per loaded season. A filled dot means lap telemetry exists for that year. */
export function SeasonScrubber() {
  const { data } = useSeasons()
  const [season, setSeason] = useSeasonState()
  const years = [...(data ?? [])].reverse() // oldest -> newest, left to right
  if (years.length === 0) return <span className="text-xs text-steel tabular">{season} Season</span>
  return (
    <div role="tablist" aria-label="Season" className="flex items-end gap-0.5">
      {years.map(({ season: y, has_telemetry }) => {
        const active = y === season
        return (
          <button
            key={y}
            role="tab"
            aria-selected={active}
            onClick={() => setSeason(y)}
            title={has_telemetry ? `${y} · full telemetry` : `${y} · results only`}
            className={`px-1.5 pt-1 text-[11px] tabular border-b-2 transition-colors ${
              active ? 'border-signal text-paper' : 'border-transparent text-steel hover:text-paper'
            }`}
          >
            {active ? y : String(y).slice(2)}
            <span
              className={`block mx-auto mt-0.5 mb-1 h-1 w-1 rounded-full ${has_telemetry ? 'bg-signal' : 'bg-hairline'}`}
            />
          </button>
        )
      })}
    </div>
  )
}
