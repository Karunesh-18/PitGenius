import type { RaceResultRow } from '../api/types'

interface PodiumStripProps {
  results: RaceResultRow[]
  colorByTeamRef: Map<string, string | null | undefined>
}

/** Three team-color-accented boxes for P1/P2/P3, replacing a plain "Winner" line. */
export function PodiumStrip({ results, colorByTeamRef }: PodiumStripProps) {
  const podium = [1, 2, 3]
    .map((pos) => results.find((r) => r.finish_position === pos))
    .filter((r): r is RaceResultRow => !!r)

  if (podium.length === 0) return null

  return (
    <div className="grid grid-cols-3 gap-2">
      {podium.map((r) => {
        const color = colorByTeamRef.get(r.team_ref) ?? '#4A5266'
        return (
          <div
            key={r.driver_ref}
            className="border border-hairline px-3 py-2 text-right"
            style={{ borderTopWidth: 2, borderTopColor: color }}
          >
            <p className="text-[11px] text-steel tracking-[0.04em] uppercase">P{r.finish_position}</p>
            <p className="text-lg font-700 tabular">{r.code ?? r.driver_ref}</p>
          </div>
        )
      })}
    </div>
  )
}
